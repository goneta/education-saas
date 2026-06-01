import re
from typing import Optional


COUNTRY_PROFILES = {
    "CI": {
        "name": "Cote d'Ivoire",
        "currency": "FCFA",
        "currency_code": "XOF",
        "locale": "fr",
        "timezone": "Africa/Abidjan",
        "date_format": "dd/MM/yyyy",
        "time_format": "HH:mm",
        "phone_code": "+225",
        "phone_lengths": [10],
        "region": "africa",
    },
    "SN": {"name": "Senegal", "currency": "FCFA", "currency_code": "XOF", "locale": "fr", "timezone": "Africa/Dakar", "date_format": "dd/MM/yyyy", "time_format": "HH:mm", "phone_code": "+221", "phone_lengths": [9], "region": "africa"},
    "ML": {"name": "Mali", "currency": "FCFA", "currency_code": "XOF", "locale": "fr", "timezone": "Africa/Bamako", "date_format": "dd/MM/yyyy", "time_format": "HH:mm", "phone_code": "+223", "phone_lengths": [8], "region": "africa"},
    "BF": {"name": "Burkina Faso", "currency": "FCFA", "currency_code": "XOF", "locale": "fr", "timezone": "Africa/Ouagadougou", "date_format": "dd/MM/yyyy", "time_format": "HH:mm", "phone_code": "+226", "phone_lengths": [8], "region": "africa"},
    "CM": {"name": "Cameroon", "currency": "FCFA", "currency_code": "XAF", "locale": "fr", "timezone": "Africa/Douala", "date_format": "dd/MM/yyyy", "time_format": "HH:mm", "phone_code": "+237", "phone_lengths": [9], "region": "africa"},
    "KE": {"name": "Kenya", "currency": "USD", "currency_code": "USD", "locale": "sw", "timezone": "Africa/Nairobi", "date_format": "dd/MM/yyyy", "time_format": "HH:mm", "phone_code": "+254", "phone_lengths": [9], "region": "africa"},
    "TZ": {"name": "Tanzania", "currency": "USD", "currency_code": "USD", "locale": "sw", "timezone": "Africa/Dar_es_Salaam", "date_format": "dd/MM/yyyy", "time_format": "HH:mm", "phone_code": "+255", "phone_lengths": [9], "region": "africa"},
    "GB": {"name": "United Kingdom", "currency": "GBP", "currency_code": "GBP", "locale": "en", "timezone": "Europe/London", "date_format": "dd/MM/yyyy", "time_format": "HH:mm", "phone_code": "+44", "phone_lengths": [10], "region": "europe"},
    "FR": {"name": "France", "currency": "EUR", "currency_code": "EUR", "locale": "fr", "timezone": "Europe/Paris", "date_format": "dd/MM/yyyy", "time_format": "HH:mm", "phone_code": "+33", "phone_lengths": [9], "region": "europe"},
    "ES": {"name": "Spain", "currency": "EUR", "currency_code": "EUR", "locale": "es", "timezone": "Europe/Madrid", "date_format": "dd/MM/yyyy", "time_format": "HH:mm", "phone_code": "+34", "phone_lengths": [9], "region": "europe"},
    "DE": {"name": "Germany", "currency": "EUR", "currency_code": "EUR", "locale": "en", "timezone": "Europe/Berlin", "date_format": "dd.MM.yyyy", "time_format": "HH:mm", "phone_code": "+49", "phone_lengths": [10, 11], "region": "europe"},
    "IT": {"name": "Italy", "currency": "EUR", "currency_code": "EUR", "locale": "en", "timezone": "Europe/Rome", "date_format": "dd/MM/yyyy", "time_format": "HH:mm", "phone_code": "+39", "phone_lengths": [9, 10], "region": "europe"},
    "US": {"name": "United States", "currency": "USD", "currency_code": "USD", "locale": "en", "timezone": "America/New_York", "date_format": "MM/dd/yyyy", "time_format": "hh:mm a", "phone_code": "+1", "phone_lengths": [10], "region": "america"},
}

SUPPORTED_CURRENCIES = {"FCFA", "GBP", "EUR", "USD"}
SUPPORTED_LOCALES = {"fr", "en", "es", "sw"}


def country_profile(country_code: Optional[str]) -> dict:
    code = (country_code or "CI").upper()
    profile = COUNTRY_PROFILES.get(code, COUNTRY_PROFILES["CI"]).copy()
    profile["country_code"] = code if code in COUNTRY_PROFILES else "CI"
    return profile


def format_address(address: Optional[dict]) -> Optional[str]:
    if not address:
        return None
    parts = [
        address.get("street"),
        address.get("district"),
        address.get("city"),
        address.get("region"),
        address.get("postal_code"),
        address.get("country"),
    ]
    return ", ".join(str(part).strip() for part in parts if part)


def normalize_phone(raw_number: Optional[str], country_code: Optional[str]) -> Optional[str]:
    if not raw_number:
        return None
    profile = country_profile(country_code)
    phone_code = profile["phone_code"]
    value = raw_number.strip()
    if value.startswith("+"):
        digits = re.sub(r"\D", "", value)
        return f"+{digits}" if digits else None
    digits = re.sub(r"\D", "", value)
    if digits.startswith("00"):
        return f"+{digits[2:]}"
    if digits.startswith("0"):
        digits = digits[1:]
    prefix = phone_code.replace("+", "")
    if digits.startswith(prefix):
        return f"+{digits}"
    return f"{phone_code}{digits}"


def validate_phone(raw_number: Optional[str], country_code: Optional[str]) -> tuple[bool, Optional[str], Optional[str]]:
    e164 = normalize_phone(raw_number, country_code)
    if not e164:
        return True, None, None
    profile = country_profile(country_code)
    prefix = profile["phone_code"]
    if not e164.startswith(prefix):
        return False, e164, f"Phone number must use country code {prefix}"
    national = e164[len(prefix):]
    if profile.get("phone_lengths") and len(national) not in profile["phone_lengths"]:
        expected = "/".join(str(length) for length in profile["phone_lengths"])
        return False, e164, f"Phone number for {profile['name']} must contain {expected} digits after {prefix}"
    return True, e164, None


def localized_school_type_profile(school_type: str, country_code: Optional[str]) -> dict:
    profile = country_profile(country_code)
    regional_rules = {
        "africa": {
            "primary": ["cycle primaire", "pieces d'inscription", "extrait de naissance"],
            "secondary": ["college/lycee", "bulletins", "examens nationaux"],
            "technical": ["ateliers", "stages", "equipements"],
            "vocational": ["competences metier", "stages", "certifications"],
            "professional": ["competences metier", "stages", "certifications"],
            "university": ["LMD", "credits", "releves certifies"],
        },
        "europe": {
            "primary": ["safeguarding", "attendance", "parental consent"],
            "secondary": ["GCSE/A-level or national equivalents", "attendance", "assessment"],
            "technical": ["apprenticeships", "work placements", "competency tracking"],
            "vocational": ["apprenticeships", "work placements", "competency tracking"],
            "professional": ["apprenticeships", "work placements", "competency tracking"],
            "university": ["ECTS", "GPA", "certified transcripts"],
        },
    }
    return {
        "school_type": school_type,
        "country": profile,
        "administrative_focus": regional_rules.get(profile["region"], regional_rules["africa"]).get(school_type, []),
    }
