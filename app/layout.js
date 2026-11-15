import './globals.css';
import './website.css';
import './navigation.css';
import './composer.css';
import '@fontsource-variable/fredoka';
import '@fontsource-variable/hanken-grotesk';
import { ResearchSession } from './components/research-session';
import { SiteHeader, SiteFooter } from './components/site-shell';
import DisclosureBehavior from './components/disclosure-behavior';
export const metadata = { title: 'TrialAgent — Clinical research, clearer.', description: 'Explore clinical research records and prepare better questions. An educational research tool.', icons: { icon: '/brand/trialagent-mark.svg' } };
export default function RootLayout({ children }) { return <html lang="en" data-scroll-behavior="smooth"><body><ResearchSession><DisclosureBehavior key="coordinated-info-panels" /><a className="skip-link" href="#main-content">Skip to content</a><SiteHeader />{children}<SiteFooter /></ResearchSession></body></html>; }
