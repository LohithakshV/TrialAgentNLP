import unittest
from unittest.mock import AsyncMock, patch

from backend.evaluation import MalformedAudit, evaluate, normalize
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

    def test_normalization_repairs_malformed_fields_without_dropping_the_audit(self):
        raw = {
            'evaluations': [{
                'nct_id': 'nct12345678',
                'match_score': '82%',
                'tier': 'Strong',
                'summary': 'x' * 1200,
                'criteria': [
                    'Condition mentioned',
                    {'label': 'Stage', 'state': 'Met', 'reason': 'y' * 700},
                    {'name': 'Biomarker', 'status': 'not met', 'explanation': 'No match'},
                ],
                'strengths': 'Condition matches',
                'gaps': None,
                'unknowns': [{'text': 'Prior treatment unknown'}],
            }],
            'guide': ['Ask one?', 'Ask two?', 'Ask three?', 'Ask four?', 'Ask five?'],
        }
        result = normalize(raw, [{'id': 'NCT12345678'}])
        self.assertEqual(len(result.evaluations), 1)
        item = result.evaluations[0]
        self.assertEqual(item.nctId, 'NCT12345678')
        self.assertEqual(item.matchScore, 82)
        self.assertEqual(item.tier, 'strong')
        self.assertEqual(len(item.summary), 800)
        self.assertEqual([criterion.state for criterion in item.criteria], ['unknown', 'met', 'unmet'])
        self.assertEqual(item.gaps, ['Biomarker'])
        self.assertEqual(item.unknowns, ['Prior treatment unknown'])
        self.assertEqual(len(result.guide), 5)
        self.assertEqual(result.guide[0].title, 'Discussion question')

    def test_a_trial_without_a_score_is_left_unaudited_but_other_trials_are_kept(self):
        raw = {
            'evaluations': [
                {'nctId': 'NCT12345678', 'matchScore': 90, 'summary': 'Aligned.'},
                {'nctId': 'NCT87654321', 'summary': 'No score supplied.'},
            ],
            'guide': [],
        }
        result = normalize(raw, [{'id': 'NCT12345678'}, {'id': 'NCT87654321'}])
        self.assertEqual([item.nctId for item in result.evaluations], ['NCT12345678'])

    def test_more_than_five_valid_questions_are_capped_at_five(self):
        raw = {
            'evaluations': [{'nctId': 'NCT12345678', 'matchScore': 70}],
            'guide': [{'title': f'Q{i}', 'question': 'Ask?'} for i in range(7)],
        }
        result = normalize(raw, [{'id': 'NCT12345678'}])
        self.assertEqual(len(result.guide), 5)

    def test_a_non_object_audit_is_rejected_as_malformed(self):
        with self.assertRaises(MalformedAudit):
            normalize([], [{'id': 'NCT12345678'}])

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

    async def test_evaluate_repairs_imperfect_model_output_instead_of_failing(self):
        generated = {
            'evaluations': [{
                'nctId': 'NCT12345678',
                'matchScore': '74',
                'summary': 's' * 1000,
                'criteria': 'Condition listed',
            }],
            'guide': ['Ask one?', 'Ask two?', 'Ask three?', 'Ask four?', 'Ask five?'],
        }
        trials = [{
            'id': 'NCT12345678', 'title': 'Study', 'phase': 'Phase 2', 'conditions': ['Lung cancer'],
            'interventions': ['Drug'], 'eligibility': 'Inclusion: EGFR', 'description': 'Summary',
        }]
        with patch('backend.evaluation.gemini', new=AsyncMock(return_value=generated)):
            result = await evaluate(None, PROFILE, trials)
        self.assertEqual(result.evaluations[0].matchScore, 74)
        self.assertEqual(result.evaluations[0].tier, 'potential')
        self.assertEqual(len(result.evaluations[0].summary), 800)
        self.assertEqual(result.evaluations[0].criteria[0].state, 'unknown')
        self.assertEqual(len(result.guide), 5)
