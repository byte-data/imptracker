"""
Email notification service for activities
Handles sending emails for assignments, status changes, and reminders
"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from activities.models import NotificationLog, NotificationPreference
import logging

logger = logging.getLogger(__name__)


def _absolute_url(path: str) -> str:
    base = (getattr(settings, "SITE_URL", "") or "").strip()
    if not base:
        return ""
    base = base.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return f"{base}{path}"


def _display_name(user) -> str:
    if not user:
        return "System"
    full = (user.get_full_name() or "").strip()
    return full or getattr(user, "username", "System")


def send_user_created_notification(new_user, created_by=None):
    """Send an email to the newly created user advising them to change password."""
    if not settings.NOTIFICATIONS_ENABLED:
        return False

    if not getattr(new_user, "email", None):
        return False

    # Ensure preference row exists for the user (defaults)
    try:
        NotificationPreference.get_or_create_for_user(new_user)
    except Exception:
        pass

    try:
        subject = "Your ImpTracker account has been created"
        context = {
            "user": new_user,
            "created_by": _display_name(created_by),
            "login_url": _absolute_url("/login/"),
            "change_password_url": _absolute_url("/accounts/profile/change-password/"),
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

        logger.info(f"User created notification sent to {new_user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send user created notification: {str(e)}")
        return False


def send_assignment_notification(activity, recipient_user, assigned_by=None):
    """
    Send notification email when an activity is assigned to a user
    
    Args:
        activity: Activity instance
        recipient_user: User instance receiving the assignment
        assigned_by: User instance who made the assignment
    """
    if not settings.NOTIFICATIONS_ENABLED:
        return False
    
    # Check user preferences
    pref = NotificationPreference.get_or_create_for_user(recipient_user)
    if not pref.notify_on_assignment:
        return False
    
    try:
        subject = f"Activity Assignment: {activity.name}"
        
        # Create email context
        context = {
            'user': recipient_user,
            'activity': activity,
            'assigned_by': assigned_by or 'System',
            'activity_url': _absolute_url(f"/activities/{activity.id}/"),
            'status': activity.status.name if activity.status else 'Not Set',
            'budget': f"{activity.total_budget} {activity.currency.code}" if activity.currency else 'N/A',
        }
        
        # Render HTML email
        html_message = render_to_string('emails/assignment.html', context)
        plain_message = strip_tags(html_message)
        
        # Create notification log
        notification = NotificationLog.objects.create(
            activity=activity,
            recipient=recipient_user,
            sender=assigned_by,
            notification_type='assignment',
            subject=subject,
            email_address=recipient_user.email,
            message=plain_message,
            created_by=assigned_by,
            status='pending'
        )
        
        # Send email
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
            logger.info(f"Assignment notification sent to {recipient_user.email} for activity {activity.id}")
            return True
        except Exception as e:
            notification.mark_as_failed(str(e))
            logger.error(f"Failed to send assignment notification: {str(e)}")
            return False
    
    except Exception as e:
        logger.error(f"Error creating assignment notification: {str(e)}")
        return False


def send_status_change_notification(activity, old_status, new_status, changed_by=None):
    """
    Send notification email when activity status changes
    
    Args:
        activity: Activity instance
        old_status: Previous status
        new_status: New status
        changed_by: User who made the change
    """
    if not settings.NOTIFICATIONS_ENABLED:
        return False
    
    # Send to responsible officer
    if not activity.responsible_officer:
        return False
    
    # Check preferences
    pref = NotificationPreference.get_or_create_for_user(activity.responsible_officer)
    if not pref.notify_on_status_change:
        return False
    
    try:
        subject = f"Status Change: {activity.name}"
        
        context = {
            'user': activity.responsible_officer,
            'activity': activity,
            'old_status': old_status,
            'new_status': new_status,
            'changed_by': changed_by or 'System',
            'activity_url': _absolute_url(f"/activities/{activity.id}/"),
        }
        
        html_message = render_to_string('emails/status_change.html', context)
        plain_message = strip_tags(html_message)
        
        notification = NotificationLog.objects.create(
            activity=activity,
            recipient=activity.responsible_officer,
            sender=changed_by,
            notification_type='status_change',
            subject=subject,
            email_address=activity.responsible_officer.email,
            message=plain_message,
            created_by=changed_by,
            status='pending'
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
            logger.info(f"Status change notification sent to {activity.responsible_officer.email}")
            return True
        except Exception as e:
            notification.mark_as_failed(str(e))
            logger.error(f"Failed to send status change notification: {str(e)}")
            return False
    
    except Exception as e:
        logger.error(f"Error creating status change notification: {str(e)}")
        return False


def send_due_date_alert(activity, days_remaining):
    """
    Send due date reminder email
    
    Args:
        activity: Activity instance
        days_remaining: Number of days until due date
    """
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
            'user': activity.responsible_officer,
            'activity': activity,
            'days_remaining': days_remaining,
            'due_date': activity.planned_month.strftime('%B %d, %Y') if activity.planned_month else 'Not set',
            'activity_url': _absolute_url(f"/activities/{activity.id}/"),
        }
        
        html_message = render_to_string('emails/due_date_alert.html', context)
        plain_message = strip_tags(html_message)
        
        notification = NotificationLog.objects.create(
            activity=activity,
            recipient=activity.responsible_officer,
            notification_type='due_date_alert',
            subject=subject,
            email_address=activity.responsible_officer.email,
            message=plain_message,
            status='pending'
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
            logger.info(f"Due date alert sent to {activity.responsible_officer.email}")
            return True
        except Exception as e:
            notification.mark_as_failed(str(e))
            logger.error(f"Failed to send due date alert: {str(e)}")
            return False
    
    except Exception as e:
        logger.error(f"Error creating due date alert: {str(e)}")
        return False


def send_activity_update_notification(activity, update_description, notified_users=None):
    """
    Send activity update notification to responsible officer and/or specific users
    
    Args:
        activity: Activity instance
        update_description: Description of what changed
        notified_users: List of User instances to notify (defaults to responsible officer)
    """
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
                'user': user,
                'activity': activity,
                'update': update_description,
                'activity_url': _absolute_url(f"/activities/{activity.id}/"),
            }
            
            html_message = render_to_string('emails/activity_update.html', context)
            plain_message = strip_tags(html_message)
            
            notification = NotificationLog.objects.create(
                activity=activity,
                recipient=user,
                notification_type='update',
                subject=subject,
                email_address=user.email,
                message=plain_message,
                status='pending'
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
                logger.info(f"Activity update notification sent to {user.email}")
            except Exception as e:
                notification.mark_as_failed(str(e))
                logger.error(f"Failed to send activity update notification: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error sending activity update notification: {str(e)}")
    
    return sent_count > 0


def retry_failed_notifications(max_retries=3):
    """
    Retry sending failed notifications
    
    Args:
        max_retries: Maximum number of retries
    """
    failed_notifications = NotificationLog.objects.filter(
        status='failed',
        retry_count__lt=max_retries
    ).order_by('created_at')[:10]
    
    retry_count = 0
    for notification in failed_notifications:
        try:
            notification.status = 'retrying'
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
            logger.info(f"Retry sent for notification {notification.id}")
        except Exception as e:
            notification.mark_as_failed(str(e))
            logger.error(f"Retry failed for notification {notification.id}: {str(e)}")
    
    return retry_count
