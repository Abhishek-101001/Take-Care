from django.db import models
from django.conf import settings
from django.utils import timezone

# Create your models here.
class Medicine(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name = 'medicines',
    )
    name = models.CharField(max_length=100)
    dosage = models.CharField(max_length=50,help_text='e.g. 1 tablet, 5 ml')
    instructions = models.CharField(max_length=200,blank=True,null=True)
    photo = models.ImageField(upload_to='pill_photos/',blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.name}({self.dosage})'


class Reminder(models.Model):
    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE,
        related_name='reminders',
    )
    time = models.TimeField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering =['time']
        
    def  __str__(self):
        return f'{self.medicine.name} at {self.time:%I:%M %p}'
    

class DoseLog(models.Model):
    STATUS_CHOICES = [
        ('pending','Pending'),
        ('taken','Taken'),
        ('missed','Missed'),
    ]
    reminder = models.ForeignKey(
        Reminder,
        on_delete = models.CASCADE,
        related_name ='logs',
    )
    scheduled_for = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    responded_at = models.DateTimeField(null=True, blank=True)
    
    
    class Meta:
        ordering = ['-scheduled_for']
        
        
    def __str__(self):
        return f'{self.reminder.medicine.name}-{self.scheduled_for:%d %b %I:%M %p}'
    