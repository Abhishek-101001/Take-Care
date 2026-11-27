import logging
from datetime import timedelta

from celery import shared_task
from django.core.mail import send_mail
from django.core.management import call_command
from django.utils import timezone
from django.conf import settings
from twilio.rest import Client
from .models import DoseLog, Profile, CaregiverAlert
from .utils import clean_phone

logger = logging.getLogger(__name__)
ALERT_MAX_LATE = timedelta(hours=2)
HARD_MAX_CALLS = 20
CALL_TOLERANCE = timedelta(seconds=10)
HARD_TOTAL_CALLS = 30

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


def link_turn(scheduled_for, link, previous_end=None):
    """When does this caregiver's turn start and end for a dose due at scheduled_for?"""
    start = scheduled_for + timedelta(minutes=link.notify_after_minutes)
    if previous_end is not None and previous_end > start:
        start = previous_end
    if not (link.call_alerts or link.email_alerts):
        return start, start  # nothing to send, so the turn is empty
    max_calls = max(1, min(link.max_calls, HARD_MAX_CALLS))
    end = start + timedelta(minutes=link.call_interval * max_calls)
    return start, end


def call_number(raw_phone):
    phone = clean_phone(raw_phone)
    if not phone:
        return False
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    client.calls.create(
        to=phone,
        from_=settings.TWILIO_PHONE_NUMBER,
        url=TRIAL_CALL_URL,
    )
    return True


def send_caregiver_email(dose, caregiver):
    medicine = dose.reminder.medicine
    owner = medicine.user
    when = timezone.localtime(dose.scheduled_for).strftime('%I:%M %p')
    send_mail(
        subject=f'Missed dose: {medicine.name}',
        message=(
            f'{owner.first_name or owner.get_username()} has not taken {medicine.name} '
            f'({medicine.dosage}) that was due at {when}.\n\n'
            'Please check on them.'
        ),
        from_email=None,
        recipient_list=[caregiver.email],
    )


def run_turn(dose, link, alert, now, total_calls):
    did = 0
    caregiver = link.caregiver

    if link.email_alerts and alert.emailed_at is None:
        if caregiver.email:
            try:
                send_caregiver_email(dose, caregiver)
            except Exception:
                logger.exception('Could not send caregiver email')
        alert.emailed_at = now
        did += 1

    if link.call_alerts:
        max_calls = min(link.max_calls, HARD_MAX_CALLS)
        spaced = alert.last_called_at is None or now >= (
            alert.last_called_at + timedelta(minutes=link.call_interval) - CALL_TOLERANCE
        )
        if alert.calls_made < max_calls and spaced and total_calls < HARD_TOTAL_CALLS:
            profile = getattr(caregiver, 'profile', None)
            try:
                call_number(profile.phone if profile else '')
            except Exception:
                logger.exception('Could not place caregiver call')
            alert.calls_made += 1
            alert.last_called_at = now
            did += 1

    alert.save()
    return did


@shared_task
def send_caregiver_alerts():
    now = timezone.now()
    doses = (
        DoseLog.objects.filter(
            status__in=['pending', 'missed'],
            scheduled_for__lte=now,
            scheduled_for__gt=now - ALERT_MAX_LATE,
            reminder__medicine__user__caregiver_links__isnull=False,
        )
        .distinct()
        .select_related('reminder__medicine__user')
    )

    actions = 0
    for dose in doses:
        owner = dose.reminder.medicine.user
        links = list(owner.caregiver_links.select_related('caregiver__profile'))
        alerts = {a.link_id: a for a in dose.caregiver_alerts.all()}
        if any(a.response for a in alerts.values()):
            continue  # a caregiver responded, so everything stops
        total_calls = dose.owner_calls + sum(a.calls_made for a in alerts.values())

        previous_end = None
        for link in links:
            start, end = link_turn(dose.scheduled_for, link, previous_end)
            previous_end = end
            if now < start:
                break      # not this caregiver's time yet, and later ones wait too
            if now >= end:
                continue   # this turn is over, so the next caregiver may be up
            alert = alerts.get(link.id)
            if alert is None:
                alert = CaregiverAlert.objects.create(dose=dose, link=link)
            actions += run_turn(dose, link, alert, now, total_calls)
            break          # only one caregiver at a time
    return f'Caregiver actions: {actions}'


@shared_task
def send_owner_reminders():
    now = timezone.now()
    candidates = DoseLog.objects.filter(
        status='pending',
        scheduled_for__lte=now,
        scheduled_for__gt=now - ALERT_MAX_LATE,
    ).select_related('reminder__medicine__user__profile')

    called = 0
    for dose in candidates:
        profile = getattr(dose.reminder.medicine.user, 'profile', None)
        remind = profile.remind_owner if profile else True
        interval = profile.owner_call_interval if profile else 5
        max_calls = min(profile.owner_max_calls if profile else 3, HARD_MAX_CALLS)
        missed_after = profile.missed_after_minutes if profile else 15

        if not remind:
            continue
        if now >= dose.scheduled_for + timedelta(minutes=missed_after):
            continue  # too late for reminders; the missed check takes over
        if dose.owner_calls >= max_calls:
            continue
        if dose.last_owner_call_at and now < (
            dose.last_owner_call_at + timedelta(minutes=interval) - CALL_TOLERANCE
        ):
            continue

        try:
            send_owner_call(dose)
        except Exception:
            logger.exception('Could not place owner reminder call')
        dose.owner_calls += 1
        dose.last_owner_call_at = now
        dose.save(update_fields=['owner_calls', 'last_owner_call_at'])
        called += 1
    return f'Called owners for {called} dose(s)'


@shared_task
def create_today_doses_logs():
    call_command('generate_doselogs')