from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from .models import User, Cluster


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
	list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
	filter_horizontal = ('clusters', 'groups')


@admin.register(Cluster)
class ClusterAdmin(admin.ModelAdmin):
	list_display = ('short_name', 'full_name')

# Ensure groups are visible in admin
admin.site.unregister(Group)
admin.site.register(Group)
