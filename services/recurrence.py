"""
Recurrence service for handling recurring activities
Handles date calculations, instance generation, and recurrence pattern logic
"""

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class RecurrenceHandler:
    """Utility class to handle recurring activity logic"""
    
    PATTERN_TO_MONTHS = {
        'monthly': 1,
        'quarterly': 3,
        'bi_annual': 6,
        'annual': 12,
    }
    
    @staticmethod
    def get_next_occurrence(current_date, pattern, interval=1):
        """
        Calculate next occurrence date based on pattern and interval
        
        Args:
            current_date: date object (should be last day of month)
            pattern: str - 'monthly', 'quarterly', 'bi_annual', 'annual'
            interval: int - repeat every N periods
            
        Returns:
            date - last day of month for next occurrence
        """
        if pattern not in RecurrenceHandler.PATTERN_TO_MONTHS:
            raise ValueError(f"Invalid recurrence pattern: {pattern}")
        
        # Get months to add based on pattern and interval
        months_to_add = RecurrenceHandler.PATTERN_TO_MONTHS[pattern] * interval
        
        # Calculate next date
        next_date = current_date + relativedelta(months=months_to_add)
        
        # Normalize to last day of month
        return RecurrenceHandler._last_day_of_month(next_date)
    
    @staticmethod
    def _last_day_of_month(dt):
        """Return last day of the month for given date"""
        next_month = dt + relativedelta(day=1, months=1)
        return next_month - timedelta(days=1)
    
    @staticmethod
    def generate_recurring_instances(parent_activity, num_periods=3):
        """
        Generate recurring activity instances for the parent activity
        
        Args:
            parent_activity: Activity instance with is_recurring=True
            num_periods: int - number of periods to generate (default 3)
            
        Returns:
            tuple: (list of Activity objects (unsaved), list of validation errors)
        """
        from activities.models import Activity
        
        errors = []
        instances = []
        
        # Validate parent activity
        if not parent_activity.is_recurring:
            errors.append("Parent activity is not marked as recurring")
            return instances, errors
        
        if not parent_activity.recurrence_pattern:
            errors.append("Recurrence pattern not set")
            return instances, errors
        
        if parent_activity.recurrence_interval is None or parent_activity.recurrence_interval < 1:
            errors.append("Recurrence interval must be at least 1")
            return instances, errors
        
        # Get recurrence parameters
        pattern = parent_activity.recurrence_pattern
        interval = parent_activity.recurrence_interval
        start_date = parent_activity.planned_month
        end_date = parent_activity.recurrence_end_date
        
        # Generate instances
        current_date = start_date
        generated_count = 0
        
        while generated_count < num_periods:
            # Calculate next occurrence
            try:
                next_date = RecurrenceHandler.get_next_occurrence(current_date, pattern, interval)
            except ValueError as e:
                errors.append(f"Error calculating next occurrence: {str(e)}")
                break
            
            # Check if we've exceeded the end date
            if end_date and next_date > end_date:
                logger.info(f"Recurrence end date reached for {parent_activity.activity_id}")
                break
            
            # Check if instance already exists for this date
            existing = Activity.objects.filter(
                parent_activity=parent_activity,
                planned_month=next_date
            ).exists()
            
            if existing:
                logger.info(f"Instance already exists for {parent_activity.activity_id} on {next_date}")
                current_date = next_date
                continue
            
            # Create new instance (unsaved)
            instance = Activity(
                name=parent_activity.name,
                year=next_date.year,
                status=parent_activity.status,
                planned_month=next_date,
                quarter=RecurrenceHandler._calculate_quarter(next_date),
                total_budget=parent_activity.total_budget,
                disbursed_amount=parent_activity.disbursed_amount,
                currency=parent_activity.currency,
                responsible_officer=parent_activity.responsible_officer,
                notes=f"[Recurring] {parent_activity.notes}",
                technical_report_available=False,
                
                # Recurrence fields
                is_recurring=False,  # Generated instances are not themselves recurring
                parent_activity=parent_activity,
                generated_from_recurrence=True,
                
                # Procurement fields (inherit from parent)
                is_procurement=parent_activity.is_procurement,
                procurement_type=parent_activity.procurement_type,
                procurement_amount=parent_activity.procurement_amount,
                has_partial_procurement=parent_activity.has_partial_procurement,
            )
            
            # Copy M2M relationships (clusters, funders)
            # Note: Will need to be handled after save() in caller
            instance._temp_clusters = list(parent_activity.clusters.all())
            instance._temp_funders = list(parent_activity.funders.all())
            
            instances.append(instance)
            generated_count += 1
            current_date = next_date
        
        logger.info(f"Generated {len(instances)} instances for recurring activity {parent_activity.activity_id}")
        return instances, errors
    
    @staticmethod
    def _calculate_quarter(dt):
        """Calculate quarter from date"""
        return ((dt.month - 1) // 3) + 1
    
    @staticmethod
    def get_next_scheduled_date(parent_activity):
        """
        Get the next date when this recurring activity should be scheduled
        
        Args:
            parent_activity: Activity instance with is_recurring=True
            
        Returns:
            date or None if recurrence has ended
        """
        if not parent_activity.is_recurring:
            return None
        
        last_instance = parent_activity.recurring_instances.order_by('-planned_month').first()
        
        if last_instance:
            current_date = last_instance.planned_month
        else:
            current_date = parent_activity.planned_month
        
        try:
            next_date = RecurrenceHandler.get_next_occurrence(
                current_date,
                parent_activity.recurrence_pattern,
                parent_activity.recurrence_interval
            )
        except ValueError:
            return None
        
        # Check if it exceeds end date
        if parent_activity.recurrence_end_date and next_date > parent_activity.recurrence_end_date:
            return None
        
        return next_date
