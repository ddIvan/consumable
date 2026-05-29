from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.database import get_db, init_db
from app.models.printer import PrinterConfig
from app.routers import (
    dashboard,
    filaments,
    manufacturers,
    mqtt_messages,
    operation_logs,
    print_records,
    printer_config,
    spools,
)
from app.schemas import PrinterStatus
from app.services.filament_calc import get_filament_params, record_consumption
from app.services.mqtt_service import manager

logger = logging.getLogger(__name__)

# ─── WebSocket connection manager for real-time pushes ──────────


class WSBroadcaster:
    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._connections.append(ws)

    def disconnect(self, ws: WebSocket):
        self._connections.remove(ws)

    async def broadcast(self, data: dict):
        dead = []
        for ws in self._connections:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections.remove(ws)


ws_bus = WSBroadcaster()


# ─── Print lifecycle tracking ──────────────────────────────────
class PrintTracker:
    """Tracks print start/stop to record consumption."""

    def __init__(self):
        self._active: dict[int, dict[str, Any]] = {}

    def start(self, printer_id: int, job_id: str, filename: str):
        self._active[printer_id] = {
            "job_id": job_id,
            "filename": filename,
            "start_time": time.time(),
            "filament_start_mm": 0,
        }

    def end(self, printer_id: int, status: str = "finished"):
        return self._active.pop(printer_id, None)

    def get(self, printer_id: int):
        return self._active.get(printer_id)


print_tracker = PrintTracker()


# ─── Lifespan ──────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    init_db()

    # auto-start any active printers from DB
    try:
        db: Session = next(get_db())
        printers = db.query(PrinterConfig).filter(PrinterConfig.is_active).all()
        for p in printers:
            logger.info("Auto-starting MQTT for printer %s (%s)", p.name, p.serial)
            client = manager.get_or_create(p)
            import time as _time
            for _ in range(10):
                if client.connected:
                    _log_operation(db, "printer_connect", p.name, "自启动连接成功")
                    break
                _time.sleep(0.3)
            else:
                _log_operation(db, "printer_connect", p.name, "自启动连接超时", level="warning")
        db.close()
    except Exception as e:
        logger.warning("Could not auto-start printers: %s", e)

    yield

    manager.stop_all()


# ─── App ───────────────────────────────────────────────────────

app = FastAPI(title="Filament Manager", version="1.0.0", lifespan=lifespan)

# Mount static frontend (created during Docker build or manual build)
import os as _os
if _os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# API routers
app.include_router(manufacturers.router)
app.include_router(filaments.router)
app.include_router(spools.router)
app.include_router(print_records.router)
app.include_router(printer_config.router)
app.include_router(mqtt_messages.router)
app.include_router(operation_logs.router)
app.include_router(dashboard.router)


# ─── Helper: operation log ─────────────────────────────────────
def _log_operation(db: Session, action: str, target: str, message: str, level: str = "info"):
    from app.models.operation_log import OperationLog
    try:
        db.add(OperationLog(action=action, target=target, message=message, level=level))
        db.commit()
    except Exception:
        db.rollback()


# ─── MQTT management endpoints ─────────────────────────────────
@app.post("/api/printer/{printer_id}/connect")
def api_connect_printer(printer_id: int):
    import time
    db: Session = next(get_db())
    try:
        p = db.query(PrinterConfig).filter(PrinterConfig.id == printer_id).first()
        if not p:
            return {"status": "error", "message": "Printer not found"}
        client = manager.get_or_create(p)

        # wait up to 5s for the async MQTT connection to complete
        for _ in range(25):
            if client.connected:
                _log_operation(db, "printer_connect", p.name, "连接成功")
                return {"status": "connected"}
            time.sleep(0.2)

        reason = f"MQTT 连接超时 (IP: {p.ip_address}:{p.port})"
        _log_operation(db, "printer_connect", p.name, reason, level="error")
        return {"status": "failed", "message": reason}
    finally:
        db.close()


@app.post("/api/printer/{printer_id}/disconnect")
def api_disconnect_printer(printer_id: int):
    manager.remove(printer_id)
    return {"status": "disconnected"}


@app.get("/api/printer/{printer_id}/status", response_model=PrinterStatus)
def api_printer_status(printer_id: int):
    client = manager.get(printer_id)
    if not client:
        return PrinterStatus()
    return client.status


# ─── WebSocket for real-time ───────────────────────────────────
@app.websocket("/ws/printer/{printer_id}")
async def ws_printer(websocket: WebSocket, printer_id: int):
    await ws_bus.connect(websocket)
    client = manager.get(printer_id)
    if client:
        client.register_ws(ws_bus)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        ws_bus.disconnect(websocket)
        if client:
            client.unregister_ws(ws_bus)


# ─── MQTT consumption hook (called periodically or on print end) ─
@app.post("/api/printer/{printer_id}/check-consumption")
def check_consumption(printer_id: int):
    """Called to record consumption deltas for active prints."""
    client = manager.get(printer_id)
    if not client:
        return {"error": "Not connected"}
    if client.status.gcode_state != "running":
        return {"error": "Printer not running"}

    delta_mm = client.get_filament_used_delta()
    if delta_mm <= 0:
        return {"consumed_mm": 0}

    # resolve spool (AMS tray or first active)
    db: Session = next(get_db())
    try:
        from app.models.spool import Spool

        spool = (
            db.query(Spool)
            .filter(Spool.is_active)
            .order_by(Spool.ams_tray)
            .first()
        )
        spool_id = spool.id if spool else None
        diameter, density = get_filament_params(db, spool_id) if spool_id else (1.75, 1.24)

        from app.services.filament_calc import filament_weight

        weight = filament_weight(delta_mm, diameter, density)

        if spool:
            spool.current_weight = max(0, spool.current_weight - weight)
            db.commit()

        return {
            "consumed_mm": round(delta_mm, 1),
            "consumed_weight": round(weight, 3),
            "spool_id": spool_id,
        }
    finally:
        db.close()


@app.get("/api/printer/{printer_id}/print-finish")
def api_print_finish(printer_id: int):
    """Call when a print finishes to record it."""
    client = manager.get(printer_id)
    if not client:
        return {"error": "Not connected"}

    tracker_data = print_tracker.end(printer_id)
    if not tracker_data:
        return {"error": "No active print tracked"}

    total_mm = client.status.filament_used_mm
    db: Session = next(get_db())
    try:
        from app.models.spool import Spool

        spool = (
            db.query(Spool)
            .filter(Spool.is_active)
            .order_by(Spool.ams_tray)
            .first()
        )
        spool_id = spool.id if spool else None
        diameter, density = get_filament_params(db, spool_id) if spool_id else (1.75, 1.24)

        record_consumption(
            db=db,
            spool_id=spool_id,
            printer_id=printer_id,
            print_job_id=tracker_data["job_id"],
            filename=tracker_data["filename"],
            filament_used_mm=total_mm,
            diameter=diameter,
            density=density,
            remaining_before=None,
            remaining_after=client.status.mc_remaining_percent,
            status="finished",
        )
        return {"recorded": True, "filament_used_mm": total_mm}
    finally:
        db.close()


# ─── Serve SPA (catch-all) ─────────────────────────────────────
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    if full_path.startswith("api/") or full_path.startswith("ws/"):
        from fastapi.responses import JSONResponse
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    from fastapi.responses import FileResponse
    import os
    spa_path = os.path.join("static", "index.html")
    if os.path.exists(spa_path):
        return FileResponse(spa_path)
    return JSONResponse({"detail": "Frontend not built yet"}, status_code=200)
