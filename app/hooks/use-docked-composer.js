'use client';
import { useEffect, useRef, useState } from 'react';

export function useDockedComposer() {
  const anchor = useRef(null);
  const form = useRef(null);
  const [docked, setDocked] = useState(false);
  const [height, setHeight] = useState(0);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (!anchor.current || !form.current) return;
    const measure = () => {
      // A queued ResizeObserver callback can run after React changes the class,
      // before this effect is cleaned up. Never reserve the compact form's height.
      if (form.current && !form.current.classList.contains('composer-docked')) {
        setHeight(form.current.getBoundingClientRect().height);
      }
    };
    measure();
    const resize = new ResizeObserver(measure);
    resize.observe(form.current);
    const observer = new IntersectionObserver(([entry]) => {
      const aboveHeader = entry.boundingClientRect.bottom <= 112;
      setDocked(!entry.isIntersecting && aboveHeader);
    }, { rootMargin: '-112px 0px 0px 0px', threshold: 0 });
    observer.observe(anchor.current);
    return () => { resize.disconnect(); observer.disconnect(); };
  }, [docked]);

  useEffect(() => { if (!docked) setExpanded(false); }, [docked]);
  return { anchor, form, docked, height, expanded, setExpanded };
}
