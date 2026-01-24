"""
Data migration to seed initial Procurement Types
Run this after creating the ProcurementType model migration:
    python manage.py makemigrations
    python manage.py migrate
    python manage.py shell < seed_procurement_types.py
"""

from masters.models import ProcurementType

# Initial procurement types based on previous hardcoded choices
initial_types = [
    {'code': 'equipment', 'name': 'Equipment', 'is_default': True},
    {'code': 'services', 'name': 'Services', 'is_default': False},
    {'code': 'supplies', 'name': 'Supplies', 'is_default': False},
    {'code': 'venue', 'name': 'Venue/Logistics', 'is_default': False},
    {'code': 'staff', 'name': 'Staff', 'is_default': False},
    {'code': 'other', 'name': 'Other', 'is_default': False},
]

print("Seeding Procurement Types...")
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
        print(f"✓ Created: {proc_type.name} ({proc_type.code})")
    else:
        print(f"- Already exists: {proc_type.name} ({proc_type.code})")

print(f"\nTotal Procurement Types: {ProcurementType.objects.count()}")
