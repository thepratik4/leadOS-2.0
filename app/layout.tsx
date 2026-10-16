import type {Metadata} from 'next';
import './globals.css'; // Global styles

export const metadata: Metadata = {
  title: 'LeadOS 2.0 | Evidence-First B2B Prospecting Platform',
  description: 'Discover relevant companies, verify buying signals against primary source evidence, and inspect deterministic lead scores.',
  openGraph: {
    title: 'LeadOS 2.0 | Evidence-First B2B Prospecting Platform',
    description: 'Discover relevant companies, verify buying signals against primary source evidence, and inspect deterministic lead scores.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'LeadOS | Evidence-First B2B Prospecting Platform',
    description: 'Discover relevant companies, verify buying signals against primary source evidence, and inspect deterministic lead scores.',
  },
};

export default function RootLayout({children}: {children: React.ReactNode}) {
  return (
    <html lang="en">
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
