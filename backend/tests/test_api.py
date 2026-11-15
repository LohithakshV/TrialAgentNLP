import unittest
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient
from backend.main import app
from backend.models import AuditResponse, Criterion, Profile, PreparedQuery, TrialEvaluation
from backend.providers import retrieve
from backend.research import prepare, search
from backend.limits import RequestLimits

PROFILE = dict(condition='Lung cancer', stage='IIIA', biomarkers=['EGFR'], city='Atlanta')
GUIDE = [{'title': f'Question {i}', 'question': 'What should the study team confirm?'} for i in range(5)]


def audit(score=82, nct='NCT12345678'):
    return AuditResponse(
        evaluations=[TrialEvaluation(
            nctId=nct, matchScore=score, tier='strong', summary='Aligned on condition.',
            criteria=[Criterion(label='Condition', state='met', reason='Listed in the registry.')],
            strengths=['Condition matches'], gaps=[], unknowns=[],
        )],
        guide=GUIDE,
    )


class Routes(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.env = patch.dict('os.environ', {'GEMINI_API_KEY': 'fake-test-key'})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.limiter = patch('backend.main.limits', RequestLimits())
        self.limiter.start()
        self.addCleanup(self.limiter.stop)
        self.payload = dict(profile=PROFILE, consent=True)

    def test_search_requires_consent_before_provider_calls(self):
        with patch('backend.main.search') as registry, patch('backend.main.prepare', new_callable=AsyncMock) as model:
            self.assertEqual(self.client.post('/api/search', json={**self.payload, 'consent': False}).status_code, 400)
            self.assertEqual(self.client.post('/api/extract', json={'note':'Fictional research question', 'consent':False}).status_code, 400)
        registry.assert_not_called()
        model.assert_not_called()

    def test_invalid_input_not_echoed(self):
        response = self.client.post('/api/extract', json={'note': 'SECRET', 'extra': 'SECRET'})
        self.assertEqual(response.status_code, 400)
        self.assertNotIn('SECRET', response.text)

    def test_extraction_success_and_no_store(self):
        with patch('backend.main.prepare', new=AsyncMock(return_value=PreparedQuery(status='ready',profile=PROFILE))) as model:
            response = self.client.post('/api/extract', json={'note': 'A fictional query about lung cancer around Atlanta', 'consent':True})
        self.assertEqual(response.json()['profile'], PROFILE)
        self.assertNotIn('guide', response.json())
        self.assertEqual(response.headers['cache-control'], 'no-store')
        self.assertEqual(model.await_count, 1)

    def test_missing_key_returns_service_error(self):
        with patch.dict('os.environ', {'GEMINI_API_KEY': ''}):
            response = self.client.post('/api/extract', json={'note':'A fictional query about lung cancer', 'consent':True})
        self.assertEqual(response.status_code, 503)

    def test_short_condition_name_is_a_valid_prompt(self):
        with patch('backend.main.prepare', new=AsyncMock(return_value=PreparedQuery(status='ready',profile={**PROFILE,'condition':'Asthma'}))):
            response = self.client.post('/api/extract', json={'note':'asthma','consent':True})
        self.assertEqual(response.status_code, 200)

    def test_foreign_origin_rejected(self):
        response = self.client.post('/api/search', json=self.payload, headers={'Origin': 'https://example.com'})
        self.assertEqual(response.status_code, 403)

    def test_same_host_origin_is_allowed(self):
        async def pipeline(profile):
            yield 'result', {'trials': [], 'profile': profile.model_dump()}
        with patch('backend.main.search', new=pipeline):
            response = self.client.post('/api/search', json=self.payload, headers={'Origin': 'http://testserver'})
        self.assertNotEqual(response.status_code, 403)

    def test_large_body_rejected(self):
        self.assertEqual(self.client.post('/api/extract', content='x' * 30001).status_code, 413)

    def test_legacy_sample_route_removed(self):
        self.assertEqual(self.client.post('/api/match', json={'mode': 'demo'}).status_code, 404)

    def test_confirmed_edited_profile_used_without_reextracting(self):
        async def pipeline(profile):
            self.assertEqual(profile.condition, 'Prostate cancer')
            self.assertEqual(profile.city, 'Seattle')
            yield 'result', {'trials': [], 'profile': profile.model_dump()}
        with patch('backend.main.search', new=pipeline):
            response = self.client.post('/api/search', json={'profile': {**PROFILE, 'condition': 'Prostate cancer', 'city': 'Seattle'}, 'consent': True})
        self.assertIn('event: result', response.text)

    def test_model_failure_keeps_provider_payload_out_of_errors(self):
        with patch('backend.main.prepare', new=AsyncMock(side_effect=ValueError('SECRET provider error'))):
            response = self.client.post('/api/extract', json={'note':'A fictional query about lung cancer', 'consent':True})
        self.assertEqual(response.status_code, 502)
        self.assertNotIn('SECRET', response.text)

    def test_search_error_is_generic_sse(self):
        async def fail(profile):
            yield 'progress', {'step': 0}
            raise ValueError('SECRET')
        with patch('backend.main.search', new=fail):
            response = self.client.post('/api/search', json=self.payload)
        self.assertIn('event: error', response.text)
        self.assertNotIn('SECRET', response.text)

    def test_daily_limit_returns_machine_code_and_retry_header(self):
        limiter = RequestLimits(daily=1)
        limiter.reserve_gemini()
        with patch('backend.main.limits', limiter), patch('backend.main.prepare', new_callable=AsyncMock) as model:
            response = self.client.post('/api/extract', json={'note':'A fictional research query', 'consent':True})
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()['code'], 'daily_limit')
        self.assertIn('Retry-After', response.headers)
        model.assert_not_called()

    def test_registry_can_complete_after_last_model_request_of_day(self):
        limiter = RequestLimits(daily=1)
        limiter.reserve_gemini()
        async def pipeline(profile):
            yield 'result', {'trials':[],'profile':profile.model_dump()}
        with patch('backend.main.limits', limiter), patch('backend.main.search', new=pipeline):
            response = self.client.post('/api/search', json=self.payload)
        self.assertIn('event: result', response.text)


class Pipeline(unittest.IsolatedAsyncioTestCase):
    async def test_registry_query_minimization_and_source_validation(self):
        seen = []
        def handler(request):
            seen.append(request)
            return httpx.Response(200, json={'studies': [
                {'protocolSection': {'identificationModule': {'nctId': 'NCT12345678'}, 'statusModule': {'overallStatus': 'RECRUITING'}}},
                {'protocolSection': {'identificationModule': {'nctId': 'javascript:bad'}, 'statusModule': {'overallStatus': 'RECRUITING'}}},
                {'protocolSection': {'identificationModule': {'nctId': 'NCT87654321'}, 'statusModule': {'overallStatus': 'COMPLETED'}}},
            ]})
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            trials = await retrieve(client, Profile(**{**PROFILE, 'stage': 'SECRET_STAGE', 'biomarkers': ['SECRET_MARKER']}))
        self.assertEqual(len(trials), 1)
        self.assertEqual(trials[0]['url'], 'https://clinicaltrials.gov/study/NCT12345678')
        self.assertNotIn('SECRET', str(seen[0].url))

    async def test_registry_records_are_audited_by_one_batched_model_call(self):
        trials = [dict(id='NCT12345678', title='Registry record', eligibility='criteria', description='Manual review needed')]
        with patch('backend.research.evaluate', new=AsyncMock(return_value=audit())) as model, patch('backend.research.retrieve', new=AsyncMock(return_value=trials)):
            events = [item async for item in search(Profile(**PROFILE))]
        result = events[-1][1]
        self.assertEqual(result['trials'][0]['matchScore'], 82)
        self.assertEqual(result['trials'][0]['matchTier'], 'strong')
        self.assertEqual(result['guideOrigin'], 'ai')
        self.assertEqual(len(result['guide']), 5)
        self.assertFalse(result['partial'])
        model.assert_awaited_once()

    async def test_audit_failure_keeps_registry_records_with_standard_guide(self):
        trials = [dict(id='NCT12345678', title='Registry record', eligibility='criteria', description='Manual review needed')]
        with patch('backend.research.evaluate', new=AsyncMock(side_effect=ValueError('SECRET'))), patch('backend.research.retrieve', new=AsyncMock(return_value=trials)):
            events = [item async for item in search(Profile(**PROFILE))]
        result = events[-1][1]
        self.assertTrue(result['partial'])
        self.assertIsNone(result['trials'][0]['matchScore'])
        self.assertEqual(result['guideOrigin'], 'standard')
        self.assertEqual(len(result['guide']), 5)
        self.assertNotIn('SECRET', str(result))

    async def test_empty_results_do_not_invoke_the_audit(self):
        with patch('backend.research.evaluate', new_callable=AsyncMock) as model, patch('backend.research.retrieve', new=AsyncMock(return_value=[])):
            events = [item async for item in search(Profile(**PROFILE))]
        self.assertEqual(events[-1][1]['trials'], [])
        model.assert_not_called()

    async def test_two_model_calls_prepare_then_audit(self):
        trials = [dict(id='NCT12345678',title='Real source record', description='From registry')]
        generated = {'status': 'ready', 'profile': PROFILE}
        audit_result = {
            'evaluations': [{'nctId': 'NCT12345678', 'matchScore': 74, 'tier': 'potential', 'summary': 'Partly aligned.', 'criteria': [], 'strengths': [], 'gaps': [], 'unknowns': []}],
            'guide': GUIDE,
        }
        with patch('backend.research.gemini', new=AsyncMock(return_value=generated)) as probe, patch('backend.evaluation.gemini', new=AsyncMock(return_value=audit_result)) as audit_model, patch('backend.research.retrieve', new=AsyncMock(return_value=trials)):
            prepared = await prepare('Fictional research: lung cancer IIIA EGFR around Atlanta')
            events = [item async for item in search(Profile(**prepared.profile.model_dump()))]
        self.assertEqual(probe.await_count, 1)
        self.assertEqual(audit_model.await_count, 1)
        self.assertEqual(prepared.profile.condition,'Lung cancer')
        self.assertEqual(events[-1][1]['trials'][0]['description'],'From registry')
        self.assertEqual(events[-1][1]['trials'][0]['matchScore'], 74)
        self.assertEqual(len(events[-1][1]['guide']), 5)
