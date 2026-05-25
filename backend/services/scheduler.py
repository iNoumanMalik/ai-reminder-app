from datetime import datetime, timedelta, timezone
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import SessionLocal
import models
import logging
from services.notifications import send_push_notification
from services.reminder_state import reset_for_reschedule
from services.repeat_schedule import next_occurrence_after, normalize_repeat

logger = logging.getLogger(__name__)

SCHEDULER_INTERVAL_SECONDS = int(os.getenv("SCHEDULER_INTERVAL_SECONDS", "30"))
MAX_DELIVERY_ATTEMPTS = int(os.getenv("MAX_DELIVERY_ATTEMPTS", "5"))
PROCESSING_TIMEOUT_SECONDS = int(os.getenv("PROCESSING_TIMEOUT_SECONDS", "120"))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def delivery_dedupe_key(reminder_id, device_id, scheduled_at: datetime) -> str:
    """One delivery per device per scheduled fire time (snooze changes scheduled_at)."""
    if scheduled_at.tzinfo is None:
        scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)
    else:
        scheduled_at = scheduled_at.astimezone(timezone.utc)
    slot = int(scheduled_at.timestamp())
    return f"{reminder_id}:{device_id}:{slot}"


def _next_retry_at(now: datetime, attempt_count: int) -> datetime:
    minutes = min(16, 2 ** max(0, attempt_count - 1))
    return now + timedelta(minutes=minutes)


def _recover_stale_processing(db: Session, now: datetime) -> int:
    stale_before = now - timedelta(seconds=PROCESSING_TIMEOUT_SECONDS)
    stale_rows = (
        db.query(models.Reminder)
        .filter(
            models.Reminder.status == models.ReminderStatus.PROCESSING.value,
            or_(
                models.Reminder.processing_started_at.is_(None),
                models.Reminder.processing_started_at <= stale_before,
            ),
        )
        .all()
    )
    if not stale_rows:
        return 0

    for reminder in stale_rows:
        logger.warning(
            "Recovering stale processing reminder_id=%s processing_started_at=%s last_error=%s",
            reminder.id,
            reminder.processing_started_at,
            reminder.last_error,
        )
        reminder.status = models.ReminderStatus.PENDING.value
        reminder.processing_started_at = None
        if not reminder.last_error:
            reminder.last_error = "processing_timeout_recovered"
        # Defer slightly so recovery does not immediately re-fire in the same tick.
        reminder.next_attempt_at = now + timedelta(seconds=SCHEDULER_INTERVAL_SECONDS)

    db.commit()
    logger.info("Recovered %d stale processing reminder(s)", len(stale_rows))
    return len(stale_rows)


def _claim_due_reminder(db: Session, reminder_id, now: datetime) -> bool:
    stale_before = now - timedelta(seconds=PROCESSING_TIMEOUT_SECONDS)
    updated = (
        db.query(models.Reminder)
        .filter(
            models.Reminder.id == reminder_id,
            models.Reminder.datetime <= now,
            models.Reminder.status == models.ReminderStatus.PENDING.value,
            or_(
                models.Reminder.next_attempt_at.is_(None),
                models.Reminder.next_attempt_at <= now,
            ),
        )
        .update(
            {
                "status": models.ReminderStatus.PROCESSING.value,
                "processing_started_at": now,
            },
            synchronize_session=False,
        )
    )
    return bool(updated)


def _release_processing_to_pending(
    db: Session,
    reminder: models.Reminder,
    now: datetime,
    error: str,
    *,
    increment_attempt: bool = True,
) -> None:
    if increment_attempt:
        reminder.attempt_count = (reminder.attempt_count or 0) + 1
    reminder.processing_started_at = None
    reminder.last_error = error
    if reminder.attempt_count >= MAX_DELIVERY_ATTEMPTS:
        reminder.status = models.ReminderStatus.FAILED.value
        reminder.next_attempt_at = None
        logger.error(
            "Reminder_id=%s marked failed after %s attempts (%s)",
            reminder.id,
            reminder.attempt_count,
            error,
        )
    else:
        reminder.status = models.ReminderStatus.PENDING.value
        reminder.next_attempt_at = _next_retry_at(now, reminder.attempt_count)
        logger.info(
            "Reminder_id=%s scheduled retry at %s (%s)",
            reminder.id,
            reminder.next_attempt_at,
            error,
        )


def _mark_triggered(
    db: Session, reminder: models.Reminder, now: datetime
) -> None:
    if normalize_repeat(reminder.repeat):
        next_dt = next_occurrence_after(reminder.repeat, reminder.datetime, after=now)
        if next_dt is not None:
            reset_for_reschedule(db, reminder)
            reminder.datetime = next_dt
            logger.info(
                "event=repeat_rescheduled reminder_id=%s rule=%s next_datetime=%s",
                reminder.id,
                reminder.repeat,
                next_dt,
            )
            return

    reminder.status = models.ReminderStatus.TRIGGERED.value
    reminder.triggered_at = now
    reminder.next_attempt_at = None
    reminder.processing_started_at = None
    reminder.last_error = None
    logger.info(
        "Reminder_id=%s triggered at %s scheduled_datetime=%s",
        reminder.id,
        now,
        reminder.datetime,
    )


def _process_reminder(db: Session, reminder: models.Reminder, now: datetime) -> None:
    scheduled_at = reminder.datetime
    if scheduled_at.tzinfo is None:
        scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)
    else:
        scheduled_at = scheduled_at.astimezone(timezone.utc)

    if scheduled_at > now:
        logger.warning(
            "Reminder_id=%s not yet due (scheduled_at=%s now=%s) — releasing claim",
            reminder.id,
            scheduled_at,
            now,
        )
        reminder.status = models.ReminderStatus.PENDING.value
        reminder.processing_started_at = None
        return

    user = db.query(models.User).filter(models.User.id == reminder.user_id).first()

    if user and not user.notifications_enabled:
        logger.info(
            "Reminder_id=%s notifications disabled for user_id=%s — marking triggered",
            reminder.id,
            reminder.user_id,
        )
        _mark_triggered(db, reminder, now)
        return

    device_tokens = (
        db.query(models.DeviceToken)
        .filter(models.DeviceToken.user_id == reminder.user_id)
        .order_by(models.DeviceToken.created_at.asc())
        .all()
    )

    if not device_tokens:
        logger.info(
            "Reminder_id=%s no devices for user_id=%s",
            reminder.id,
            reminder.user_id,
        )
        db_state = (
            db.query(models.Reminder.status)
            .filter(models.Reminder.id == reminder.id)
            .scalar()
        )
        if db_state != models.ReminderStatus.PROCESSING.value:
            logger.warning(
                "Reminder_id=%s was modified externally (status=%s) before releasing. "
                "Skipping status release to protect user action.",
                reminder.id,
                db_state,
            )
            return
        _release_processing_to_pending(db, reminder, now, "no_devices")
        return

    delivered = False
    last_error = None
    sends_attempted = 0

    for device in device_tokens:
        dedupe_key = delivery_dedupe_key(reminder.id, device.id, scheduled_at)
        existing = (
            db.query(models.DeliveryAttempt)
            .filter(models.DeliveryAttempt.dedupe_key == dedupe_key)
            .first()
        )
        if existing is not None:
            logger.info(
                "Reminder_id=%s skipping already-delivered dedupe_key=%s status=%s",
                reminder.id,
                dedupe_key,
                existing.status,
            )
            if existing.status == models.DeliveryStatus.SUCCESS.value:
                delivered = True
            continue

        sends_attempted += 1
        logger.info(
            "Reminder_id=%s sending push scheduled_at=%s device_token_id=%s dedupe_key=%s",
            reminder.id,
            scheduled_at,
            device.id,
            dedupe_key,
        )
        result = send_push_notification(
            device_token=device.token,
            user_id=str(reminder.user_id),
            task=reminder.task,
            reminder_id=str(reminder.id),
        )
        delivered = delivered or result.success
        if not result.success:
            last_error = result.error_message or result.error_code
            logger.warning(
                "Reminder_id=%s push failed device_token_id=%s error=%s",
                reminder.id,
                device.id,
                last_error,
            )

        attempt = models.DeliveryAttempt(
            reminder_id=reminder.id,
            device_token_id=device.id,
            dedupe_key=dedupe_key,
            status=(
                models.DeliveryStatus.SUCCESS.value
                if result.success
                else (
                    models.DeliveryStatus.PERM_FAILURE.value
                    if result.permanent_failure
                    else models.DeliveryStatus.TEMP_FAILURE.value
                )
            ),
            provider_message_id=result.provider_message_id,
            error_code=result.error_code,
            error_message=result.error_message,
        )
        db.add(attempt)

        if result.invalid_token:
            db.delete(device)

    # Concurrency safe: verify status is still PROCESSING and has not been snoozed/completed.
    db_state = (
        db.query(models.Reminder.status, models.Reminder.processing_started_at)
        .filter(models.Reminder.id == reminder.id)
        .first()
    )
    if not db_state or db_state[0] != models.ReminderStatus.PROCESSING.value or db_state[1] != reminder.processing_started_at:
        logger.warning(
            "Reminder_id=%s was modified externally (status=%s, started_at=%s) during push delivery. "
            "Skipping state update to protect user action.",
            reminder.id,
            db_state[0] if db_state else None,
            db_state[1] if db_state else None,
        )
        return

    reminder.attempt_count = (reminder.attempt_count or 0) + 1

    if delivered:
        _mark_triggered(db, reminder, now)
        return

    if sends_attempted == 0 and device_tokens:
        logger.warning(
            "Reminder_id=%s no sends for scheduled_at=%s — treating as delivery failure",
            reminder.id,
            scheduled_at,
        )

    _release_processing_to_pending(
        db,
        reminder,
        now,
        last_error or "delivery_failed",
        increment_attempt=False,
    )


async def check_due_reminders():
    db = SessionLocal()
    try:
        now = _utcnow()
        recovered = _recover_stale_processing(db, now)
        if recovered:
            logger.info("Stale processing recovery complete count=%s", recovered)

        # Only PENDING reminders are due; PROCESSING rows are handled via recovery.
        due_reminders = (
            db.query(models.Reminder)
            .filter(
                models.Reminder.datetime <= now,
                models.Reminder.status == models.ReminderStatus.PENDING.value,
                or_(
                    models.Reminder.next_attempt_at.is_(None),
                    models.Reminder.next_attempt_at <= now,
                ),
            )
            .all()
        )

        logger.debug("Scheduler tick at %s found %d due reminder(s)", now, len(due_reminders))

        for reminder in due_reminders:
            reminder_id = reminder.id
            try:
                logger.info(
                    "Scheduler considering reminder_id=%s scheduled_at=%s status=%s next_attempt_at=%s",
                    reminder.id,
                    reminder.datetime,
                    reminder.status,
                    reminder.next_attempt_at,
                )
                if not _claim_due_reminder(db, reminder_id, now):
                    continue

                # Immediate commit to ensure other workers / ticks cannot process this claimed reminder.
                db.commit()
                db.refresh(reminder)
                logger.info(
                    "Processing start reminder_id=%s scheduled_at=%s processing_started_at=%s",
                    reminder.id,
                    reminder.datetime,
                    reminder.processing_started_at,
                )

                _process_reminder(db, reminder, now)
                db.commit()
                logger.info(
                    "Processing finished reminder_id=%s final_status=%s triggered_at=%s",
                    reminder.id,
                    reminder.status,
                    reminder.triggered_at,
                )
            except Exception:
                logger.exception(
                    "Processing failed reminder_id=%s — rolling back and recovering",
                    reminder_id,
                )
                db.rollback()
                try:
                    stuck = (
                        db.query(models.Reminder)
                        .filter(models.Reminder.id == reminder_id)
                        .first()
                    )
                    if (
                        stuck
                        and stuck.status == models.ReminderStatus.PROCESSING.value
                    ):
                        _release_processing_to_pending(
                            db,
                            stuck,
                            now,
                            "processing_exception_recovered",
                        )
                        db.commit()
                        logger.info(
                            "Reminder_id=%s released to pending after exception",
                            reminder_id,
                        )
                except Exception:
                    logger.exception(
                        "Failed to recover reminder_id=%s after processing error",
                        reminder_id,
                    )
                    db.rollback()

    except Exception:
        logger.exception("Scheduler job failed")
        db.rollback()
    finally:
        db.close()


def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_due_reminders,
        "interval",
        seconds=SCHEDULER_INTERVAL_SECONDS,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info(
        "Scheduler started interval=%ss processing_timeout=%ss max_attempts=%s",
        SCHEDULER_INTERVAL_SECONDS,
        PROCESSING_TIMEOUT_SECONDS,
        MAX_DELIVERY_ATTEMPTS,
    )
    return scheduler
