'use client';
import { useRef, useState } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'motion/react';
import { ArrowRight, ArrowLeft, Pencil, Check } from 'lucide-react';
import { useResearch } from './research-session';
import { Button, Icon } from './ui';
import { WebsiteSections } from './website-sections';
import ResearchComposer from './research-composer';

export default function ResearchWorkspace() {
  const session = useResearch();
  const { phase, busy, available, error } = session;
  const reduced = useReducedMotion();
  const heading = useRef(null);
  const searchSection = useRef(null);
  return <main id="main-content" className="home-page">
    <section className="website-hero interaction-hero">
      <motion.div className="hero-intro" initial={reduced ? false : { opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .6, ease: [.22, 1, .36, 1] }}>
        <h1>Start with a question.</h1>
        <p>A clearer way to explore clinical research.</p>
      </motion.div>
      <div className="web-search-section research-stage" id="search" ref={searchSection}>
        <AnimatePresence mode="wait" initial={false}>
          <motion.section key={phase} initial={{ opacity: 0, y: reduced ? 0 : 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: reduced ? 0 : .25 }} onAnimationComplete={() => {
            if (phase === 'review') {
              heading.current?.focus({ preventScroll: true });
              searchSection.current?.scrollIntoView({ behavior: reduced ? 'instant' : 'smooth', block: 'start' });
            }
          }}>
            {phase === 'details' ? <>
              <ResearchComposer session={session} />
              {busy && <div className="query-status" role="status"><span>Organizing the details you mentioned.</span><button className="text-link" onClick={session.cancel}>Cancel</button></div>}
              {available === false && <p className="inline-note" role="status">The research service is temporarily unavailable. The learning guides below are still available.</p>}
            </> : <QueryReview session={session} heading={heading} />}
            {error && phase !== 'details' && <p className="error-message" role="alert">{error}</p>}
          </motion.section>
        </AnimatePresence>
        <ol className="search-step-indicator stage-steps" aria-label="Search steps">
          <li className={phase === 'details' ? 'active' : 'complete'}><span className="stage-step-number">1</span>Describe</li>
          <li className={phase === 'review' ? 'active' : ''}><span className="stage-step-number">2</span>Check</li>
          <li><span className="stage-step-number">3</span>Explore</li>
        </ol>
      </div>
    </section>
    <WebsiteSections />
  </main>;
}

function QueryReview({ session, heading }) {
  const { profile, editProfile, search } = session;
  const [editing, setEditing] = useState(!profile.condition);
  const [biomarkers, setBiomarkers] = useState(profile.biomarkers.join(', '));
  const update = (field, value) => editProfile({ ...profile, [field]: value });
  const fields = [['Condition', profile.condition || 'Add a condition'], ['Stage', profile.stage || 'Not specified'], ['Biomarkers', profile.biomarkers.join(', ') || 'Not specified'], ['City', profile.city || 'Any location']];
  return <div className="query-review"><div className="query-review-heading"><div><h2 ref={heading} tabIndex={-1}>Here’s what we understood.</h2><p>{profile.condition ? 'Check the details before searching the registry.' : 'Add the condition you want to research.'}</p></div><button className="button button-secondary" onClick={() => setEditing(!editing)} type="button" aria-expanded={editing} aria-controls="query-edit-fields"><Icon as={editing ? Check : Pencil} size={15} />{editing ? 'Done editing' : 'Edit details'}</button></div>
    {!editing && <dl className="query-preview">{fields.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>}
    {editing && <div className="profile-fields" id="query-edit-fields"><div className="field full"><label htmlFor="condition">Condition <span>Required</span></label><input id="condition" required minLength={3} maxLength={160} value={profile.condition} onChange={e => update('condition', e.target.value)} autoComplete="off" /></div><div className="field"><label htmlFor="stage">Stage <span>Optional</span></label><input id="stage" maxLength={80} value={profile.stage} onChange={e => update('stage', e.target.value)} /></div><div className="field"><label htmlFor="city">City <span>Optional</span></label><input id="city" maxLength={100} value={profile.city} onChange={e => update('city', e.target.value)} autoComplete="off" /></div><div className="field full"><label htmlFor="biomarkers">Biomarkers <span>Separate with commas</span></label><input id="biomarkers" maxLength={2000} value={biomarkers} onChange={e => { setBiomarkers(e.target.value); update('biomarkers', e.target.value.split(',').map(s => s.trim()).filter(Boolean).slice(0, 12)); }} /></div></div>}
    <div className="query-review-bottom"><Button variant="ghost" onClick={() => session.setPhase('details')}><Icon as={ArrowLeft} size={15} /> Edit question</Button><Button disabled={profile.condition.trim().length < 3} onClick={search}>Find recruiting studies<Icon as={ArrowRight} size={16} /></Button></div><p className="review-footnote">Your condition and city guide the registry search. A study team confirms eligibility.</p></div>;
}

