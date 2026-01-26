from django.apps import apps
from django.tasks import task

from services.notification_core import (
    send_activity_update_notification_sync,
    send_assignment_notification_sync,
    send_due_date_alert_sync,
    send_status_change_notification_sync,
    send_user_created_notification_sync,
)


@task
def task_send_user_created_notification(user_id: int, created_by_id: int | None = None) -> bool:
    User = apps.get_model("accounts", "User")
    user = User.objects.get(pk=user_id)
    created_by = User.objects.get(pk=created_by_id) if created_by_id else None
    return send_user_created_notification_sync(user, created_by=created_by)


@task
def task_send_assignment_notification(activity_id: int, recipient_user_id: int, assigned_by_id: int | None = None) -> bool:
    Activity = apps.get_model("activities", "Activity")
    User = apps.get_model("accounts", "User")
    activity = Activity.objects.get(pk=activity_id)
    recipient_user = User.objects.get(pk=recipient_user_id)
    assigned_by = User.objects.get(pk=assigned_by_id) if assigned_by_id else None
    return send_assignment_notification_sync(activity, recipient_user, assigned_by=assigned_by)


@task
def task_send_status_change_notification(
    activity_id: int,
    old_status: str,
    new_status: str,
    changed_by_id: int | None = None,
) -> bool:
    Activity = apps.get_model("activities", "Activity")
    User = apps.get_model("accounts", "User")
    activity = Activity.objects.get(pk=activity_id)
    changed_by = User.objects.get(pk=changed_by_id) if changed_by_id else None
    return send_status_change_notification_sync(activity, old_status, new_status, changed_by=changed_by)


@task
def task_send_due_date_alert(activity_id: int, days_remaining: int) -> bool:
    Activity = apps.get_model("activities", "Activity")
    activity = Activity.objects.get(pk=activity_id)
    return send_due_date_alert_sync(activity, days_remaining)


@task
def task_send_activity_update_notification(activity_id: int, update_description: str, user_ids: list[int] | None = None) -> bool:
    Activity = apps.get_model("activities", "Activity")
    User = apps.get_model("accounts", "User")
    activity = Activity.objects.get(pk=activity_id)
    notified_users = None
    if user_ids is not None:
        notified_users = list(User.objects.filter(pk__in=user_ids))
    return send_activity_update_notification_sync(activity, update_description, notified_users=notified_users)
