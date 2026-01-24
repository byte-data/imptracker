from django.core.management.base import BaseCommand
from masters.models import ProcurementType


class Command(BaseCommand):
    help = 'Seed initial procurement types'

    def handle(self, *args, **options):
        initial_types = [
            {'code': 'equipment', 'name': 'Equipment', 'is_default': True},
            {'code': 'services', 'name': 'Services', 'is_default': False},
            {'code': 'supplies', 'name': 'Supplies', 'is_default': False},
            {'code': 'venue', 'name': 'Venue/Logistics', 'is_default': False},
            {'code': 'staff', 'name': 'Staff', 'is_default': False},
            {'code': 'other', 'name': 'Other', 'is_default': False},
        ]

        self.stdout.write("Seeding Procurement Types...")
        for type_data in initial_types:
            proc_type, created = ProcurementType.objects.get_or_create(
                code=type_data['code'],
                defaults={
                    'name': type_data['name'],
                    'active': True,
                    'is_default': type_data['is_default']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✓ Created: {proc_type.name} ({proc_type.code})"))
            else:
                self.stdout.write(f"- Already exists: {proc_type.name} ({proc_type.code})")

        total = ProcurementType.objects.count()
        self.stdout.write(self.style.SUCCESS(f"\nTotal Procurement Types: {total}"))
