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
    medicine_name = serializers.CharField(source='reminder.medicine.name',read_only=True)
    medicine_dosage = serializers.CharField(source='reminder.medicine.dosage',read_only=True)
    medicine_photo = serializers.ImageField(source='reminder.medicine.photo',read_only=True)
    class Meta:
        model = DoseLog
        fields = ['id','reminder','scheduled_for','status','responded_at',
                  'medicine_name','medicine_dosage','medicine_photo']
        read_only_fields = ['responded_at']

