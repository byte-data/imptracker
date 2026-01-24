from django.apps import AppConfig
from django.db.models.signals import post_migrate


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # Create default role groups after migrations complete
        def create_groups(sender, **kwargs):
            from django.contrib.auth.models import Group
            role_names = [
                'System Admin',
                'User Manager',
                'Data Manager',
                'Activity Manager',
                'Viewer',
            ]
            for rn in role_names:
                Group.objects.get_or_create(name=rn)
        
        post_migrate.connect(create_groups, sender=self)
