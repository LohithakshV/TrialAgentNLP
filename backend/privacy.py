import re


def redact_identifiers(text):
    """Best effort only; cannot anonymize medical records."""
    text = re.sub(r'(?im)\b(?:patient(?: name)?|name|dob|date of birth|mrn|medical record(?: number)?|address|phone|email)\s*[:=][^;\n]*', '[identifier removed]', text)
    text = re.sub(r'\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b', '[email removed]', text)
    text = re.sub(r'(?<!\d)(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}(?!\d)', '[phone removed]', text)
    return re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[identifier removed]', text)


def clean_profile(profile):
    return type(profile)(condition=redact_identifiers(profile.condition), stage=redact_identifiers(profile.stage),
        biomarkers=[redact_identifiers(b)[:180] for b in profile.biomarkers], city=redact_identifiers(profile.city))
