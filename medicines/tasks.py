import logging
from datetime import timedelta

from celery import shared_task
from django.core.mail import send_mail
from django.core.management import call_command
from django.utils import timezone
from django.conf import settings
from twilio.rest import Client
from .models import DoseLog, Profile
from .utils import clean_phone

logger = logging.getLogger(__name__)
ALERT_MAX_LATE = timedelta(hours=2)

TRIAL_CALL_URL = 'https://webhooks.twilio.com/v1/Voice/Template/voice_text_to_speech'


def send_missed_alert(dose):
    medicine = dose.reminder.medicine
    user = medicine.user
    emails = list(user.caregivers.values_list('email', flat=True))
    if not emails:
        return  # no caregiver saved for this user

    when = timezone.localtime(dose.scheduled_for).strftime('%I:%M %p')
    send_mail(
        subject=f'Missed dose: {medicine.name}',
        message=(
            f'{user.get_username()} has not taken {medicine.name} '
            f'({medicine.dosage}) that was due at {when}.\n\n'
            'Please check on them.'
        ),
        from_email=None,
        recipient_list=emails,
    )

def send_missed_call(dose):
    user = dose.reminder.medicine.user
    phones = list(user.caregivers.values_list('phone', flat=True))
    if not phones:
        return  # no caregiver saved for this user

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    for raw_phone in phones:
        phone = clean_phone(raw_phone)
        if not phone:
            logger.warning('Skipping an invalid caregiver phone number for dose %s', dose.id)
            continue  # skip a caregiver with an empty phone field
        client.calls.create(
            to=phone,
            from_=settings.TWILIO_PHONE_NUMBER,
            url=TRIAL_CALL_URL,
        )

def send_owner_call(dose):
    user = dose.reminder.medicine.user
    raw_phone = Profile.objects.filter(user=user).values_list('phone', flat=True).first()
    phone = clean_phone(raw_phone)
    if not phone:
        logger.warning('No usable owner phone for dose %s', dose.id)
        return

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    client.calls.create(
        to=phone,
        from_=settings.TWILIO_PHONE_NUMBER,
        url=TRIAL_CALL_URL,
    )


@shared_task
def check_missed_doses():
    threshold = timezone.now() - timedelta(minutes=15)
    stale_cutoff = timezone.now() - ALERT_MAX_LATE
    overdue = list(
        DoseLog.objects.filter(status='pending', scheduled_for__lte=threshold)
        .select_related('reminder__medicine__user')
    )
    for dose in overdue:
        dose.status = 'missed'
        dose.responded_at = timezone.now()
        dose.save()
        if dose.scheduled_for < stale_cutoff:
            logger.warning('Dose %s is too old for alerts ; marked missed only',dose.id)
            continue
        try:
            send_missed_alert(dose)
        except Exception:
            logger.exception('Could not send missed-dose email')
        try:
            send_missed_call(dose)
        except Exception:
            logger.exception('Could not send missed-dose call')
    return f'Marked {len(overdue)} dose(s) as missed'


@shared_task
def send_owner_reminders():
    now = timezone.now()
    window_start = now - timedelta(minutes=15)
    due = list(
        DoseLog.objects.filter(
            status='pending',
            scheduled_for__lte=now,
            scheduled_for__gt=window_start,
        ).select_related('reminder__medicine__user')
    )
    for dose in due:
        try:
            send_owner_call(dose)
        except Exception:
            logger.exception('Could not place owner reminder call')
    return f'Called owners for {len(due)} dose(s)'


@shared_task
def create_today_doses_logs():
    call_command('generate_doselogs')