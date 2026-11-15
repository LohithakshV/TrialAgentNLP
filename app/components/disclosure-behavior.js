'use client';
import { useEffect } from 'react';

export default function DisclosureBehavior() {
  useEffect(() => {
    const seen = new WeakSet();
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) {
        const panel = entry.target;
        if (!panel.isConnected) { observer.unobserve(panel); continue; }
        if (entry.isIntersecting) seen.add(panel);
        else if (seen.has(panel) && panel.open) panel.open = false;
      }
    }, { rootMargin: '-112px 0px 0px 0px' });

    function onToggle(event) {
      const panel = event.target;
      if (!(panel instanceof HTMLDetailsElement)) return;
      if (panel.open) {
        // Preserve the ancestor chain when opening nested eligibility text.
        document.querySelectorAll('main details[open]').forEach(other => {
          if (other !== panel && !other.contains(panel) && !panel.contains(other)) other.open = false;
        });
        observer.observe(panel);
      } else {
        observer.unobserve(panel);
        seen.delete(panel);
        panel.querySelectorAll('details[open]').forEach(child => { child.open = false; });
      }
    }

    function beforeSectionNavigation(event) {
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const link = event.target instanceof Element ? event.target.closest('a[href]') : null;
      if (!link) return;
      const destination = new URL(link.href, window.location.href);
      if (destination.origin === window.location.origin && destination.pathname === window.location.pathname && destination.hash) {
        const panels = document.querySelectorAll('main details[open]');
        const target = document.getElementById(destination.hash.slice(1));
        if (!target) return;
        // Let the collapsed layout settle before measuring the anchor target.
        event.preventDefault();
        panels.forEach(panel => { panel.open = false; });
        if (window.location.hash !== destination.hash) window.history.pushState(window.history.state, '', destination);
        requestAnimationFrame(() => requestAnimationFrame(() => target.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'start' })));
      }
    }

    document.addEventListener('toggle', onToggle, true);
    document.addEventListener('click', beforeSectionNavigation, true);
    document.querySelectorAll('main details[open]').forEach(panel => observer.observe(panel));
    return () => { document.removeEventListener('toggle', onToggle, true); document.removeEventListener('click', beforeSectionNavigation, true); observer.disconnect(); };
  }, []);
  return null;
}
