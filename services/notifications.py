"""Notification API.

Public functions keep the original signatures but enqueue work via Django 6 tasks.
The actual email rendering/sending happens in `services.notification_core`.
"""

import logging

from django.conf import settings

from activities.models import NotificationLog

logger = logging.getLogger(__name__)


def send_user_created_notification(new_user, created_by=None) -> bool:
    if not settings.NOTIFICATIONS_ENABLED:
        return False

    user_id = getattr(new_user, "pk", None)
    if not user_id:
        return False

    created_by_id = getattr(created_by, "pk", None) if created_by else None

    try:
        from services.notification_tasks import task_send_user_created_notification

        task_send_user_created_notification.enqueue(user_id, created_by_id)
        return True
    except Exception:
        logger.exception("Failed to enqueue user created notification; falling back to sync")
        from services.notification_core import send_user_created_notification_sync

        return send_user_created_notification_sync(new_user, created_by=created_by)


def send_assignment_notification(activity, recipient_user, assigned_by=None) -> bool:
    if not settings.NOTIFICATIONS_ENABLED:
        return False

    activity_id = getattr(activity, "pk", None)
    recipient_user_id = getattr(recipient_user, "pk", None)
    if not activity_id or not recipient_user_id:
        return False

    assigned_by_id = getattr(assigned_by, "pk", None) if assigned_by else None

    try:
        from services.notification_tasks import task_send_assignment_notification

        task_send_assignment_notification.enqueue(activity_id, recipient_user_id, assigned_by_id)
        return True
    except Exception:
        logger.exception("Failed to enqueue assignment notification; falling back to sync")
        from services.notification_core import send_assignment_notification_sync

        return send_assignment_notification_sync(activity, recipient_user, assigned_by=assigned_by)


def send_status_change_notification(activity, old_status, new_status, changed_by=None) -> bool:
    if not settings.NOTIFICATIONS_ENABLED:
        return False

    activity_id = getattr(activity, "pk", None)
    if not activity_id:
        return False

    changed_by_id = getattr(changed_by, "pk", None) if changed_by else None

    try:
        from services.notification_tasks import task_send_status_change_notification

        task_send_status_change_notification.enqueue(activity_id, old_status, new_status, changed_by_id)
        return True
    except Exception:
        logger.exception("Failed to enqueue status change notification; falling back to sync")
        from services.notification_core import send_status_change_notification_sync

        return send_status_change_notification_sync(activity, old_status, new_status, changed_by=changed_by)


def send_due_date_alert(activity, days_remaining) -> bool:
    if not settings.NOTIFICATIONS_ENABLED:
        return False

    activity_id = getattr(activity, "pk", None)
    if not activity_id:
        return False

    try:
        from services.notification_tasks import task_send_due_date_alert

        task_send_due_date_alert.enqueue(activity_id, int(days_remaining))
        return True
    except Exception:
        logger.exception("Failed to enqueue due date alert; falling back to sync")
        from services.notification_core import send_due_date_alert_sync

        return send_due_date_alert_sync(activity, int(days_remaining))


def send_activity_update_notification(activity, update_description, notified_users=None) -> bool:
    if not settings.NOTIFICATIONS_ENABLED:
        return False

    activity_id = getattr(activity, "pk", None)
    if not activity_id:
        return False

    user_ids = None
    if notified_users is not None:
        user_ids = [u.pk for u in notified_users if getattr(u, "pk", None)]

    try:
        from services.notification_tasks import task_send_activity_update_notification

        task_send_activity_update_notification.enqueue(activity_id, str(update_description), user_ids)
        return True
    except Exception:
        logger.exception("Failed to enqueue activity update notification; falling back to sync")
        from services.notification_core import send_activity_update_notification_sync

        return send_activity_update_notification_sync(activity, update_description, notified_users=notified_users)


def retry_failed_notifications(max_retries=3):
    """Retry sending failed notifications synchronously."""
    from django.core.mail import send_mail

    failed_notifications = NotificationLog.objects.filter(
        status="failed",
        retry_count__lt=max_retries,
    ).order_by("created_at")[:10]

    retry_count = 0
    for notification in failed_notifications:
        try:
            notification.status = "retrying"
            notification.save()

            send_mail(
                subject=notification.subject,
                message=notification.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.email_address],
                fail_silently=False,
            )
            notification.mark_as_sent()
            retry_count += 1
            logger.info("Retry sent for notification %s", notification.id)
        except Exception as e:
            notification.mark_as_failed(str(e))
            logger.error("Retry failed for notification %s: %s", notification.id, str(e))

    return retry_count
