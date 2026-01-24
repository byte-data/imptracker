"""
Django management command to generate recurring activity instances
Usage:
    python manage.py generate_recurring_activities --months=3
    python manage.py generate_recurring_activities --months=6 --dry-run
    python manage.py generate_recurring_activities --activity-id=Y26-000001
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from activities.models import Activity
from services.recurrence import RecurrenceHandler
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generate instances for recurring activities'

    def add_arguments(self, parser):
        parser.add_argument(
            '--months',
            type=int,
            default=3,
            help='Number of months ahead to generate instances for (default: 3)'
        )
        parser.add_argument(
            '--activity-id',
            type=str,
            help='Generate only for specific activity ID (e.g., Y26-000001)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without saving'
        )
        parser.add_argument(
            '--no-m2m',
            action='store_true',
            help='Skip copying M2M relationships (clusters, funders)'
        )

    def handle(self, *args, **options):
        months = options['months']
        activity_id = options.get('activity_id')
        dry_run = options.get('dry_run', False)
        skip_m2m = options.get('no_m2m', False)
        
        # Convert months to number of periods to generate
        # For simplicity, generate one instance per month within the period
        num_periods = months
        
        # Get recurring activities
        if activity_id:
            try:
                recurring_activities = Activity.objects.filter(
                    activity_id=activity_id,
                    is_recurring=True
                )
                if not recurring_activities.exists():
                    self.stdout.write(
                        self.style.ERROR(f'Activity {activity_id} not found or not marked as recurring')
                    )
                    return
            except Activity.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Activity {activity_id} not found')
                )
                return
        else:
            recurring_activities = Activity.objects.filter(
                is_recurring=True,
                recurrence_end_date__isnull=True  # Indefinite
            ) | Activity.objects.filter(
                is_recurring=True,
                recurrence_end_date__gte=timezone.now().date()  # Not ended
            )
        
        if not recurring_activities.exists():
            self.stdout.write(self.style.WARNING('No recurring activities found'))
            return
        
        total_created = 0
        total_skipped = 0
        total_errors = 0
        
        self.stdout.write(
            self.style.SUCCESS(f'Found {recurring_activities.count()} recurring activity/ies')
        )
        self.stdout.write(f'Generating up to {num_periods} periods...\n')
        
        for parent in recurring_activities:
            self.stdout.write(f'Processing {parent.activity_id}: {parent.name}')
            
            # Generate instances
            instances, errors = RecurrenceHandler.generate_recurring_instances(
                parent,
                num_periods=num_periods
            )
            
            if errors:
                for error in errors:
                    self.stdout.write(self.style.ERROR(f'  ✗ {error}'))
                total_errors += len(errors)
                continue
            
            if not instances:
                self.stdout.write(self.style.WARNING('  (No new instances to create)'))
                total_skipped += 1
                continue
            
            if dry_run:
                for instance in instances:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  + {instance.activity_id} (would be generated) - {instance.planned_month}'
                        )
                    )
                total_skipped += len(instances)
            else:
                for instance in instances:
                    try:
                        # Save instance
                        instance.save()
                        
                        # Copy M2M relationships if not skipping
                        if not skip_m2m and hasattr(instance, '_temp_clusters'):
                            instance.clusters.set(instance._temp_clusters)
                            instance.funders.set(instance._temp_funders)
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ Created {instance.activity_id} - {instance.planned_month}'
                            )
                        )
                        total_created += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ Error saving {instance.activity_id}: {str(e)}')
                        )
                        total_errors += 1
            
            self.stdout.write('')  # Blank line for readability
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'Created: {total_created}'))
        if total_skipped:
            self.stdout.write(self.style.WARNING(f'Skipped: {total_skipped}'))
        if total_errors:
            self.stdout.write(self.style.ERROR(f'Errors: {total_errors}'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] No changes were saved'))
