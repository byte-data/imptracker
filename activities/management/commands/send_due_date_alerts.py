"""
Management command to send due date alerts for upcoming activity deadlines
Run with: python manage.py send_due_date_alerts
Schedule with cron or celery for regular execution
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from activities.models import Activity
from services.notifications import send_due_date_alert
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send due date reminder emails for activities with upcoming deadlines'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=None,
            help='Number of days ahead to check (default from settings)',
        )
        parser.add_argument(
            '--test',
            action='store_true',
            help='Send test email to superuser',
        )
        parser.add_argument(
            '--activity-id',
            type=int,
            default=None,
            help='Send alert for specific activity ID',
        )

    def handle(self, *args, **options):
        # Check if notifications are enabled
        if not settings.NOTIFICATIONS_ENABLED:
            self.stdout.write(
                self.style.WARNING('Notifications are disabled. Set NOTIFICATIONS_ENABLED=True in settings.')
            )
            return

        alert_days = options['days'] or settings.DUE_DATE_ALERT_DAYS
        test_mode = options['test']
        activity_id = options['activity_id']

        # Get activities with upcoming deadlines
        today = timezone.now().date()
        alert_date = today + timedelta(days=alert_days)

        query = Activity.objects.filter(
            planned_month__date__lte=alert_date,
            planned_month__date__gte=today,
            responsible_officer__isnull=False
        )

        if activity_id:
            query = query.filter(id=activity_id)

        activities = query.select_related('responsible_officer', 'status')

        if not activities.exists():
            self.stdout.write(
                self.style.SUCCESS(f'No activities found with due dates in the next {alert_days} days.')
            )
            return

        sent_count = 0
        failed_count = 0

        for activity in activities:
            try:
                # Calculate days remaining
                days_remaining = (activity.planned_month.date() - today).days

                if days_remaining < 0:
                    days_remaining = 0

                # Check if already sent alert today
                from activities.models import NotificationLog
                recent_alert = NotificationLog.objects.filter(
                    activity=activity,
                    notification_type='due_date_alert',
                    sent_at__date=today
                ).exists()

                if recent_alert:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Alert already sent today for {activity.name} (ID: {activity.activity_id})'
                        )
                    )
                    continue

                # Send alert
                if send_due_date_alert(activity, days_remaining):
                    sent_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Alert sent for {activity.name} ({days_remaining} days remaining)'
                        )
                    )
                else:
                    failed_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'✗ Failed to send alert for {activity.name}')
                    )

            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f'Error processing {activity.name}: {str(e)}')
                )
                logger.error(f'Error in send_due_date_alerts: {str(e)}')

        # Summary
        self.stdout.write(self.style.SUCCESS(f'\n✓ Sent {sent_count} alerts'))
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f'✗ Failed to send {failed_count} alerts'))

        self.stdout.write(
            self.style.SUCCESS(f'\nAlerts sent for activities due within {alert_days} days')
        )
