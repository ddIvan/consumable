from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.mqtt_message import MqttMessage
from app.schemas import MqttMessageOut

router = APIRouter(prefix="/api/mqtt-messages", tags=["mqtt-messages"])


@router.get("", response_model=list[MqttMessageOut])
def list_mqtt_messages(
    search: str = "",
    printer_id: int = 0,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    q = db.query(MqttMessage)
    if search:
        q = q.filter(
            or_(
                MqttMessage.payload.ilike(f"%{search}%"),
                MqttMessage.topic.ilike(f"%{search}%"),
                MqttMessage.printer_name.ilike(f"%{search}%"),
            )
        )
    if printer_id > 0:
        q = q.filter(MqttMessage.printer_id == printer_id)
    return (
        q.order_by(MqttMessage.received_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.delete("/{message_id}", status_code=204)
def delete_mqtt_message(message_id: int, db: Session = Depends(get_db)):
    m = db.query(MqttMessage).filter(MqttMessage.id == message_id).first()
    if not m:
        raise HTTPException(404)
    db.delete(m)
    db.commit()


@router.delete("", status_code=204)
def clear_mqtt_messages(db: Session = Depends(get_db)):
    db.query(MqttMessage).delete()
    db.commit()
