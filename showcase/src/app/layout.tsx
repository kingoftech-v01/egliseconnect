import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'ÉgliseConnect — Système de gestion d\'église intelligent',
  description:
    'Plateforme complète de gestion d\'église avec IA intégrée. Membres, dons, événements, bénévoles, communication, présences et plus encore.',
  keywords: 'gestion église, church management, logiciel église, ChMS, SaaS, Canada, Québec',
  openGraph: {
    title: 'ÉgliseConnect — Gestion d\'église intelligente',
    description: 'Plateforme tout-en-un pour gérer votre église avec l\'intelligence artificielle.',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr-CA">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
