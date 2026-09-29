from django.contrib import admin
from .models import Medicine,Reminder,DoseLog

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

