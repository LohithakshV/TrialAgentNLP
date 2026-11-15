'use client';
import { useState } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'motion/react';
import { ArrowRight, ArrowUpRight, ChevronDown } from 'lucide-react';
import { resources } from '../lib/resources.mjs';
import { Icon } from './ui';

export function Reveal({ children, className = '' }) {
  const reduced = useReducedMotion();
  return <motion.div className={className} initial={reduced ? false : { opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: .12 }} transition={{ duration: reduced ? 0 : .55, ease: [.22, 1, .36, 1] }}>{children}</motion.div>;
}

const process = [
  { title: 'Start with a question.', body: 'Write naturally. A condition is enough to begin.', symbol: 'trialagent-mark', detail: 'TrialAgent organizes the condition, stage, biomarkers, and city you mention. You do not need to know every detail.' },
  { title: 'Make sure it sounds right.', body: 'Check what was understood. Change anything.', symbol: 'privacy', detail: 'You see the extracted details before a registry search. Missing information stays unknown, and every field can be edited.' },
  { title: 'Explore with context.', body: 'Read study records and take questions with you.', symbol: 'questions', detail: 'Open the original registry record, read its requirements, and use your discussion guide to prepare for a conversation with a qualified professional.' },
];

export function WebsiteSections() {
  const [active, setActive] = useState(0);
  const reduced = useReducedMotion();
  return <>
    <section className="web-section process-section" id="how-it-works"><Reveal><div className="web-section-heading"><h2>A little structure.<br />A clearer next step.</h2><p>Three steps, at your pace.</p></div><div className="process-cards" role="group" aria-label="How a search works">{process.map((step, i) => <button key={step.title} className={`process-card ${active === i ? 'selected' : ''}`} aria-pressed={active === i} onClick={() => setActive(i)}><div className="process-card-top"><img src={`/brand/${step.symbol}.svg`} width="38" height="38" alt="" /><span>0{i + 1}</span></div><h3>{step.title}</h3><p>{step.body}</p><span className="process-track">{active === i && <motion.span layoutId="process-track" transition={{ duration: reduced ? 0 : .35, ease: [.22, 1, .36, 1] }} />}</span></button>)}</div><div className="process-description" aria-live="polite"><AnimatePresence mode="wait" initial={false}><motion.p key={active} initial={{ opacity: 0, y: reduced ? 0 : 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: reduced ? 0 : .18 }}>{process[active].detail}</motion.p></AnimatePresence></div></Reveal></section>
    <section className="web-section learning-section" id="learn"><Reveal><div className="web-section-heading"><div className="learning-heading"><img src="/brand/learning.svg" width="42" height="42" alt="" /><h2>A place to begin.</h2></div><p>New to clinical trials?<br />These guides make a useful first read.</p></div><div className="learning-grid">{resources.map(item => <a className={`learning-card ${item.featured ? 'feature' : 'compact-card'}`} key={item.id} href={item.href} target="_blank" rel="noopener noreferrer"><div className="resource-top"><img src={`/brand/${item.symbol}.svg`} alt="" width={item.featured ? 66 : 32} height={item.featured ? 66 : 32} /><Icon as={ArrowUpRight} size={20} /></div><div><span className="resource-source">{item.organization}</span><h3>{item.title}</h3><p>{item.description}</p></div><span className="resource-action">{item.label}<Icon as={ArrowUpRight} size={15} /></span></a>)}</div></Reveal></section>
    <section className="web-section practical-section" id="resources"><Reveal className="practical-grid"><div><h2>What helps<br />a search?</h2><p>Start small. Add only what you know.</p><a className="underlined-link" href="#search">Back to your question<Icon as={ArrowRight} size={15} /></a></div><div className="practical-questions"><details open><summary>A condition or area of research<Icon as={ChevronDown} size={17} /></summary><p>This is the starting point for the registry search. You can describe it in your own words and check the interpretation before continuing.</p></details><details><summary>Stage and biomarker details, if known<Icon as={ChevronDown} size={17} /></summary><p>These can help frame questions about a study’s requirements. Leave them out if unknown. A study team will need to confirm the actual criteria.</p></details><details><summary>A city, if location matters<Icon as={ChevronDown} size={17} /></summary><p>Add a city to focus the search. A site being listed does not confirm that it has an available place; check the registry record or contact the study team.</p></details><details><summary>What happens after finding a study?<Icon as={ChevronDown} size={17} /></summary><p>Read the source record and discuss it with a qualified professional. A research coordinator can explain screening, visits, possible risks, and the consent process.</p></details></div></Reveal></section>

  </>;
}
