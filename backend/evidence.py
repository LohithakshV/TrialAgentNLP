"""Literal source overlap, never a clinical eligibility assessment."""
import re


MAX_MANUAL_CRITERIA = 10
MAX_MANUAL_LABEL = 200
MAX_MANUAL_REASON = 400
MAX_MANUAL_VALUE = 120
MAX_PROFILE_BIOMARKERS = 3
MAX_INCLUSION_ITEMS = 4
MAX_EXCLUSION_ITEMS = 2

INCLUSION_HEADER = re.compile(r'\binclusion\s+criteria\b', re.I)
EXCLUSION_HEADER = re.compile(r'\bexclusion\s+criteria\b', re.I)
BULLET = re.compile(r'^\s*(?:\d+\s*[.)]|[A-Za-z]\s*[.)]|[*\-•·])\s*(.+)$')


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


def _clean(value, limit):
    return ' '.join(str(value).split())[:limit].strip()


def _profile_value(profile, field):
    if isinstance(profile, dict):
        return profile.get(field, '')
    return getattr(profile, field, '')


def _header(line):
    if INCLUSION_HEADER.search(line):
        return 'inclusion'
    if EXCLUSION_HEADER.search(line):
        return 'exclusion'
    return ''


def eligibility_items(text):
    """Split published criteria into cleaned inclusion and exclusion requirements."""
    if not isinstance(text, str) or not text.strip():
        return []
    items, current, section = [], None, ''

    def flush():
        nonlocal current
        if current and len(current['text']) >= 8:
            items.append(current)
        current = None

    for raw_line in re.split(r'\r?\n', text):
        line = raw_line.strip()
        if not line:
            continue
        header = _header(line)
        if header:
            flush()
            section = header
            remainder = line.split(':', 1)[1].strip() if ':' in line else ''
            if remainder:
                bullet = BULLET.match(remainder)
                current = {'text': _clean(bullet.group(1) if bullet else remainder, MAX_MANUAL_LABEL), 'section': section}
            continue
        bullet = BULLET.match(line)
        if bullet:
            flush()
            current = {'text': _clean(bullet.group(1), MAX_MANUAL_LABEL), 'section': section or 'inclusion'}
            continue
        if current and len(current['text']) < MAX_MANUAL_LABEL:
            current['text'] = _clean(f"{current['text']} {line}", MAX_MANUAL_LABEL)
    flush()

    seen, cleaned = set(), []
    for item in items:
        key = item['text'].casefold()
        if not key or key in seen:
            continue
        seen.add(key)
        cleaned.append(item)
    return cleaned


def _section_text(items, section):
    return '\n'.join(item['text'] for item in items if item['section'] == section)


def manual_review(profile, trial):
    """Deterministic checklist for when no model score is available.

    Green means a supplied detail has literal support in the registry text. It is
    never a clinical eligibility decision.
    """
    condition = _clean(_profile_value(profile, 'condition'), MAX_MANUAL_VALUE)
    stage = _clean(_profile_value(profile, 'stage'), MAX_MANUAL_VALUE)
    biomarkers = [_clean(value, MAX_MANUAL_VALUE) for value in (_profile_value(profile, 'biomarkers') or []) if value]
    eligibility = trial.get('eligibility', '') or ''
    items = eligibility_items(eligibility)
    inclusion = _section_text(items, 'inclusion')
    exclusion = _section_text(items, 'exclusion')
    conditions = ', '.join(trial.get('conditions') or [])
    criteria, seen = [], set()

    def add(label, state, reason):
        label, reason = _clean(label, MAX_MANUAL_LABEL), _clean(reason, MAX_MANUAL_REASON)
        key = label.casefold()
        if not label or key in seen or len(criteria) >= MAX_MANUAL_CRITERIA:
            return False
        seen.add(key)
        criteria.append({'label': label, 'state': state, 'reason': reason})
        return True

    if condition:
        if locate(condition, conditions):
            add(f'Condition: {condition}', 'met', 'Listed in the trial conditions.')
        elif locate(condition, eligibility) or locate(condition, trial.get('description', '')):
            add(f'Condition: {condition}', 'unknown', 'Condition wording appears in the record; confirm the exact study population.')
        else:
            add(f'Condition: {condition}', 'unknown', 'Not found in the listed conditions; confirm with the study team.')

    if stage:
        if locate(stage, inclusion) and not locate(stage, exclusion):
            add(f'Stage: {stage}', 'met', 'Mentioned in the inclusion criteria; confirm the exact stage requirement.')
        elif locate(stage, exclusion):
            add(f'Stage: {stage}', 'unknown', 'Stage wording appears in the exclusion criteria; confirm whether it applies.')
        else:
            add(f'Stage: {stage}', 'unknown', 'Stage was not located in the published criteria; confirm the requirement.')

    for biomarker in biomarkers[:MAX_PROFILE_BIOMARKERS]:
        if locate(biomarker, inclusion) and not locate(biomarker, exclusion):
            add(f'Biomarker: {biomarker}', 'met', 'Mentioned in the inclusion criteria; confirm the exact test and result.')
        elif locate(biomarker, exclusion):
            add(f'Biomarker: {biomarker}', 'unknown', 'Biomarker wording appears in the exclusion criteria; confirm whether it applies.')
        else:
            add(f'Biomarker: {biomarker}', 'unknown', 'Biomarker was not located in the published criteria; confirm the requirement.')

    age_range = _clean(trial.get('ageRange', ''), MAX_MANUAL_VALUE)
    if age_range and age_range.casefold() != 'not provided':
        add(f'Age range: {age_range}', 'unknown', 'Your age was not supplied; confirm this requirement.')

    sex = str(trial.get('sex', '') or '').upper()
    if sex == 'ALL':
        add('Sex: All', 'met', 'The registry lists all sexes for this study.')
    elif sex in {'FEMALE', 'MALE'}:
        add(f'Sex: {sex.title()}', 'unknown', 'Your sex was not supplied; confirm this requirement.')

    exclusion_added = 0
    for item in items:
        if exclusion_added >= MAX_EXCLUSION_ITEMS:
            break
        if item['section'] == 'exclusion' and add(f"Exclusion: {item['text']}", 'unknown', 'This exclusion may apply; confirm with the study team.'):
            exclusion_added += 1

    inclusion_added = 0
    for item in items:
        if inclusion_added >= MAX_INCLUSION_ITEMS:
            break
        if item['section'] == 'inclusion' and add(item['text'], 'unknown', 'Read the full registry criterion and confirm with the study team.'):
            inclusion_added += 1

    if not items:
        add('Full inclusion and exclusion criteria', 'unknown', 'No structured criteria were available; confirm every requirement with the study team.')

    return {
        'summary': 'Manual review from the details you supplied and the registry text. Green items are supported by your details; orange items need confirmation with the study team.',
        'criteria': criteria,
    }
