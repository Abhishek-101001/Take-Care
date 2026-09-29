from  rest_framework import serializers
from .models import Medicine,Reminder,DoseLog



class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = ['id','time','is_active']
        
        
class MedicineSerializer(serializers.ModelSerializer):
    reminders = ReminderSerializer(many=True, read_only=True)
    
    class Meta:
        model = Medicine
        fields = ['id','name','dosage','instructions','photo','reminders','created_at']
        read_only_fields = ['user']

class DoseLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoseLog
        fields = ['id','reminder','scheduled_for','status','responded_at']
        read_only_fields = ['responded_at']

