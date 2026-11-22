from django.contrib import admin
from .models import Medicine,Reminder,DoseLog,Caregiver,Profile

# Register your models here.
class ReminderInline(admin.TabularInline):
    model = Reminder
    extra = 1
    
    
@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name','dosage','user')
    inlines = [ReminderInline]
    
@admin.register(DoseLog)
class DoseLogAdmin(admin.ModelAdmin):
    list_display = ('reminder','scheduled_for','status','responded_at')
    list_filter = ('status',)


@admin.register(Caregiver)
class CaregiverAdmin(admin.ModelAdmin):
    list_display = ('name','email','phone','user')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone')


