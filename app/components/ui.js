import { ArrowUpRight, LoaderCircle, Check } from 'lucide-react';

export function Icon({ as: Component, size = 18, ...props }) { return <Component aria-hidden="true" size={size} strokeWidth={2} {...props} />; }
export function Button({ children, className = '', variant = 'primary', ...props }) {
  return <button className={`button button-${variant} inline-flex min-h-11 items-center justify-center gap-2.5 rounded-lg px-5 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${className}`} {...props}>{children}</button>;
}
export function Spinner() { return <Icon as={LoaderCircle} className="spinner" />; }
export function ConsentCheckbox({ children, inputRef, ...props }) {
  return <label className="consent-row"><input ref={inputRef} type="checkbox" {...props} /><span className="consent-control" aria-hidden="true"><Icon as={Check} size={14} /></span><span className="consent-label">{children}</span></label>;
}
export function ExternalLink({ children, href, ...props }) { return <a href={href} target="_blank" rel="noopener noreferrer" {...props}>{children}<Icon as={ArrowUpRight} size={14} /></a>; }
export function Warning({ compact = false }) { return <div id="privacy-warning" className={`privacy-warning ${compact ? 'compact' : ''}`}><img src="/brand/warning.svg" alt="" width="20" height="20" /><span>Do not enter personal information.{!compact && <span className="warning-detail"> Use fictional, non-sensitive details only.</span>}</span></div>; }
