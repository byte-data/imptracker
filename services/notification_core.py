"""Core synchronous notification email sending.

This module contains the actual email rendering/sending and NotificationLog writes.
It is called from background tasks in `services.notification_tasks`.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from activities.models import NotificationLog, NotificationPreference

logger = logging.getLogger(__name__)


def absolute_url(path: str) -> str:
    base = (getattr(settings, "SITE_URL", "") or "").strip()
    if not base:
        return ""
    base = base.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return f"{base}{path}"


def display_name(user) -> str:
    if not user:
        return "System"
    full = (user.get_full_name() or "").strip()
    return full or getattr(user, "username", "System")


def send_user_created_notification_sync(new_user, created_by=None) -> bool:
    if not settings.NOTIFICATIONS_ENABLED:
        return False

    if not getattr(new_user, "email", None):
        return False

    try:
        NotificationPreference.get_or_create_for_user(new_user)
    except Exception:
        pass

    try:
        subject = "Your ImpTracker account has been created"
        context = {
            "user": new_user,
            "created_by": display_name(created_by),
            "login_url": absolute_url("/login/"),
            "change_password_url": absolute_url("/accounts/profile/change-password/"),
        }

        html_message = render_to_string("emails/user_created.html", context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[new_user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info("User created notification sent to %s", new_user.email)
        return True
    except Exception:
        logger.exception("Failed to send user created notification")
        return False


def send_assignment_notification_sync(activity, recipient_user, assigned_by=None) -> bool:
    if not settings.NOTIFICATIONS_ENABLED:
        return False

    pref = NotificationPreference.get_or_create_for_user(recipient_user)
    if not pref.notify_on_assignment:
        return False

    try:
        subject = f"Activity Assignment: {activity.name}"

        context = {
            "user": recipient_user,
            "activity": activity,
            "assigned_by": assigned_by or "System",
            "activity_url": absolute_url(f"/activities/{activity.id}/"),
            "status": activity.status.name if activity.status else "Not Set",
            "budget": f"{activity.total_budget} {activity.currency.code}" if activity.currency else "N/A",
        }

        html_message = render_to_string("emails/assignment.html", context)
        plain_message = strip_tags(html_message)

        notification = NotificationLog.objects.create(
            activity=activity,
            recipient=recipient_user,
            sender=assigned_by,
            notification_type="assignment",
            subject=subject,
            email_address=recipient_user.email,
            message=plain_message,
            created_by=assigned_by,
            status="pending",
        )

        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_user.email],
                html_message=html_message,
                fail_silently=False,
            )
            notification.mark_as_sent()
            logger.info(
                "Assignment notification sent to %s for activity %s",
                recipient_user.email,
                activity.id,
            )
            return True
        except Exception as e:
            notification.mark_as_failed(str(e))
            logger.error("Failed to send assignment notification: %s", str(e))
            return False

    except Exception:
        logger.exception("Error creating assignment notification")
        return False


def send_status_change_notification_sync(activity, old_status: str, new_status: str, changed_by=None) -> bool:
    if not settings.NOTIFICATIONS_ENABLED:
        return False

    if not activity.responsible_officer:
        return False

    pref = NotificationPreference.get_or_create_for_user(activity.responsible_officer)
    if not pref.notify_on_status_change:
        return False

    try:
        subject = f"Status Change: {activity.name}"

        context = {
            "user": activity.responsible_officer,
            "activity": activity,
            "old_status": old_status,
            "new_status": new_status,
            "changed_by": changed_by or "System",
            "activity_url": absolute_url(f"/activities/{activity.id}/"),
        }

        html_message = render_to_string("emails/status_change.html", context)
        plain_message = strip_tags(html_message)

        notification = NotificationLog.objects.create(
            activity=activity,
            recipient=activity.responsible_officer,
            sender=changed_by,
            notification_type="status_change",
            subject=subject,
            email_address=activity.responsible_officer.email,
            message=plain_message,
            created_by=changed_by,
            status="pending",
        )

        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[activity.responsible_officer.email],
                html_message=html_message,
                fail_silently=False,
            )
            notification.mark_as_sent()
            logger.info("Status change notification sent to %s", activity.responsible_officer.email)
            return True
        except Exception as e:
            notification.mark_as_failed(str(e))
            logger.error("Failed to send status change notification: %s", str(e))
            return False

    except Exception:
        logger.exception("Error creating status change notification")
        return False


def send_due_date_alert_sync(activity, days_remaining: int) -> bool:
    if not settings.NOTIFICATIONS_ENABLED:
        return False

    if not activity.responsible_officer:
        return False

    pref = NotificationPreference.get_or_create_for_user(activity.responsible_officer)
    if not pref.notify_on_due_date_alert:
        return False

    try:
        subject = f"Due Date Reminder: {activity.name} due in {days_remaining} days"

        context = {
            "user": activity.responsible_officer,
            "activity": activity,
            "days_remaining": days_remaining,
            "due_date": activity.planned_month.strftime("%B %d, %Y") if activity.planned_month else "Not set",
            "activity_url": absolute_url(f"/activities/{activity.id}/"),
        }

        html_message = render_to_string("emails/due_date_alert.html", context)
        plain_message = strip_tags(html_message)

        notification = NotificationLog.objects.create(
            activity=activity,
            recipient=activity.responsible_officer,
            notification_type="due_date_alert",
            subject=subject,
            email_address=activity.responsible_officer.email,
            message=plain_message,
            status="pending",
        )

        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[activity.responsible_officer.email],
                html_message=html_message,
                fail_silently=False,
            )
            notification.mark_as_sent()
            logger.info("Due date alert sent to %s", activity.responsible_officer.email)
            return True
        except Exception as e:
            notification.mark_as_failed(str(e))
            logger.error("Failed to send due date alert: %s", str(e))
            return False

    except Exception:
        logger.exception("Error creating due date alert")
        return False


def send_activity_update_notification_sync(activity, update_description: str, notified_users=None) -> bool:
    if not settings.NOTIFICATIONS_ENABLED:
        return False

    if notified_users is None:
        if activity.responsible_officer:
            notified_users = [activity.responsible_officer]
        else:
            return False

    sent_count = 0
    for user in notified_users:
        try:
            pref = NotificationPreference.get_or_create_for_user(user)
            if not pref.notify_on_activity_update:
                continue

            subject = f"Activity Update: {activity.name}"

            context = {
                "user": user,
                "activity": activity,
                "update": update_description,
                "activity_url": absolute_url(f"/activities/{activity.id}/"),
            }

            html_message = render_to_string("emails/activity_update.html", context)
            plain_message = strip_tags(html_message)

            notification = NotificationLog.objects.create(
                activity=activity,
                recipient=user,
                notification_type="update",
                subject=subject,
                email_address=user.email,
                message=plain_message,
                status="pending",
            )

            try:
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                notification.mark_as_sent()
                sent_count += 1
                logger.info("Activity update notification sent to %s", user.email)
            except Exception as e:
                notification.mark_as_failed(str(e))
                logger.error("Failed to send activity update notification: %s", str(e))

        except Exception:
            logger.exception("Error sending activity update notification")

    return sent_count > 0
