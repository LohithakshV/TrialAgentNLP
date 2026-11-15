'use client';
import { useEffect, useRef } from 'react';
import Link from 'next/link';
import { ArrowRight, ChevronUp, ChevronDown } from 'lucide-react';
import { useDockedComposer } from '../hooks/use-docked-composer';
import { Button, Icon, Spinner, Warning, ConsentCheckbox } from './ui';

export default function ResearchComposer({ session }) {
  const { anchor, form, docked, height, expanded, setExpanded } = useDockedComposer();
  const textarea = useRef(null);
  const checkbox = useRef(null);
  const feedbackNotice = useRef(null);
  const { busy, available } = session;
  const compact = docked && !expanded;
  useEffect(() => {
    if (session.feedback) {
      setExpanded(true);
      requestAnimationFrame(() => feedbackNotice.current?.focus({ preventScroll: true }));
    }
  }, [session.feedback, setExpanded]);

  function submit(event) {
    event.preventDefault();
    if (!session.consent) {
      setExpanded(true);
      requestAnimationFrame(() => checkbox.current?.focus());
      return;
    }
    session.extract();
  }

  return <div className="composer-anchor" ref={anchor} style={docked ? { height } : undefined}>
    <form ref={form} className={`web-composer persistent-composer${docked ? ' composer-docked' : ''}${compact ? ' composer-compact' : ''}`} onSubmit={submit} onKeyDown={event => {
      if (event.key === 'Escape' && docked && expanded) { setExpanded(false); textarea.current?.focus(); }
    }} aria-label="Research question">
      {docked && <div className="docked-composer-heading"><span><img src="/brand/trialagent-mark.svg" alt="" width="20" height="20" />Your research</span><button type="button" className="dock-toggle" aria-label={expanded ? 'Collapse research box' : 'Expand research box'} aria-expanded={expanded} aria-controls="composer-disclosure" onClick={() => setExpanded(!expanded)}><Icon as={expanded ? ChevronDown : ChevronUp} size={18} /></button></div>}
      {session.feedback && <div className="prompt-feedback" ref={feedbackNotice} tabIndex={-1} role="status" aria-live="polite"><h2>{session.feedback.title}</h2><p>{session.feedback.message}</p><div className="feedback-example"><span>{session.feedback.example}</span><button type="button" onClick={() => { session.editNote(session.feedback.example); textarea.current?.focus(); }}>Use example</button></div><a href={session.feedback.resource.href} target="_blank" rel="noopener noreferrer">Read the clinical trial introduction<Icon as={ArrowRight} size={15} /></a></div>}
      <div className="composer-input-row"><label className={docked ? 'sr-only' : 'composer-title'} htmlFor="research-note">{!docked && <span className="composer-emblem" aria-hidden="true"><img src="/brand/trialagent-mark.svg" alt="" width="23" height="23" /></span>}Describe your research question</label><textarea ref={textarea} id="research-note" placeholder={compact ? 'Ask a research question…' : 'A condition, a study topic, or something you want to understand…'} value={session.note} onChange={event => session.editNote(event.target.value)} autoComplete="off" spellCheck="false" minLength={3} maxLength={6000} required disabled={!!busy} aria-describedby={compact ? 'compact-composer-hint' : 'query-help privacy-warning'} />
        {compact && <Button className="dock-submit" disabled={!!busy || !!session.feedback || session.note.trim().length < 3 || available === false} type="submit" aria-label={session.consent ? 'Prepare my search' : 'Review privacy before continuing'}>{busy ? <Spinner /> : <Icon as={ArrowRight} size={19} />}</Button>}
      </div>
      {compact && <p className="compact-composer-hint" id="compact-composer-hint">{available === false ? 'The research service is temporarily unavailable.' : session.consent ? 'Your draft stays with you.' : 'Fictional details only. Review privacy to continue.'}</p>}
      <div id="composer-disclosure" hidden={compact}>
        <div className="composer-hint" id="query-help">A condition is enough. Add other details if you know them.</div>
        <div className="composer-safety"><Warning /><ConsentCheckbox inputRef={checkbox} checked={session.consent} onChange={event => session.setConsent(event.target.checked)} required={!compact} disabled={!!busy}>I’m 18 or older and using fictional, non-sensitive details. Google receives this text; the registry later receives the condition and city.</ConsentCheckbox>
          <div className="composer-bottom"><div className="legal-links"><a href="https://ai.google.dev/gemini-api/terms" target="_blank" rel="noopener noreferrer">Google terms</a><Link href="/privacy">Privacy & data flow</Link></div><Button disabled={!!busy || !!session.feedback || !session.consent || session.note.trim().length < 3 || available === false} type="submit">{busy ? <><Spinner />Reading your question</> : <>Prepare my search<Icon as={ArrowRight} size={17} /></>}</Button></div>
        </div>
      </div>
      {session.error && <p className="error-message composer-error" role="alert">{session.error}</p>}
      {docked && busy && <button className="text-link dock-cancel" type="button" onClick={session.cancel}>Cancel</button>}
    </form>
  </div>;
}
