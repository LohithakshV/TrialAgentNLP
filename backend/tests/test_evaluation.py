import unittest
from unittest.mock import AsyncMock, patch

from backend.evaluation import evaluate, normalize
from backend.models import AuditResponse, Criterion, Profile, Question, TrialEvaluation


PROFILE = Profile(condition='Lung cancer', stage='IIIA', biomarkers=['EGFR'], city='Atlanta')


def evaluation(nct, score, tier='strong'):
    return TrialEvaluation(nctId=nct, matchScore=score, tier=tier, summary='Registry text reviewed.',
        criteria=[Criterion(label='Condition', state='met', reason='Listed.')],
        strengths=['Condition matches'], gaps=[], unknowns=[])


class Evaluation(unittest.IsolatedAsyncioTestCase):
    def test_normalization_filters_unknown_and_duplicate_ids_and_recomputes_tiers(self):
        audit = AuditResponse(
            evaluations=[evaluation('NCT12345678', 55), evaluation('NCT12345678', 90), evaluation('NCT99999999', 70)],
            guide=[Question(title='Q', question='Ask?')] * 5,
        )
        result = normalize(audit, [{'id': 'NCT12345678'}])
        self.assertEqual(len(result.evaluations), 1)
        self.assertEqual(result.evaluations[0].matchScore, 55)
        self.assertEqual(result.evaluations[0].tier, 'potential')
        self.assertEqual(len(result.guide), 5)

    def test_a_non_five_question_guide_is_withheld_for_the_standard_guide(self):
        audit = AuditResponse(evaluations=[evaluation('NCT12345678', 90)], guide=[Question(title='Q', question='Ask?')])
        self.assertEqual(normalize(audit, [{'id': 'NCT12345678'}]).guide, [])

    async def test_evaluate_sends_only_reviewed_profile_and_public_registry_text(self):
        generated = {
            'evaluations': [{'nctId': 'NCT12345678', 'matchScore': 82, 'tier': 'strong', 'summary': 'Aligned.', 'criteria': [], 'strengths': [], 'gaps': [], 'unknowns': []}],
            'guide': [{'title': f'Q{i}', 'question': 'Ask?'} for i in range(5)],
        }
        trials = [{
            'id': 'NCT12345678', 'title': 'Study', 'phase': 'Phase 2', 'conditions': ['Lung cancer'],
            'interventions': ['Drug'], 'eligibility': 'Inclusion: EGFR', 'description': 'Summary',
            'contacts': [{'email': 'private@example.org'}], 'city': 'Atlanta',
        }]
        with patch('backend.evaluation.gemini', new=AsyncMock(return_value=generated)) as model:
            result = await evaluate(None, PROFILE, trials)
        payload = model.await_args.args[2]
        self.assertEqual(payload['profile'], {'condition': 'Lung cancer', 'stage': 'IIIA', 'biomarkers': ['EGFR']})
        self.assertNotIn('city', payload['profile'])
        self.assertNotIn('contacts', payload['trials'][0])
        self.assertEqual(result.evaluations[0].matchScore, 82)
