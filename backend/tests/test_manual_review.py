import unittest

from backend.evidence import eligibility_items, manual_review
from backend.models import Profile


PROFILE = Profile(condition='Lung cancer', stage='IIIA', biomarkers=['EGFR'], city='Atlanta')
TRIAL = {
    'id': 'NCT12345678',
    'conditions': ['Lung cancer'],
    'description': 'A study of lung cancer.',
    'eligibility': '''Inclusion Criteria:
1. Histologically confirmed lung cancer.
2. Stage IIIA disease.
3. EGFR mutation positive.
4. Age 18 years or older.

Exclusion Criteria:
1. Prior chemotherapy.
2. Active brain metastases.
''',
    'ageRange': '18 Years and older',
    'sex': 'ALL',
}


class EligibilityItems(unittest.TestCase):
    def test_splits_inclusion_and_exclusion_bullets(self):
        items = eligibility_items(TRIAL['eligibility'])
        self.assertEqual([item['section'] for item in items], ['inclusion'] * 4 + ['exclusion'] * 2)
        self.assertEqual(items[0]['text'], 'Histologically confirmed lung cancer.')
        self.assertEqual(items[-1]['text'], 'Active brain metastases.')


class ManualReview(unittest.TestCase):
    def test_profile_details_in_inclusion_only_are_green(self):
        review = manual_review(PROFILE, TRIAL)
        states = {item['label']: item['state'] for item in review['criteria']}
        self.assertEqual(states['Condition: Lung cancer'], 'met')
        self.assertEqual(states['Stage: IIIA'], 'met')
        self.assertEqual(states['Biomarker: EGFR'], 'met')
        self.assertEqual(states['Sex: All'], 'met')
        self.assertIn('Green items are supported', review['summary'])

    def test_exclusion_mentions_keep_profile_items_orange(self):
        trial = {
            **TRIAL,
            'eligibility': '''Inclusion Criteria:
1. Stage IIIA disease.
2. EGFR mutation positive.

Exclusion Criteria:
1. Prior EGFR inhibitor therapy.
2. Stage IIIA recurrence.
''',
        }
        review = manual_review(PROFILE, trial)
        states = {item['label']: item for item in review['criteria']}
        self.assertEqual(states['Stage: IIIA']['state'], 'unknown')
        self.assertEqual(states['Biomarker: EGFR']['state'], 'unknown')
        self.assertIn('exclusion criteria', states['Stage: IIIA']['reason'])
        self.assertIn('exclusion criteria', states['Biomarker: EGFR']['reason'])

    def test_remaining_requirements_are_orange(self):
        review = manual_review(PROFILE, TRIAL)
        states = {item['label']: item['state'] for item in review['criteria']}
        self.assertEqual(states['Age range: 18 Years and older'], 'unknown')
        self.assertEqual(states['Histologically confirmed lung cancer.'], 'unknown')
        self.assertEqual(states['Exclusion: Active brain metastases.'], 'unknown')
        self.assertTrue(all(state in {'met', 'unknown'} for state in states.values()))

    def test_unlisted_condition_is_orange(self):
        trial = {
            **TRIAL,
            'conditions': ['Breast cancer'],
            'description': 'A breast cancer study.',
            'eligibility': 'Inclusion Criteria:\n1. Breast cancer diagnosis.\n\nExclusion Criteria:\n1. Prior chemotherapy.',
        }
        review = manual_review(PROFILE, trial)
        states = {item['label']: item for item in review['criteria']}
        self.assertEqual(states['Condition: Lung cancer']['state'], 'unknown')
        self.assertIn('Not found in the listed conditions', states['Condition: Lung cancer']['reason'])

    def test_criteria_are_capped_and_deduplicated(self):
        bullets = '\n'.join(f'{i}. Inclusion requirement number {i}.' for i in range(1, 21))
        trial = {**TRIAL, 'eligibility': f'Inclusion Criteria:\n{bullets}'}
        review = manual_review(PROFILE, trial)
        labels = [item['label'] for item in review['criteria']]
        self.assertLessEqual(len(labels), 10)
        self.assertEqual(len(labels), len(set(labels)))

    def test_missing_structured_criteria_still_return_a_checklist(self):
        trial = {**TRIAL, 'eligibility': '', 'ageRange': 'Not provided', 'sex': ''}
        review = manual_review(PROFILE, trial)
        states = {item['label']: item['state'] for item in review['criteria']}
        self.assertEqual(states['Full inclusion and exclusion criteria'], 'unknown')
        self.assertTrue(review['criteria'])
