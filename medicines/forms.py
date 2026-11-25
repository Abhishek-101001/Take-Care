from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

from .models import Profile
from .utils import clean_phone as normalize_phone

User = get_user_model()


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=60, label='Your name')
    email = forms.EmailField(label='Email')
    phone = forms.CharField(max_length=20, label='Mobile number')
    agree = forms.BooleanField(label='I agree to receive reminder calls and emails')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = 'form-check-input' if name == 'agree' else 'form-control form-control-lg'
            field.widget.attrs['class'] = css

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data['phone'])
        if not phone:
            raise forms.ValidationError('Enter a valid mobile number, for example 9793123011.')
        return phone

    def save(self, role):
        with transaction.atomic():
            user = super().save()
            Profile.objects.create(user=user, role=role, phone=self.cleaned_data['phone'])
        return user
        