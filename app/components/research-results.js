'use client';
import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { motion, useReducedMotion } from 'motion/react';
import { ArrowDown, ArrowLeft, ArrowRight, Check, ChevronDown, FileText, MapPin, Search, CircleHelp, Minus, Copy } from 'lucide-react';
import { useResearch } from './research-session';
import { Button, ExternalLink, Icon, Spinner } from './ui';
import { Steps } from './site-shell';

export default function ResearchResults() {
  const session = useResearch();
  const { result, busy, error, progress, backToReview, search } = session;
  const title = useRef(null);
  const reduced = useReducedMotion();
  useEffect(() => { if (result && !busy) title.current?.focus({ preventScroll: true }); }, [!!result, busy]);
  if (!result) return <main id="main-content" className="results-wait"><Steps current={2} />{busy ? <SearchProgress progress={progress} cancel={backToReview} /> : <div className="empty-state"><Icon as={Search} size={30} /><h1>{error ? 'Let’s try that again.' : 'Your research starts with a search.'}</h1><p>{error || 'Add a condition to explore recruiting study records.'}</p><div className="empty-actions">{error && <Button onClick={search}>Try again <Icon as={ArrowRight} size={16} /></Button>}<Link className="button button-ghost" href="/">{error ? 'Edit details' : 'Start a search'}<Icon as={ArrowRight} size={16} /></Link></div></div>}</main>;
  return <main id="main-content" className="results-main"><nav className="results-nav" aria-label="Results sections"><button onClick={backToReview} className="text-link"><Icon as={ArrowLeft} size={15} /> Edit search</button><div><a href="#overview">01 <span>Overview</span></a><a href="#studies">02 <span>Studies</span></a><a href="#questions">03 <span>Questions</span></a></div><span className="live-label"><span className="status-dot" />Live records</span></nav>
    <motion.section id="overview" className="results-overview" initial={{ opacity: 0, y: reduced ? 0 : 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: reduced ? 0 : .25 }}>
      <div className="overview-copy"><span className="section-label">01 / YOUR SEARCH</span><h1 ref={title} tabIndex={-1}>Research.<br /><span>With perspective.</span></h1><p>A place to start, not a decision to make alone.<br />Only a study team can confirm eligibility.</p><a href="#studies" className="scroll-link">Explore {result.trials.length} study records <span><Icon as={ArrowDown} size={18} /></span></a></div>
      <div className="search-context"><div className="context-top"><Icon as={FileText} size={19} /><span>Your reviewed details</span></div><h2>{result.profile.condition}</h2><dl><div><dt>Stage</dt><dd>{result.profile.stage || 'Not provided'}</dd></div><div><dt>Biomarkers</dt><dd>{result.profile.biomarkers.join(' · ') || 'Not provided'}</dd></div><div><dt>Location</dt><dd>{result.profile.city || 'Any location'}</dd></div></dl><div className="search-scope"><strong>How these records were found</strong><p>ClinicalTrials.gov was searched by condition{result.profile.city ? ' and city' : ''}, with recruiting status selected. Up to eight records are shown in registry order.</p><p>Stage and biomarkers are not registry filters. An AI-assisted review compares them with each record’s published criteria and marks each requirement met, not met, or unknown.</p><p>When an automated estimate is not shown, registry requirements are marked green when supported by your details and orange when they need confirmation.</p><p>Any score is an educational estimate, not an eligibility decision.</p></div><button className="text-link" onClick={backToReview}>Edit details <Icon as={ArrowRight} size={14} /></button></div>
    </motion.section>
    <section id="studies" className="result-section"><div className="section-heading"><div><span className="section-label">02 / EXPLORE THE RESEARCH</span><h2>Study records<span className="record-count">{result.trials.length}</span></h2></div><p>Registry-reported recruiting status.<br />Check the full record for sites and availability.</p></div>
      {busy && <div className="inline-progress" role="status"><Spinner /> {progress.message}<button className="text-link" onClick={session.cancel}>Stop search</button></div>}
      {error && <div className="error-message" role="alert">{error}</div>}
      {!!result.trials.length && <p className="registry-access-note">Read study details here, or open the official record. If ClinicalTrials.gov shows an access error, you can still use these retrieved details, copy the NCT ID, or open the source JSON.</p>}
      {!result.trials.length ? <div className="empty-records"><Icon as={Search} size={30} /><h3>No records found for this search.</h3><p>Try a broader condition or another city. This search does not cover every possible study.</p><Button variant="secondary" onClick={backToReview}>Edit condition or location<Icon as={ArrowRight} size={16} /></Button></div> : <div className="study-list">{result.trials.map((trial, i) => <StudyCard key={trial.id} trial={trial} index={i} reduced={reduced} />)}</div>}
      <p className="source-retrieval-note">Source: <ExternalLink href="https://clinicaltrials.gov">ClinicalTrials.gov</ExternalLink>{result.retrievedAt && <> · Retrieved {new Date(result.retrievedAt).toLocaleString()}</>}. Descriptions and eligibility text are registry material; discussion questions are labeled separately.</p>
      <details className="reading-help"><summary>New to clinical trials?<Icon as={ChevronDown} size={16} /></summary><div><p><strong>Recruiting</strong> means the registry lists a study as accepting participants. An individual site may have different availability.</p><p><strong>Phase</strong> describes a stage of research, not how suitable a study is for someone. Early phases often study safety and dosing; later phases may compare outcomes.</p><p><strong>Eligibility criteria</strong> are the study’s inclusion and exclusion rules. A registry search cannot confirm that someone meets all of them. <ExternalLink href="https://www.cancer.gov/research/participate/clinical-trials-search/steps">NCI guide to reviewing requirements</ExternalLink></p><p><strong>NCT ID</strong> is the study’s identifier on ClinicalTrials.gov. Use it when discussing a record.</p></div></details>
    </section>
    <section id="questions" className="result-section questions-section"><div className="section-heading"><div><span className="section-label">03 / THE NEXT CONVERSATION</span><h2>Bring better questions.</h2></div><Button variant="secondary" onClick={printOverview}><Icon as={FileText} size={16} /> Print overview</Button></div><p className="questions-intro">{result.guideOrigin === 'ai' ? 'AI-prepared questions based on your reviewed profile and retrieved records.' : 'Standard questions based on your reviewed details.'} Use them to prepare for a conversation with a qualified professional.</p><div className="question-list">{result.guide.map((item, i) => <div className="question" key={item.title}><span>0{i + 1}</span><div><h3>{item.title}</h3><p>{item.question}</p></div></div>)}</div><div className="closing-note"><img src="/brand/questions.svg" alt="" width="32" height="32" /><p>Research can open a conversation.<br /><strong>The study team helps determine what comes next.</strong></p></div></section>
  </main>;
}

function StudyCard({ trial, index, reduced }) {
  const sourceDetails = useRef(null);
  const [copyStatus, setCopyStatus] = useState('');
  function readStudy() {
    const panel = sourceDetails.current;
    if (!panel) return;
    panel.open = true;
    requestAnimationFrame(() => requestAnimationFrame(() => {
      panel.scrollIntoView({ behavior: reduced ? 'instant' : 'smooth', block: 'start' });
      panel.querySelector('summary')?.focus({ preventScroll: true });
    }));
  }
  async function copyId() {
    try { await navigator.clipboard.writeText(trial.id); setCopyStatus('Copied'); }
    catch { setCopyStatus('Select the NCT ID to copy it.'); }
  }
  return <motion.article className="study-card" initial={{ opacity: 0, y: reduced ? 0 : 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: .1 }} transition={{ duration: reduced ? 0 : .4, delay: reduced ? 0 : Math.min(index * .04, .16) }}>
    <div className="study-body">
      <div className="study-meta"><span className="recruiting">Listed as recruiting</span><span>{trial.phase}</span></div>
      <h3><button type="button" className="study-title-button" onClick={readStudy}>{trial.title}</button></h3>
      <div className="study-location"><Icon as={MapPin} size={15} />{trial.location}</div>
      {trial.matchScore == null ? (trial.criteria?.length ? <MatchPanel trial={trial} manual /> : <div className="match-panel audit-unavailable"><strong>Review the registry criteria</strong><p>{trial.summary || 'Confirm every requirement with the study team.'}</p></div>) : <MatchPanel trial={trial} />}
      {trial.evidence && <EvidenceChecklist evidence={trial.evidence} />}
      <details className="study-details" ref={sourceDetails}><summary>Source details and criteria<Icon as={ChevronDown} size={16} /></summary><div>
        <dl className="study-facts"><div><dt>Listed conditions</dt><dd>{trial.conditions?.join(', ') || 'Not provided'}</dd></div><div><dt>Being studied</dt><dd>{trial.interventions?.join(', ') || 'See the full record'}</dd></div><div><dt>Lead sponsor</dt><dd>{trial.sponsor || 'Not provided'}</dd></div><div><dt>Study type</dt><dd>{({INTERVENTIONAL:'Interventional',OBSERVATIONAL:'Observational',EXPANDED_ACCESS:'Expanded access'})[trial.studyType] || trial.studyType || 'Not provided'}</dd></div><div><dt>Listed age range</dt><dd>{trial.ageRange || 'Not provided'}</dd></div><div><dt>Listed sex categories</dt><dd>{({ALL:'All',FEMALE:'Female',MALE:'Male'})[trial.sex] || trial.sex || 'Not provided'}</dd></div></dl>
        <span className="detail-label">Registry overview excerpt</span><p>{trial.description || 'An overview is not available in this record. Read the full source for details.'}</p>
        <div className="study-contacts"><h4>Registry-listed contacts</h4>{trial.contacts?.length ? <><ul>{trial.contacts.map((contact, i) => <li key={`${contact.email || contact.name}-${i}`}><strong>{contact.name || 'Name not provided'}</strong><span>{contact.location}</span>{contact.phone && <span>{contact.phone}</span>}{contact.email && <a href={`mailto:${encodeURIComponent(contact.email)}`}>{contact.email}</a>}</li>)}</ul>{trial.contactsTruncated && <p>Selected contacts are shown. The source JSON contains the complete contact and site list.</p>}</> : <p>No contact details were included in the retrieved record. Use the NCT ID when checking with the registry or study team.</p>}</div>
        {trial.eligibility && <details className="eligibility-disclosure"><summary>Published criteria excerpt<Icon as={ChevronDown} size={15} /></summary><p>{trial.eligibility}</p><p>Read the complete inclusion and exclusion criteria in the linked registry record.</p></details>}
      </div></details>
      <div className="source-meta"><span className="verified-source"><Icon as={Check} size={15} />{trial.id}</span><button className="copy-study-id" type="button" onClick={copyId} aria-label={`Copy ${trial.id}`}><Icon as={Copy} size={14} />Copy ID</button><span>Registry updated {trial.updated}</span></div>
      {copyStatus && <p className="copy-status" role="status">{copyStatus}</p>}
      <div className="study-source-actions"><Button variant="secondary" onClick={readStudy}>Read study details<Icon as={ArrowRight} size={16} /></Button><ExternalLink className="registry-link" href={trial.url}>Official record</ExternalLink>{trial.apiUrl && <ExternalLink className="registry-link" href={trial.apiUrl}>Source JSON</ExternalLink>}</div>
    </div>
  </motion.article>;
}

const TIER_TEXT = { strong: 'Strong match', potential: 'Potential match', low: 'Lower match' };
const CRITERIA_GROUPS = [
  { state: 'met', title: 'Met', icon: Check },
  { state: 'unmet', title: 'Not met', icon: Minus },
  { state: 'unknown', title: 'Still unknown', icon: CircleHelp },
];
const MANUAL_CRITERIA_GROUPS = [
  { state: 'met', title: 'Supported by your details', icon: Check },
  { state: 'unknown', title: 'Needs confirmation', icon: CircleHelp },
];

function MatchPanel({ trial, manual = false }) {
  const criteria = trial.criteria || [];
  const groups = (manual ? MANUAL_CRITERIA_GROUPS : CRITERIA_GROUPS).map(group => ({ ...group, items: criteria.filter(item => item.state === group.state) })).filter(group => group.items.length);
  const lists = [
    { title: 'What lines up', items: trial.strengths },
    { title: 'What may not fit', items: trial.gaps },
    { title: 'Still unknown', items: trial.unknowns },
  ].filter(list => list.items?.length);
  return <div className={`match-panel ${manual ? 'manual' : `match-${trial.matchTier}`}`}>
    <div className="match-head">
      {manual ? <span className="match-tier tier-manual">Registry requirements</span> : <><span className="match-score"><strong>{trial.matchScore}</strong><span>/100</span></span><span className={`match-tier tier-${trial.matchTier}`}>{TIER_TEXT[trial.matchTier] || 'Match estimate'}</span></>}
      <span className="match-caption">{manual ? 'Published registry criteria · confirm with the study team' : 'AI-assisted eligibility review'}</span>
    </div>
    {trial.summary && <p className="match-summary">{trial.summary}</p>}
    {!!criteria.length && <details className="criteria-details" open={manual}><summary>Review {criteria.length} requirement{criteria.length === 1 ? '' : 's'}<Icon as={ChevronDown} size={16} /></summary>
      <div className="criteria-groups">{groups.map(group => <div className={`criteria-group criteria-${group.state}`} key={group.state}><h4><Icon as={group.icon} size={15} />{group.title}<span>{group.items.length}</span></h4><ul>{group.items.map((item, i) => <li key={`${item.label}-${i}`}><strong>{item.label}</strong>{item.reason && <p>{item.reason}</p>}</li>)}</ul></div>)}</div>
    </details>}
    {!!lists.length && <div className="match-lists">{lists.map(list => <div key={list.title}><h4>{list.title}</h4><ul>{list.items.map((item, i) => <li key={`${item}-${i}`}>{item}</li>)}</ul></div>)}</div>}
    <p className="match-disclaimer">{manual ? 'This checklist uses only the details you supplied and the registry text. Green means supported by those details, not confirmed eligibility. Confirm every requirement with the study team.' : 'This is an educational estimate from registry text, not an eligibility decision. Confirm every requirement with the study team.'}</p>
  </div>;
}

function EvidenceChecklist({ evidence }) {
  const ratio = evidence.provided > 0 ? Math.max(0, Math.min(1, evidence.mentioned / evidence.provided)) : 0;
  const red = [245, 161, 151], amber = [240, 207, 133], mint = [188, 236, 213];
  const from = ratio <= .5 ? red : amber;
  const to = ratio <= .5 ? amber : mint;
  const blend = ratio <= .5 ? ratio * 2 : (ratio - .5) * 2;
  const channels = from.map((value, i) => Math.round(value + (to[i] - value) * blend)).join(', ');
  const tint = evidence.provided > 0 ? { '--overlap-accent': `rgb(${channels})`, '--overlap-wash': `rgba(${channels}, .12)` } : { '--overlap-accent': '#afbeb3', '--overlap-wash': '#afbeb30d' };
  const labels = {listed:'Listed in registry',wording_to_review:'Wording needs review',not_located:'Exact wording not located',not_provided:'Not supplied'};
  return <details className="evidence-checklist" style={tint}><summary><span><strong>{evidence.mentioned} of {evidence.provided}</strong> supplied details mentioned<span className="evidence-caption">Literal source overlap · secondary signal</span><span className="overlap-meter" aria-hidden="true"><span style={{ width: `${ratio * 100}%` }} /></span></span><Icon as={ChevronDown} size={17} /></summary>
    <div className="evidence-content"><p>This counts literal text mentions, including possible exclusions. Different terminology may be missed. Use the eligibility review above as the primary signal.</p>
      <ul>{evidence.items.map((item, i) => <li key={`${item.field}-${i}`} className={`evidence-item evidence-${item.status}`}><span className="evidence-symbol"><Icon as={item.status === 'listed' ? Check : item.status === 'wording_to_review' ? FileText : item.status === 'not_located' ? CircleHelp : Minus} size={17} /></span><div><div className="evidence-item-heading"><strong>{item.label}</strong><span>{labels[item.status]}</span></div><p>{item.value || 'Not provided in your question'}</p>{item.excerpt && <><span className="evidence-source">{item.source}</span><blockquote><HighlightedExcerpt text={item.excerpt} value={item.value} /></blockquote></>}</div></li>)}</ul>
      <p className="evidence-next-step">Ask the study team to review the complete requirements, treatment history, test results, and site availability.</p>
    </div>
  </details>;
}

function HighlightedExcerpt({ text, value }) {
  const start = text.toLowerCase().indexOf(value.toLowerCase());
  return start < 0 ? text : <>{text.slice(0, start)}<mark>{text.slice(start, start + value.length)}</mark>{text.slice(start + value.length)}</>;
}

function SearchProgress({ progress, cancel }) {
  const labels = ['Search ClinicalTrials.gov', 'Audit eligibility criteria', 'Prepare your discussion guide'];
  return <section className="search-progress"><div className="progress-mark"><img src="/brand/trialagent-mark.svg" width="65" height="65" alt="" /></div><span className="section-label">EXPLORING THE REGISTRY</span><h1>A little clarity<br />is on its way.</h1><div className="search-status" role="status" aria-live="polite"><Spinner /><span>{progress.message}</span></div><ol>{labels.map((label, i) => <li key={label} className={progress.step >= i ? 'active' : ''}><span>{progress.step > i ? <Icon as={Check} size={14} /> : `0${i + 1}`}</span>{label}</li>)}</ol><button className="text-link" onClick={cancel}>Cancel search</button></section>;
}

function printOverview() {
  const disclosures = [...document.querySelectorAll('.study-details, .reading-help')];
  const states = disclosures.map(item => item.open);
  disclosures.forEach(item => { item.open = true; });
  window.print();
  disclosures.forEach((item, i) => { item.open = states[i]; });
}
