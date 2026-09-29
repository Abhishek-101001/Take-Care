from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import DoseLog



@shared_task
def check_missed_doses():
    threshold = timezone.now() - timedelta(minutes=15)
    overdue = DoseLog.objects.filter(status='pending', scheduled_for__lte=threshold)
    count = overdue.update(status='missed', responded_at=timezone.now())
    return f"Marked {count} dose(s) as missed"


    