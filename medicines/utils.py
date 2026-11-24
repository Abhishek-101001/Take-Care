import re


def clean_phone(raw, default_country_code='+91'):
    """Turn a phone number into Twilio's +<country><number> format.

    Returns None if the number can't be fixed.
    """
    if not raw:
        return None

    raw = raw.strip()
    digits = re.sub(r'\D', '', raw)   # keep only the digits

    if raw.startswith('+'):
        number = '+' + digits         # already has a country code
    else:
        digits = digits.lstrip('0')   # drop leading zeros, like 09793123011
        if len(digits) == 12 and digits.startswith('91'):
            number = '+' + digits     # 919793123011 already has the 91
        elif len(digits) == 10:
            number = default_country_code + digits
        else:
            return None

    if not re.fullmatch(r'\+\d{8,15}', number):
        return None
    return number