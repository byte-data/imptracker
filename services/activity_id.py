# def generate_activity_id(year): return f'Y{str(year)[-2:]}-000001'

from django.db.models import Max
from activities.models import Activity

def generate_activity_id(year):
    prefix = f"Y{str(year)[-2:]}"
    last_seq = Activity.objects.filter(year=year).aggregate(
        Max("sequence")
    )["sequence__max"] or 0

    next_seq = last_seq + 1
    return {
        "sequence": next_seq,
        "activity_id": f"{prefix}-{str(next_seq).zfill(6)}"
    }

