import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from deps import get_current_user
import models
import schemas
from services.reminder_state import clear_delivery_history, reset_for_reschedule
from services.repeat_schedule import (
    next_occurrence_after,
    normalize_repeat,
    repeat_label,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _reschedule_repeating_reminder(
    db: Session, reminder: models.Reminder, now: datetime
) -> bool:
    """Advance a repeating reminder to its next occurrence. Returns True if rescheduled."""
    if not normalize_repeat(reminder.repeat):
        return False
    next_dt = next_occurrence_after(reminder.repeat, reminder.datetime, after=now)
    if next_dt is None:
        return False
    cleared = reset_for_reschedule(db, reminder)
    reminder.datetime = next_dt
    logger.info(
        "event=repeat_rescheduled reminder_id=%s rule=%s next_datetime=%s "
        "cleared_delivery_attempts=%s",
        reminder.id,
        reminder.repeat,
        next_dt,
        cleared,
    )
    return True


@router.post("", response_model=schemas.ReminderResponse)
def create_reminder(
    reminder: schemas.ReminderCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_reminder = models.Reminder(
        task=reminder.task,
        datetime=reminder.datetime,
        repeat=normalize_repeat(reminder.repeat),
        user_id=current_user.id,
        status=models.ReminderStatus.PENDING.value,
    )
    db.add(db_reminder)
    db.commit()
    db.refresh(db_reminder)
    logger.info(
        "event=reminder_created user_id=%s reminder_id=%s scheduled_at=%s repeat=%s",
        current_user.id,
        db_reminder.id,
        db_reminder.datetime,
        db_reminder.repeat,
    )
    return db_reminder


@router.get("", response_model=list[schemas.ReminderResponse])
def get_reminders(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.Reminder)
        .filter(models.Reminder.user_id == current_user.id)
        .all()
    )


def _reminder_for_user(
    db: Session, reminder_id: UUID, user_id: UUID
) -> Optional[models.Reminder]:
    return (
        db.query(models.Reminder)
        .filter(
            models.Reminder.id == reminder_id,
            models.Reminder.user_id == user_id,
        )
        .first()
    )


@router.delete("/{reminder_id}")
def delete_reminder(
    reminder_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_reminder = _reminder_for_user(db, reminder_id, current_user.id)
    if not db_reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    db.query(models.DeliveryAttempt).filter(
        models.DeliveryAttempt.reminder_id == reminder_id
    ).delete(synchronize_session=False)
    db.delete(db_reminder)
    db.commit()
    logger.info("event=reminder_deleted user_id=%s reminder_id=%s", current_user.id, reminder_id)
    return {"message": "Reminder deleted successfully"}


@router.patch("/{reminder_id}", response_model=schemas.ReminderResponse)
def update_reminder(
    reminder_id: UUID,
    body: schemas.ReminderUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_reminder = _reminder_for_user(db, reminder_id, current_user.id)
    if not db_reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    rescheduled = False
    if body.task is not None:
        db_reminder.task = body.task
    if body.datetime is not None:
        if body.datetime != db_reminder.datetime:
            rescheduled = True
        db_reminder.datetime = body.datetime
    if body.repeat is not None:
        db_reminder.repeat = normalize_repeat(body.repeat)
    cleared = 0
    if rescheduled:
        cleared = reset_for_reschedule(db, db_reminder)
    db.commit()
    db.refresh(db_reminder)
    logger.info(
        "event=reminder_updated user_id=%s reminder_id=%s scheduled_at=%s repeat=%s "
        "rescheduled=%s cleared_delivery_attempts=%s",
        current_user.id,
        db_reminder.id,
        db_reminder.datetime,
        db_reminder.repeat,
        rescheduled,
        cleared,
    )
    return db_reminder


@router.post("/{reminder_id}/republish", response_model=schemas.ReminderResponse)
def republish_reminder(
    reminder_id: UUID,
    body: schemas.ReminderRepublish,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_reminder = _reminder_for_user(db, reminder_id, current_user.id)
    if not db_reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    now = datetime.now(timezone.utc)
    if body.task is not None:
        cleaned = body.task.strip()
        if not cleaned:
            raise HTTPException(status_code=400, detail="Task cannot be empty")
        db_reminder.task = cleaned
    if body.repeat is not None:
        db_reminder.repeat = normalize_repeat(body.repeat)
    if body.datetime is not None:
        if body.datetime <= now:
            raise HTTPException(
                status_code=400,
                detail="Scheduled time must be in the future",
            )
        db_reminder.datetime = body.datetime
    elif db_reminder.datetime <= now:
        raise HTTPException(
            status_code=400,
            detail="Reminder time is in the past. Set a new date and time to republish.",
        )

    cleared = reset_for_reschedule(db, db_reminder)
    db.commit()
    db.refresh(db_reminder)
    logger.info(
        "event=reminder_republished user_id=%s reminder_id=%s scheduled_at=%s "
        "cleared_delivery_attempts=%s",
        current_user.id,
        reminder_id,
        db_reminder.datetime,
        cleared,
    )
    return db_reminder


@router.patch("/{reminder_id}/complete", response_model=schemas.ReminderResponse)
def complete_reminder(
    reminder_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_reminder = _reminder_for_user(db, reminder_id, current_user.id)
    if not db_reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    now = datetime.now(timezone.utc)
    if _reschedule_repeating_reminder(db, db_reminder, now):
        db.commit()
        db.refresh(db_reminder)
        logger.info(
            "event=reminder_repeat_advanced user_id=%s reminder_id=%s rule=%s next=%s",
            current_user.id,
            reminder_id,
            db_reminder.repeat,
            db_reminder.datetime,
        )
        return db_reminder

    db_reminder.status = models.ReminderStatus.COMPLETED.value
    db_reminder.processing_started_at = None
    db_reminder.next_attempt_at = None
    db_reminder.last_error = None
    db.commit()
    db.refresh(db_reminder)
    logger.info(
        "event=reminder_completed user_id=%s reminder_id=%s",
        current_user.id,
        reminder_id,
    )
    return db_reminder


@router.post("/{reminder_id}/snooze", response_model=schemas.ReminderResponse)
def snooze_reminder(
    reminder_id: UUID,
    body: schemas.ReminderSnooze,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_reminder = _reminder_for_user(db, reminder_id, current_user.id)
    if not db_reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    now = datetime.now(timezone.utc)
    previous_status = db_reminder.status
    previous_datetime = db_reminder.datetime
    new_datetime = now + timedelta(minutes=body.minutes)

    cleared = clear_delivery_history(db, reminder_id)
    db_reminder.datetime = new_datetime
    db_reminder.status = models.ReminderStatus.PENDING.value
    db_reminder.triggered_at = None
    db_reminder.processing_started_at = None
    db_reminder.next_attempt_at = None
    db_reminder.attempt_count = 0
    db_reminder.last_error = None
    db.commit()
    db.refresh(db_reminder)

    logger.info(
        "Snooze reminder_id=%s user_id=%s minutes=%s previous_status=%s "
        "previous_datetime=%s new_datetime=%s cleared_delivery_attempts=%s",
        reminder_id,
        current_user.id,
        body.minutes,
        previous_status,
        previous_datetime,
        new_datetime,
        cleared,
    )
    return db_reminder
