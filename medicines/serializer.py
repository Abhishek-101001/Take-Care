from  rest_framework import serializers
from .models import Medicine,Reminder



class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = ['id','time','is_active']
        
        
class MedicineSerializer(serializers.ModelSerializer):
    reminders = ReminderSerializer(many=True, read_only=True)
    
    class Meta:
        model = Medicine
        fields = ['id','name','dosage','instructions','photo','reminders','createda_at']
        read_only_fields = ['user']

