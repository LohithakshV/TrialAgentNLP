"""Literal source overlap, never a clinical eligibility assessment."""
import re


def locate(value, text):
    tokens = re.findall(r'\w+', value)
    if not tokens or not text:
        return ''
    pattern = r'(?<!\w)' + r'[\W_]+'.join(re.escape(token) for token in tokens) + r'(?!\w)'
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return ''
    start, end = max(0, match.start() - 100), min(len(text), match.end() + 160)
    return ('…' if start else '') + re.sub(r'\s+', ' ', text[start:end]).strip() + ('…' if end < len(text) else '')


def record_evidence(profile, trial):
    condition_sources = [
        ('Listed conditions', ', '.join(trial['conditions'])),
        ('Registry overview', trial['description']),
        ('Published eligibility text', trial['eligibility']),
    ]
    criteria_sources = [
        ('Published eligibility text', trial['eligibility']),
        ('Registry overview', trial['description']),
    ]
    checks = [
        ('condition', 'Condition', profile.condition, condition_sources),
        ('stage', 'Stage', profile.stage, criteria_sources),
        *[('biomarker', 'Biomarker', value, criteria_sources) for value in profile.biomarkers],
        ('city', 'City', profile.city, [('Listed site cities', ', '.join(trial['siteCities']))]),
    ]
    if not profile.biomarkers:
        checks.insert(2, ('biomarker', 'Biomarkers', '', criteria_sources))
    items = []
    for field, label, value, sources in checks:
        item = {'field': field, 'label': label, 'value': value, 'status': 'not_provided' if not value else 'not_located', 'source': '', 'excerpt': ''}
        if value:
            for source, text in sources:
                excerpt = locate(value, text)
                if excerpt:
                    # A term in eligibility text can be an exclusion. Never mark it met.
                    item.update(status='listed' if source in ('Listed conditions', 'Listed site cities') else 'wording_to_review', source=source, excerpt=excerpt)
                    break
        items.append(item)
    return {
        'provided': sum(bool(item['value']) for item in items),
        'mentioned': sum(item['status'] in ('listed', 'wording_to_review') for item in items),
        'meaning': 'Literal mentions of supplied details in this record. This is not an eligibility score; exclusions can mention the same terms.',
        'items': items,
    }
