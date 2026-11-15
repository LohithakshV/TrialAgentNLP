'use client';
import { useEffect, useRef, useState } from 'react';
import NextLink from 'next/link';
import { Menu, X, RotateCcw, ArrowUpRight, Search } from 'lucide-react';
import { useResearch } from './research-session';
import { useNavigationState } from '../hooks/use-navigation-state';
import { Icon } from './ui';

const navigation = [
  { id: 'how-it-works', label: 'How it works' },
  { id: 'learn', label: 'Learning library' },
];

function Link({ href, ...props }) {
  return <NextLink {...props} href={href} onNavigate={event => {
    // Re-selecting the current hash is still a request to return to its section.
    if (href.startsWith('/#') && window.location.pathname === '/' && window.location.hash === href.slice(1)) {
      const section = document.getElementById(href.slice(2));
      if (section) {
        event.preventDefault();
        section.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'start' });
      }
    }
  }} />;
}

export function SiteHeader() {
  const { reset, note, result } = useResearch();
  const { compact, active, pathname } = useNavigationState();
  const [open, setOpen] = useState(false);
  const menuButton = useRef(null);
  useEffect(() => setOpen(false), [pathname]);

  function closeMenu() { setOpen(false); }
  function startOver() { reset(); closeMenu(); }

  return (
    <header className={`navigation-shell${compact ? ' is-compact' : ''}`} data-state={compact ? 'compact' : 'expanded'} onKeyDown={event => {
      if (event.key === 'Escape' && open) { closeMenu(); menuButton.current?.focus(); }
    }}>
      <div className="navigation-island">
        <Link href="/" className="wordmark navigation-brand" aria-label="TrialAgent home" onClick={closeMenu}>
          <img src="/brand/trialagent-mark.svg" width="34" height="34" alt="" />
          <span>TrialAgent</span>
        </Link>

        <nav className="island-links" aria-label="Main navigation">
          {navigation.map(item => <Link key={item.id} href={`/#${item.id}`} className="island-nav-link" aria-current={pathname === '/' && active === item.id ? 'location' : undefined}>{item.label}</Link>)}
        </nav>

        <div className="island-actions">
          <Link className="island-privacy" href="/privacy" aria-label="Privacy and data flow" aria-current={pathname === '/privacy' ? 'page' : undefined} onClick={closeMenu}>
            <img src="/brand/privacy.svg" width="21" height="21" alt="" /><span>Privacy</span>
          </Link>
          {(note || result) && <button className="island-icon-button island-reset" aria-label="Start a new search" onClick={startOver}><Icon as={RotateCcw} size={17} /></button>}
          <Link className="island-search" href="/#search" onClick={closeMenu}><Icon as={Search} size={16} /><span className="island-wide-label">Find studies</span><span className="island-short-label">Search</span></Link>
          <button ref={menuButton} className="island-icon-button island-menu-toggle" aria-label={open ? 'Close navigation' : 'Open navigation'} aria-expanded={open} aria-controls="mobile-navigation" onClick={() => setOpen(!open)}><Icon as={open ? X : Menu} size={20} /></button>
        </div>

        {open && <nav id="mobile-navigation" className="island-mobile-menu" aria-label="Mobile navigation">
          <Link onClick={closeMenu} href="/#search"><Icon as={Search} size={17} /><span>Find studies</span></Link>
          {navigation.map(item => <Link key={item.id} onClick={closeMenu} href={`/#${item.id}`}>{item.label}</Link>)}
          <Link onClick={closeMenu} href="/privacy"><img src="/brand/privacy.svg" width="19" height="19" alt="" /><span>Privacy & data flow</span></Link>
          <button onClick={startOver}><Icon as={RotateCcw} size={17} />Start a new search</button>
        </nav>}
      </div>
    </header>
  );
}

export function SiteFooter() {
  return <footer className="website-footer"><div className="footer-upper"><div className="footer-brand"><Link href="/" className="wordmark"><img src="/brand/trialagent-mark.svg" width="32" height="32" alt="" />TrialAgent</Link><p>A calmer place to start<br />learning about clinical research.</p></div><div className="footer-links"><span>Explore</span><Link href="/#search">Find studies</Link><Link href="/#how-it-works">How it works</Link><Link href="/#learn">Learning library</Link></div><div className="footer-links"><span>Go to the source</span><a href="https://clinicaltrials.gov" target="_blank" rel="noopener noreferrer">ClinicalTrials.gov<Icon as={ArrowUpRight} size={13} /></a><a href="https://www.nih.gov/health-information/nih-clinical-research-trials-you/basics" target="_blank" rel="noopener noreferrer">NIH clinical trial basics<Icon as={ArrowUpRight} size={13} /></a><Link href="/privacy">Privacy & data flow</Link></div></div><div className="footer-lower"><span>Educational use. Not medical advice.</span><span>Only a study team can confirm eligibility.</span></div></footer>;
}

export function Steps({ current }) {
  return <ol className="workflow-steps" aria-label="Research steps">{['Describe', 'Check', 'Explore'].map((name, i) => <li key={name} aria-current={i === current ? 'step' : undefined} className={i < current ? 'complete' : ''}><span className="step-index">0{i + 1}</span><span>{name}</span>{i < 2 && <span className="step-line" />}</li>)}</ol>;
}
