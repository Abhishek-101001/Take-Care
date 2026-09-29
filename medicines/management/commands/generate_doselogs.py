from django.core.management.base import BaseCommand
from django.utils import timezone
from medicines.models import Reminder, DoseLog



class Command(BaseCommand):
    help = "Generate today's DoseLog entries from active Reminders"
    
    
    def handle(self,*args, **kwargs):
        today = timezone.localdate()
        count = 0 
        
        for reminder in Reminder.objects.filter(is_active=True):
            scheduled_dt = timezone.make_aware(
                timezone.datetime.combine(today, reminder.time)
            )
            _, created = DoseLog.objects.get_or_create(
                reminder = reminder,
                scheduled_for = scheduled_dt,
                defaults = {'status':'pending'}
            )
            if created:
                count+=1
        self.stdout.write(self.style.SUCCESS(f"Created {count} dose log(s) for {today}"))
            