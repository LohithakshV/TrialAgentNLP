import json
import os
import re
from .limits import limits, LimitError
from .evidence import record_evidence


async def gemini(client, instruction, data, schema):
    key = os.getenv('GEMINI_API_KEY', '').strip()
    if not key:
        raise ValueError('missing_key')
    model = os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite')
    if not re.fullmatch(r'[a-zA-Z0-9._-]+', model):
        raise ValueError('invalid_model')
    limits.reserve_gemini()
    response = await client.post(
        f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
        headers={'x-goog-api-key': key},
        json={'systemInstruction': {'parts': [{'text': instruction}]},
              'contents': [{'role': 'user', 'parts': [{'text': json.dumps(data)}]}],
              'generationConfig': {'responseMimeType': 'application/json', 'responseJsonSchema': schema}},
    )
    if response.status_code == 429:
        # Inspect quota identifiers internally; never echo provider payloads.
        details = str(response.json().get('error', {}).get('details', [])).lower()
        daily = 'perday' in details or 'per_day' in details or 'requestsperday' in details
        if daily:
            raise LimitError('provider_daily_limit', 'Google’s daily request quota has been reached. Please return after the daily reset.', limits.exhaust_provider())
        raise LimitError('provider_rate_limit', 'Google’s request or token limit was reached. Please wait a minute before trying again.', 60)
    response.raise_for_status()
    parts = response.json().get('candidates', [{}])[0].get('content', {}).get('parts', [])
    return json.loads(''.join(p.get('text', '') for p in parts if not p.get('thought')))


def registry_contacts(protocol, city):
    module = protocol.get('contactsLocationsModule', {})
    candidates = [(contact, 'Study contact') for contact in module.get('centralContacts', [])]
    locations = sorted(module.get('locations', []), key=lambda location: bool(city) and city.casefold() not in location.get('city', '').casefold())
    for location in locations:
        place = ', '.join(value for value in [location.get('city', ''), location.get('country', '')] if value)
        candidates.extend((contact, place or 'Study site') for contact in location.get('contacts', []))
    contacts, seen = [], set()
    for contact, location in candidates:
        details = {field: contact.get(field, '').strip()[:180] for field in ('name', 'role', 'email', 'phone') if isinstance(contact.get(field, ''), str)}
        key = (details.get('email') or details.get('phone') or details.get('name') or '').casefold()
        if not key or key in seen:
            continue
        seen.add(key)
        contacts.append({**details, 'location': location})
    return contacts[:6], len(contacts) > 6


async def retrieve(client, profile):
    params = {'format': 'json', 'query.cond': profile.condition, 'filter.overallStatus': 'RECRUITING', 'pageSize': 8}
    if profile.city:
        params['query.locn'] = profile.city
    response = await client.get('https://clinicaltrials.gov/api/v2/studies', params=params)
    response.raise_for_status()
    trials = []
    for study in response.json().get('studies', []):
        p = study.get('protocolSection', {})
        ident = p.get('identificationModule', {})
        nct = ident.get('nctId', '')
        if not re.fullmatch(r'NCT\d{8}', nct) or p.get('statusModule', {}).get('overallStatus') != 'RECRUITING':
            continue
        locations = p.get('contactsLocationsModule', {}).get('locations', [])
        cities = list(dict.fromkeys(l.get('city', '') for l in locations if l.get('city')))
        if profile.city:
            cities.sort(key=lambda c: profile.city.casefold() not in c.casefold())
        eligibility = p.get('eligibilityModule', {})
        minimum = eligibility.get('minimumAge', '')
        maximum = eligibility.get('maximumAge', '')
        minimum = '' if minimum == 'N/A' else minimum
        maximum = '' if maximum == 'N/A' else maximum
        age_range = f'{minimum} to {maximum}' if minimum and maximum else f'{minimum} and older' if minimum else f'Up to {maximum}' if maximum else 'Not provided'
        contacts, contacts_truncated = registry_contacts(p, profile.city)
        trial = dict(id=nct, title=ident.get('briefTitle', 'Untitled registry record'),
            phase=', '.join(p.get('designModule', {}).get('phases', [])).replace('PHASE', 'Phase ') or 'Phase not specified',
            location=', '.join(cities[:3]) + (f' + {len(cities)-3} more' if len(cities) > 3 else '') or 'See registry for sites',
            siteCities=cities,
            conditions=p.get('conditionsModule', {}).get('conditions', []),
            interventions=list(dict.fromkeys(item['name'] for item in p.get('armsInterventionsModule', {}).get('interventions', []) if item.get('name'))),
            sponsor=p.get('sponsorCollaboratorsModule', {}).get('leadSponsor', {}).get('name', ''),
            studyType=p.get('designModule', {}).get('studyType', ''),
            ageRange=age_range, sex=eligibility.get('sex', ''),
            contacts=contacts, contactsTruncated=contacts_truncated,
            eligibility=eligibility.get('eligibilityCriteria', '')[:14000],
            description=p.get('descriptionModule', {}).get('briefSummary', '')[:4000],
            updated=p.get('statusModule', {}).get('lastUpdatePostDateStruct', {}).get('date', 'Not provided'),
            url=f'https://clinicaltrials.gov/study/{nct}',
            apiUrl=f'https://clinicaltrials.gov/api/v2/studies/{nct}')
        trial['evidence'] = record_evidence(profile, trial)
        trials.append(trial)
    return trials
