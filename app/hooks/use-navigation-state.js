'use client';
import { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';

export function useNavigationState() {
  const pathname = usePathname();
  const [compact, setCompact] = useState(false);
  const [active, setActive] = useState('');

  useEffect(() => {
    let frame = 0;
    function update() {
      frame = 0;
      setCompact(previous => window.scrollY > (previous ? 32 : 64));
      const sections = ['search', 'how-it-works', 'learn', 'resources'];
      const current = sections.filter(id => {
        const element = document.getElementById(id);
        return element && element.getBoundingClientRect().top <= 180;
      }).at(-1);
      setActive(current === 'resources' ? 'learn' : current || '');
    }
    function schedule() { if (!frame) frame = requestAnimationFrame(update); }
    update();
    window.addEventListener('scroll', schedule, { passive: true });
    window.addEventListener('resize', schedule);
    return () => {
      window.removeEventListener('scroll', schedule);
      window.removeEventListener('resize', schedule);
      cancelAnimationFrame(frame);
    };
  }, [pathname]);
  return { compact, active, pathname };
}
