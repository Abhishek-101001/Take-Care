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
    owner_calls = models.PositiveSmallIntegerField(default=0)
    last_owner_call_at = models.DateTimeField(null=True, blank=True)
    
    
    class Meta:
        ordering = ['-scheduled_for']
        
        
    def __str__(self):
        return f'{self.reminder.medicine.name}-{self.scheduled_for:%d %b %I:%M %p}'
    

class Caregiver(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='caregivers',
    )
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    

    def __str__(self):
        return f'{self.name} (caregiver of {self.user})'



class Profile(models.Model):
    ROLE_CHOICES = [
        ('owner','Owner'),
        ('caregiver','Caregiver'),
    ]
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='owner')
    phone = models.CharField(max_length=20, blank=True)
    remind_owner = models.BooleanField(default=True)
    owner_call_interval = models.PositiveSmallIntegerField(default=5)
    owner_max_calls = models.PositiveSmallIntegerField(default=3)
    missed_after_minutes = models.PositiveSmallIntegerField(default=15)



    def __str__(self):
        return f'Profile of {self.user}'



class CareLink(models.Model):
    PRIORITY_CHOICES = [
        (1, 'Caregiver'),
        (2, 'Alternate caregiver'),
    ]
    caregiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='parent_links',
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='caregiver_links',
    )
    priority = models.PositiveSmallIntegerField(choices=PRIORITY_CHOICES, default=1)
    notify_after_minutes = models.PositiveSmallIntegerField(default=15)
    call_interval = models.PositiveSmallIntegerField(default=5)
    max_calls = models.PositiveSmallIntegerField(default=3)
    call_alerts = models.BooleanField(default=True)
    email_alerts = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['priority', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['caregiver', 'owner'], name='unique_care_link'
            ),
            models.UniqueConstraint(
                fields=['owner', 'priority'], name='one_caregiver_per_level'
            ),
        ]

    def __str__(self):
        return f'{self.caregiver} cares for {self.owner}'


class CaregiverAlert(models.Model):
    RESPONSE_CHOICES = [
        ('informed', "I'm informed"),
        ('handling', "I'll manage it now"),
    ]
    dose = models.ForeignKey(
        DoseLog, on_delete=models.CASCADE, related_name='caregiver_alerts'
    )
    link = models.ForeignKey(
        CareLink, on_delete=models.CASCADE, related_name='alerts'
    )
    calls_made = models.PositiveSmallIntegerField(default=0)
    last_called_at = models.DateTimeField(null=True, blank=True)
    emailed_at = models.DateTimeField(null=True, blank=True)
    response = models.CharField(max_length=10, choices=RESPONSE_CHOICES, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['dose', 'link'], name='unique_alert_per_dose_link'),
        ]

    def __str__(self):
        return f'Alert for {self.dose} to {self.link.caregiver}'

        