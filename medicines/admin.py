from django.contrib import admin
from .models import Medicine,Reminder

# Register your models here.
class ReminderInline(admin.TabularInline):
    model = Reminder
    extra = 1
    
    
@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name','dosage','user')
    inlines = [ReminderInline]

