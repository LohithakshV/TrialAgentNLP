# Research API and source evidence

## Prepare a fictional prompt

`POST /api/extract`, JSON `{ "note": "Fictional asthma studies near Boston", "consent": true }`.

One Gemini request performs classification, extraction, and question preparation. The schema requires a status of `ready`, `needs_details`, or `off_topic`; unknown or missing statuses fail closed. Non-ready responses discard all model-produced profile details and questions. A ready response without a condition is downgraded to `needs_details`.

HTTP 200, ready response:

```json
{
  "status": "ready",
  "profile": { "condition": "Asthma", "stage": "", "biomarkers": [], "city": "Boston" },
  "guide": [
    { "title": "Requirements to confirm", "question": "Which tests and records would the study team need to review?" }
  ]
}
```

The guide above is abbreviated for documentation; actual ready responses require exactly five questions.

HTTP 422, semantic rejection:

```json
{
  "error": "Please describe a condition or clinical research topic to look up study records.",
  "code": "off_topic"
}
```

`needs_details` instead asks for a condition and points the UI toward the introductory clinical-trial guide. Error copy, example prompts, and links are app-controlled; Gemini does not invent source URLs. The UI preserves the original draft, announces the feedback, and disables unchanged re-submission until editing. Choosing the fictional example clears the notice and requires acknowledgment again.

Classification is model-assisted and can be wrong; schema validation checks structure, not clinical truth. This is not an authentication or security boundary. `/api/search` accepts the reviewed profile independently and has its own consent, field validation, and rate limits.

## Retrieve records

`POST /api/search`, JSON `{ "profile": { "condition": "Asthma", "stage": "", "biomarkers": [], "city": "Boston" }, "consent": true }`.

The response is SSE with JSON `progress` and terminal `result` events. It makes **zero Gemini calls**. The result contains `profile`, `trials`, five standard fallback questions, `guideOrigin`, `source`, `retrievedAt`, and `searchScope`. The browser uses previously prepared AI questions only while the reviewed profile remains unchanged.

The registry query uses condition, optional city, recruiting status, and a limit of eight. Stage and biomarkers are context for manual source review; they are not query filters. Registry order is preserved. Recruiting status does not establish a local site's availability.

Each record includes the NCT ID, title, phase, listed site cities, conditions, interventions, lead sponsor, study type, listed age range and sex categories, registry update date, source excerpts, and a direct ClinicalTrials.gov URL constructed from a validated NCT ID. Overviews are limited to 4,000 characters and criteria to 14,000 characters; the UI labels them as excerpts and links to the full record.

`apiUrl` is the official public JSON URL for the validated NCT ID. `contacts` contains registry-listed name, role, email, phone, and location fields; central contacts are prioritized, followed by site contacts near the requested city. Duplicates are removed and at most six contacts are returned. `contactsTruncated` identifies a selected list. Missing contact information is not invented.

Study titles and the primary reader action show the already-retrieved source details within the app. Opening this reader requires no additional provider request. The official website link remains separate; the app cannot guarantee the external site will load or fix a third-party 403. A copyable ID and source JSON link are alternate access paths.

## Literal source-overlap checklist

`trial.evidence` is calculated on the server without a model call:

```json
{
  "provided": 3,
  "mentioned": 2,
  "meaning": "Literal mentions of supplied details in this record. This is not an eligibility score; exclusions can mention the same terms.",
  "items": [
    { "field": "condition", "label": "Condition", "value": "Asthma", "status": "listed", "source": "Listed conditions", "excerpt": "Asthma" },
    { "field": "stage", "label": "Stage", "value": "", "status": "not_provided", "source": "", "excerpt": "" },
    { "field": "biomarker", "label": "Biomarker", "value": "Example marker", "status": "not_located", "source": "", "excerpt": "" },
    { "field": "city", "label": "City", "value": "Boston", "status": "listed", "source": "Listed site cities", "excerpt": "Boston" }
  ]
}
```

- `listed`: a supplied condition or city is literally found in the structured registry conditions/site-city list. A mint check indicates this source fact only.
- `wording_to_review`: the term is found in overview or eligibility wording. This may be an exclusion and is never marked as a requirement met.
- `not_located`: no literal phrase was found in the inspected fields/excerpts. Synonyms, spelling differences, abbreviations, and text outside the excerpts can be missed. This does not establish a mismatch or exclusion.
- `not_provided`: the optional detail was absent. It is excluded from the denominator. Each supplied biomarker counts as one detail.

Matching is case-insensitive and tolerates punctuation between words; it does not interpret negation, combine aliases, infer diagnoses, evaluate clinical criteria, or rank clinical suitability. Excerpts retain surrounding source text and highlight literal wording. There are no met/not-met eligibility decisions or eligibility percentages.

Medical context: [NCI's guide to finding a trial](https://www.cancer.gov/research/participate/clinical-trials-search/steps). Structured classification uses [Gemini's JSON Schema output](https://aistudio.google.com/docs/structured-output). Trial data comes from the [ClinicalTrials.gov API](https://clinicaltrials.gov/data-api/api).
