"""Shared reminder status resets for snooze, edit, and repeat rescheduling."""

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

import models


def clear_delivery_history(db: Session, reminder_id: UUID) -> int:
    deleted = (
        db.query(models.DeliveryAttempt)
        .filter(models.DeliveryAttempt.reminder_id == reminder_id)
        .delete(synchronize_session=False)
    )
    return deleted


def reset_for_reschedule(db: Session, reminder: models.Reminder) -> int:
    """Return reminder to pending and clear delivery state for a new fire time."""
    cleared = clear_delivery_history(db, reminder.id)
    reminder.status = models.ReminderStatus.PENDING.value
    reminder.triggered_at = None
    reminder.processing_started_at = None
    reminder.next_attempt_at = None
    reminder.attempt_count = 0
    reminder.last_error = None
    return cleared
