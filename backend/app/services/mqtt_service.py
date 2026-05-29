from __future__ import annotations

import json
import logging
import ssl
import time
from datetime import datetime, timezone
from typing import Any, Optional

import paho.mqtt.client as mqtt

from app.models.printer import PrinterConfig
from app.schemas import PrinterStatus

logger = logging.getLogger(__name__)


class PrinterMqttClient:
    """Manages MQTT connection to a Bambu Lab printer.

    On every MQTT report, automatically deducts filament consumption
    from the active spool matching the current AMS tray (or EXT).
    Also tracks print lifecycle to create PrintRecords on completion.
    """

    def __init__(self, printer: PrinterConfig):
        self.printer = printer
        self.client: Optional[mqtt.Client] = None
        self._connected = False
        self._status = PrinterStatus()
        self._last_report: dict[str, Any] = {}
        self._ws_clients: list = []

        # filament delta tracking (mm)
        self._last_filament_mm: float = 0
        self._last_tray: int = 0

        # print lifecycle
        self._prev_gcode_state: str = ""
        self._print_start_mm: float = 0
        self._print_start_time: Optional[datetime] = None
        self._current_job_id: str = ""

        # per-tray tracking for multi-color support {tray: total_mm}
        self._tray_usage: dict[int, float] = {}

    @property
    def status(self) -> PrinterStatus:
        return self._status

    @property
    def connected(self) -> bool:
        return self._connected

    def register_ws(self, manager):
        self._ws_clients.append(manager)

    def unregister_ws(self, manager):
        self._ws_clients.remove(manager)

    def _notify_ws(self, data: dict):
        dead = []
        for m in self._ws_clients:
            try:
                m.broadcast(data)
            except Exception:
                dead.append(m)
        for m in dead:
            self._ws_clients.remove(m)

    def start(self):
        if self.client:
            # 如果已有 client，先检查是否需要重启
            if self._connected:
                return
            self.stop()
        self.client = mqtt.Client(
            client_id=f"fm-{self.printer.serial}-{int(time.time())}",
            protocol=mqtt.MQTTv311,
        )
        # 自动重连：断开后 1s 开始尝试，最长间隔 60s
        self.client.reconnect_delay_set(min_delay=1, max_delay=60)
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        self.client.tls_set_context(ssl_ctx)
        self.client.username_pw_set("bblp", self.printer.access_code)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        logger.info(
            "Connecting MQTT to %s:%d (serial=%s)",
            self.printer.ip_address, self.printer.port, self.printer.serial,
        )
        self.client.connect_async(self.printer.ip_address, self.printer.port, 60)
        self.client.loop_start()

    def stop(self):
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.client = None
        self._connected = False

    def _on_connect(self, _client, _userdata, _flags, rc):
        if rc == 0:
            self._connected = True
            topic = f"device/{self.printer.serial}/report"
            self.client.subscribe(topic, qos=0)
            logger.info("MQTT connected, subscribed to %s", topic)
            self._status.connected = True
            self._notify_ws({"type": "connection", "connected": True})
        else:
            reason = {1: "协议版本错误", 2: "标识符被拒", 3: "服务器不可用", 4: "用户名或密码错误", 5: "未授权"}.get(rc, f"未知错误({rc})")
            logger.error("MQTT connect failed, rc=%d (%s)", rc, reason)
            try:
                from app.database import SessionLocal
                from app.models.operation_log import OperationLog
                db = SessionLocal()
                db.add(OperationLog(
                    action="printer_connect",
                    target=self.printer.name,
                    message=f"连接失败: {reason} (rc={rc})",
                    level="error",
                ))
                db.commit()
                db.close()
            except Exception:
                pass

    def _on_disconnect(self, _client, _userdata, rc):
        self._connected = False
        self._status.connected = False
        logger.warning("MQTT disconnected, rc=%d", rc)
        self._notify_ws({"type": "connection", "connected": False})

    def _on_message(self, _client, _userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning("Invalid MQTT payload: %s", e)
            return
        self._last_report = payload
        self._save_message(msg.topic, payload)
        self._parse_report(payload)

    def _save_message(self, topic: str, payload: dict):
        """Persist incoming MQTT message to database."""
        try:
            from app.database import SessionLocal
            from app.models.mqtt_message import MqttMessage

            db = SessionLocal()
            try:
                m = MqttMessage(
                    printer_id=self.printer.id,
                    printer_name=self.printer.name,
                    topic=topic,
                    payload=json.dumps(payload, ensure_ascii=False),
                )
                db.add(m)
                db.commit()
            except Exception as e:
                logger.error("Failed to save MQTT message: %s", e)
                db.rollback()
            finally:
                db.close()
        except Exception as e:
            logger.error("Failed to save MQTT message (db error): %s", e)

    # ──────────────────────────────────────────────────────────
    #  MQTT report parser  —  runs on every incoming message
    # ──────────────────────────────────────────────────────────

    def _parse_report(self, payload: dict):
        data = payload.get("print", payload)
        s = self._status

        # ── state machine ──
        prev_state = self._prev_gcode_state
        new_state = data.get("gcode_state", s.gcode_state)
        s.gcode_state = new_state

        # ── filament used mm ──
        new_filament_mm = data.get("filament_used_mm", s.filament_used_mm)
        s.filament_used_mm = new_filament_mm

        # ── other status fields ──
        s.gcode_file = data.get("gcode_file", s.gcode_file) or data.get("gcode_filename", s.gcode_file)
        s.mc_percent = data.get("mc_percent", s.mc_percent)
        s.nozzle_temp = data.get("nozzle_temper", s.nozzle_temp)
        s.nozzle_target = data.get("nozzle_target", s.nozzle_target)
        s.bed_temp = data.get("bed_temper", s.bed_temp)
        s.bed_target = data.get("bed_target", s.bed_target)
        s.mc_remaining_percent = data.get("mc_remaining_percent", s.mc_remaining_percent)
        s.current_tray = data.get("tray_now", s.current_tray)

        # ── print lifecycle ──
        if prev_state != "RUNNING" and new_state == "RUNNING":
            self._on_print_start()
        elif prev_state == "RUNNING" and new_state in ("FINISH", "FAILED"):
            self._on_print_end(new_state.lower())

        self._prev_gcode_state = new_state

        # ── auto-deduct filament (only while running) ──
        if new_state == "RUNNING":
            self._deduct_filament()

        # ── push to WebSocket ──
        self._notify_ws({"type": "status", "status": s.model_dump()})

    # ──────────────────────────────────────────────────────────
    #  Auto-deduction logic
    # ──────────────────────────────────────────────────────────

    def _deduct_filament(self):
        """Calculate delta filament_used_mm since last report and deduct from spool."""
        current_mm = self._status.filament_used_mm
        current_tray = self._status.current_tray

        if self._last_filament_mm == 0:
            self._last_filament_mm = current_mm
            self._last_tray = current_tray
            return

        delta_mm = max(0, current_mm - self._last_filament_mm)
        self._last_filament_mm = current_mm

        if delta_mm < 0.1:  # ignore sub-mm noise
            return

        # attribute delta to the tray that was active during this period
        active_tray = self._last_tray
        self._tray_usage[active_tray] = self._tray_usage.get(active_tray, 0) + delta_mm
        self._last_tray = current_tray

        # ── resolve spool (AMS tray or EXT) ──
        from app.database import SessionLocal
        from app.models.spool import Spool
        from app.services.filament_calc import filament_weight

        db = SessionLocal()
        try:
            tray = self._status.current_tray
            if tray > 0:
                spool = db.query(Spool).filter(
                    Spool.ams_tray == tray,
                    Spool.is_active == True,
                ).first()
            else:
                spool = db.query(Spool).filter(
                    Spool.is_active == True,
                    Spool.ams_tray == 0,
                ).first()

            if not spool:
                return

            # resolve filament params
            diameter, density = 1.75, 1.24
            fil = spool.filament
            if fil:
                diameter = fil.diameter
                density = fil.density

            weight = filament_weight(delta_mm, diameter, density)
            old = spool.current_weight
            spool.current_weight = max(0, round(old - weight, 2))
            db.commit()

            logger.debug(
                "Deduct Tray%d %s: %.2fmm → %.3fg (was %.1fg → %.1fg)",
                tray, spool.name, delta_mm, weight, old, spool.current_weight,
            )
        except Exception as e:
            logger.error("Auto-deduct error: %s", e)
            db.rollback()
        finally:
            db.close()

    # ──────────────────────────────────────────────────────────
    #  Print lifecycle
    # ──────────────────────────────────────────────────────────

    def _on_print_start(self):
        self._print_start_mm = self._status.filament_used_mm
        self._last_filament_mm = self._status.filament_used_mm
        self._last_tray = self._status.current_tray
        self._print_start_time = datetime.now(timezone.utc)
        self._current_job_id = f"{self.printer.serial}_{int(time.time())}"
        self._tray_usage = {}
        logger.info(
            "Print started: %s (job=%s, filament_mm=%.1f, tray=%d)",
            self._status.gcode_file, self._current_job_id,
            self._print_start_mm, self._last_tray,
        )

    def _on_print_end(self, status: str = "finished"):
        total_mm = self._status.filament_used_mm - self._print_start_mm
        if total_mm < 0:
            total_mm = self._status.filament_used_mm  # fallback if counter reset

        logger.info(
            "Print ended (%s): %s, total=%.1fmm, trays=%s",
            status, self._status.gcode_file, total_mm, self._tray_usage,
        )

        # If no per-tray tracking (e.g. very short print), attribute all to last known tray
        if not self._tray_usage and total_mm > 0:
            self._tray_usage[self._last_tray] = total_mm

        from app.database import SessionLocal
        from app.models.print_record import PrintRecord, PrintRecordDetail
        from app.models.spool import Spool
        from app.services.filament_calc import filament_weight, get_filament_params

        db = SessionLocal()
        try:
            # create master record
            master = PrintRecord(
                printer_id=self.printer.id,
                printer_name=self.printer.name,
                print_job_id=self._current_job_id,
                filename=self._status.gcode_file or "",
                start_time=self._print_start_time or datetime.now(timezone.utc),
                end_time=datetime.now(timezone.utc),
                status=status,
            )
            db.add(master)
            db.flush()  # get master.id

            # create detail per tray
            for tray, tray_mm in self._tray_usage.items():
                if tray_mm < 1:
                    continue
                # resolve spool for this tray
                if tray > 0:
                    spool = db.query(Spool).filter(
                        Spool.ams_tray == tray,
                        Spool.is_active == True,
                    ).first()
                else:
                    spool = db.query(Spool).filter(
                        Spool.is_active == True,
                        Spool.ams_tray == 0,
                    ).first()

                spool_id = spool.id if spool else None
                diameter, density = get_filament_params(db, spool_id) if spool_id else (1.75, 1.24)
                weight = filament_weight(tray_mm, diameter, density)

                detail = PrintRecordDetail(
                    print_record_id=master.id,
                    tray=tray,
                    spool_id=spool_id,
                    filament_used_mm=round(tray_mm, 1),
                    filament_used_weight=round(weight, 3),
                    filament_diameter=diameter,
                    deducted=True,  # real-time deduction happened during printing
                    remaining_percent_before=None,
                    remaining_percent_after=self._status.mc_remaining_percent,
                )
                db.add(detail)
                logger.info(
                    "PrintRecordDetail Tray%d: %.1fmm → %.3fg (spool=%s)",
                    tray, tray_mm, weight, spool.name if spool else "none",
                )
            db.commit()
        except Exception as e:
            logger.error("Print end record error: %s", e)
            db.rollback()
        finally:
            db.close()

        # reset tracking
        self._last_filament_mm = 0
        self._last_tray = 0
        self._print_start_mm = 0
        self._print_start_time = None
        self._tray_usage = {}

    def get_filament_used_delta(self) -> float:
        """Used by external API — resets internal tracking separately."""
        current = self._status.filament_used_mm
        if self._last_filament_mm == 0:
            self._last_filament_mm = current
            return 0
        delta = max(0, current - self._last_filament_mm)
        self._last_filament_mm = current
        return delta


class ConnectionManager:
    """Manages multiple printer MQTT clients."""

    def __init__(self):
        self._printers: dict[int, PrinterMqttClient] = {}

    def get_or_create(self, printer: PrinterConfig) -> PrinterMqttClient:
        if printer.id not in self._printers:
            client = PrinterMqttClient(printer)
            client.start()
            self._printers[printer.id] = client
        return self._printers[printer.id]

    def remove(self, printer_id: int):
        client = self._printers.pop(printer_id, None)
        if client:
            client.stop()

    def stop_all(self):
        for client in self._printers.values():
            client.stop()
        self._printers.clear()

    def get(self, printer_id: int) -> Optional[PrinterMqttClient]:
        return self._printers.get(printer_id)

    def health_check(self):
        """Periodic check: restart clients that are disconnected."""
        import logging as _logging
        for client in list(self._printers.values()):
            if not client.connected:
                _logging.getLogger(__name__).warning(
                    "MQTT health: %s disconnected, restarting...", client.printer.name,
                )
                client.stop()
                client.start()


manager = ConnectionManager()
