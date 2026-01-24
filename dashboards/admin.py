from django.contrib import admin
from .models import SavedDashboardView

@admin.register(SavedDashboardView)
class SavedDashboardViewAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at', 'updated_at', 'is_default')
    list_filter = ('created_at', 'updated_at', 'is_default')
    search_fields = ('name', 'description', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        """Filter to show only the user's saved views, or all for superusers."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)
    
    def save_model(self, request, obj, form, change):
        """Set the user to the current user when creating a new saved view."""
        if not change:
            obj.user = request.user
        super().save_model(request, obj, form, change)
