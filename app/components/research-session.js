'use client';
import { createContext, useContext, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { MotionConfig } from 'motion/react';
import { postJSON, readEvents } from '../lib/research-client.mjs';
import { promptFeedback } from '../lib/prompt-feedback.mjs';

const Session = createContext(null);
const emptyProfile = () => ({ condition: '', stage: '', biomarkers: [], city: '' });
export function ResearchSession({ children }) {
  const router = useRouter();
  const [note, setNote] = useState('');
  const [profile, setProfile] = useState(emptyProfile);
  const [phase, setPhase] = useState('details');
  const [busy, setBusy] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [feedback, setFeedback] = useState(null);
  const [progress, setProgress] = useState({ step: 0, message: 'Searching ClinicalTrials.gov' });
  const [available, setAvailable] = useState(null);
  const [consent, setConsent] = useState(false);
  const [prepared, setPrepared] = useState(null);
  const active = useRef({ id: 0, controller: null });
  const running = useRef(false);
  useEffect(() => {
    const controller = new AbortController();
    fetch('/api/health', { cache: 'no-store', signal: controller.signal }).then(r => r.json()).then(d => setAvailable(d.liveAvailable)).catch(() => setAvailable(false));
    return () => { controller.abort(); active.current.controller?.abort(); };
  }, []);
  function begin(kind) {
    if (running.current) return null;
    running.current = true;
    const controller = new AbortController(); const id = ++active.current.id;
    active.current.controller = controller; setBusy(kind); setError('');
    return { id, controller };
  }
  function finish(id) { if (id !== active.current.id) return; running.current = false; setBusy(null); }
  function cancel() { active.current.id++; active.current.controller?.abort(); running.current = false; setBusy(null); setError(''); }
  function reset() { cancel(); setNote(''); setProfile(emptyProfile()); setPhase('details'); setResult(null); setConsent(false); setPrepared(null); setFeedback(null); setProgress({ step: 0, message: '' }); router.push('/'); }
  function editNote(value) { setNote(value); setPrepared(null); setFeedback(null); setConsent(false); setResult(null); setError(''); }
  function editProfile(value) { setProfile(value); setResult(null); setError(''); }
  async function extract() {
    if (!consent || feedback) return;
    if (prepared) { setPhase('review'); return; }
    const request = begin('extract'); if (!request) return;
    try {
      const response = await postJSON('/api/extract', { note, consent: true }, request.controller.signal);
      const data = await response.json();
      if (request.id !== active.current.id) return;
      if (data.status !== 'ready' || !data.profile?.condition) throw new Error('We could not prepare this search. Please edit your question and try again.');
      setProfile(data.profile); setPrepared(data); setPhase('review');
    } catch (err) {
      if (request.id === active.current.id && err.name !== 'AbortError') {
        const notice = promptFeedback(err.code);
        if (notice) setFeedback(notice);
        else setError(err.message);
      }
    }
    finally { finish(request.id); }
  }
  async function search() {
    if (!consent || !profile.condition.trim()) return;
    const request = begin('search'); if (!request) return;
    setResult(null); setProgress({ step: 0, message: 'Searching ClinicalTrials.gov' }); router.push('/results');
    try {
      const response = await postJSON('/api/search', { profile, consent: true }, request.controller.signal);
      await readEvents(response.body, (kind, data) => {
        if (request.id !== active.current.id) return;
        if (kind === 'progress') setProgress(data);
        if (kind === 'records' || kind === 'result') {
          setResult(data);
        }
      });
    } catch (err) { if (request.id === active.current.id && err.name !== 'AbortError') setError(err.message); }
    finally { finish(request.id); }
  }
  function backToReview() { cancel(); setPhase('review'); router.push('/'); }
  return <Session.Provider value={{ note, editNote, profile, editProfile, phase, setPhase, busy, result, error, feedback, progress, available, consent, setConsent, extract, search, cancel, reset, backToReview }}><MotionConfig reducedMotion="user">{children}</MotionConfig></Session.Provider>;
}
export const useResearch = () => useContext(Session);
