from django.db import models
from django.conf import settings
import json


class SavedDashboardView(models.Model):
    """Stores user-saved dashboard configurations"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_dashboards')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Filters
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=100, blank=True)
    cluster = models.CharField(max_length=100, blank=True)
    funder = models.CharField(max_length=100, blank=True)
    
    # Chart display options
    show_year_chart = models.BooleanField(default=True)
    show_status_chart = models.BooleanField(default=True)
    show_cluster_chart = models.BooleanField(default=True)
    show_funder_chart = models.BooleanField(default=True)
    show_quarter_chart = models.BooleanField(default=True)
    show_month_chart = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_default = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-updated_at']
        unique_together = ('user', 'name')
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    def get_filter_dict(self):
        """Return filter parameters as dict"""
        return {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'year': self.year,
            'status': self.status,
            'cluster': self.cluster,
            'funder': self.funder,
        }
