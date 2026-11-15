import unittest
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from backend.main import app
from backend.limits import RequestLimits
from backend.models import Profile
from backend.providers import retrieve
from backend.research import prepare


PROFILE = dict(condition='Asthma', stage='', biomarkers=[], city='Boston')


class RelevanceRoutes(unittest.TestCase):
    def test_unrelated_and_incomplete_prompts_return_actionable_422_without_registry(self):
        for status, note in [('off_topic', 'Write me a poem about pizza.'), ('needs_details', 'What does randomized mean in clinical trials?')]:
            with self.subTest(status=status), patch.dict('os.environ', {'GEMINI_API_KEY': 'fake-test-key'}), patch('backend.main.limits', RequestLimits()), patch('backend.research.gemini', new=AsyncMock(return_value={'status': status, 'profile': PROFILE})) as model, patch('backend.research.retrieve', new_callable=AsyncMock) as registry:
                response = TestClient(app).post('/api/extract', json={'note': note, 'consent': True})
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json()['code'], status)
                self.assertIn('condition', response.json()['error'])
                self.assertNotIn('profile', response.json())
                self.assertEqual(response.headers['cache-control'], 'no-store')
                self.assertEqual(model.await_count, 1)
                registry.assert_not_called()


class Preparation(unittest.IsolatedAsyncioTestCase):
    async def test_ready_condition_returns_a_reviewed_profile_in_one_classified_response(self):
        with patch('backend.research.gemini', new=AsyncMock(return_value={'status': 'ready', 'profile': PROFILE})) as model:
            result = await prepare('Fictional asthma research near Boston')
        self.assertEqual(result.status, 'ready')
        self.assertEqual(result.profile.condition, 'Asthma')
        self.assertEqual(model.await_count, 1)

    async def test_non_ready_result_cannot_keep_a_model_invented_profile(self):
        with patch('backend.research.gemini', new=AsyncMock(return_value={'status': 'off_topic', 'profile': PROFILE})):
            result = await prepare('Write a poem')
        self.assertEqual(result.status, 'off_topic')
        self.assertEqual(result.profile.condition, '')

    async def test_ready_without_a_condition_is_downgraded_to_needs_details(self):
        with patch('backend.research.gemini', new=AsyncMock(return_value={'status': 'ready', 'profile': {**PROFILE, 'condition': ''}})):
            result = await prepare('Find studies')
        self.assertEqual(result.status, 'needs_details')

    async def test_missing_or_unknown_classification_fails_closed(self):
        for status in [None, 'probably_ready']:
            value = {'profile': PROFILE}
            if status is not None:
                value['status'] = status
            with self.subTest(status=status), patch('backend.research.gemini', new=AsyncMock(return_value=value)):
                with self.assertRaises(ValueError):
                    await prepare('Fictional asthma studies')


class RegistryFacts(unittest.IsolatedAsyncioTestCase):
    async def test_public_contacts_and_source_json_are_available_when_the_website_fails(self):
        protocol = {
            'identificationModule': {'nctId': 'NCT07554313', 'briefTitle': 'Registry record'},
            'statusModule': {'overallStatus': 'RECRUITING'},
            'contactsLocationsModule': {
                'centralContacts': [{'name': 'Study desk', 'role': 'CONTACT', 'email': 'desk@example.org', 'phone': '+1 555 010 0100'}],
                'locations': [{'city': 'Boston', 'contacts': [{'name': 'Site desk', 'role': 'CONTACT', 'email': 'site@example.org'}]}],
            },
        }
        def handler(request):
            return httpx.Response(200, json={'studies': [{'protocolSection': protocol}]})
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            result = (await retrieve(client, Profile(**PROFILE)))[0]
        self.assertEqual(result['apiUrl'], 'https://clinicaltrials.gov/api/v2/studies/NCT07554313')
        self.assertEqual(result['contacts'][0]['name'], 'Study desk')
        self.assertEqual(result['contacts'][0]['email'], 'desk@example.org')
        self.assertEqual(result['contacts'][1]['location'], 'Boston')
        self.assertFalse(result['contactsTruncated'])

    async def test_facts_and_evidence_checklist_are_source_based_not_match_scores(self):
        protocol = {
            'identificationModule': {'nctId': 'NCT12345678', 'briefTitle': 'A registry study'},
            'statusModule': {'overallStatus': 'RECRUITING', 'lastUpdatePostDateStruct': {'date': '2026-11-01'}},
            'conditionsModule': {'conditions': ['Asthma']},
            'armsInterventionsModule': {'interventions': [{'type': 'DRUG', 'name': 'Investigational treatment'}]},
            'sponsorCollaboratorsModule': {'leadSponsor': {'name': 'Example research institution'}},
            'designModule': {'studyType': 'INTERVENTIONAL', 'phases': ['PHASE2']},
            'eligibilityModule': {'eligibilityCriteria': 'Exclusion: uncontrolled asthma', 'minimumAge': '18 Years', 'maximumAge': '65 Years', 'sex': 'ALL'},
        }
        def handler(request):
            return httpx.Response(200, json={'studies': [{'protocolSection': protocol}]})
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            result = (await retrieve(client, Profile(**PROFILE)))[0]
        self.assertEqual(result['conditions'], ['Asthma'])
        self.assertEqual(result['interventions'], ['Investigational treatment'])
        self.assertEqual(result['sponsor'], 'Example research institution')
        self.assertEqual(result['studyType'], 'INTERVENTIONAL')
        self.assertEqual(result['ageRange'], '18 Years to 65 Years')
        self.assertEqual(result['sex'], 'ALL')
        self.assertNotIn('score', result)
        self.assertNotIn('eligible', result)
        self.assertEqual(result['eligibility'], 'Exclusion: uncontrolled asthma')
        self.assertEqual(result['url'], 'https://clinicaltrials.gov/study/NCT12345678')

    async def test_exclusion_wording_is_evidence_to_review_not_a_met_requirement(self):
        protocol = {
            'identificationModule': {'nctId': 'NCT12345678'},
            'statusModule': {'overallStatus': 'RECRUITING'},
            'conditionsModule': {'conditions': ['Lung cancer']},
            'eligibilityModule': {'eligibilityCriteria': 'Exclusion criteria: EGFR exon 19 deletion is excluded.'},
            'contactsLocationsModule': {'locations': [{'city': 'Boston'}]},
        }
        def handler(request):
            return httpx.Response(200, json={'studies': [{'protocolSection': protocol}]})
        profile = Profile(condition='Lung cancer', stage='IIIA', biomarkers=['EGFR exon 19 deletion'], city='Boston')
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            result = (await retrieve(client, profile))[0]
        evidence = result['evidence']
        self.assertEqual(evidence['provided'], 4)
        self.assertEqual(evidence['mentioned'], 3)
        marker = next(item for item in evidence['items'] if item['field'] == 'biomarker')
        self.assertEqual(marker['status'], 'wording_to_review')
        self.assertIn('excluded', marker['excerpt'])
        self.assertEqual(next(item for item in evidence['items'] if item['field'] == 'stage')['status'], 'not_located')
        self.assertNotIn('eligible', json_string(result))


def json_string(value):
    import json
    return json.dumps(value).lower()
