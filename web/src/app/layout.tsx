import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from '@/components/providers';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'ÉgliseConnect',
  description: "Système de gestion d'église",
  manifest: '/manifest.json',
  themeColor: '#7c3aed',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'ÉgliseConnect',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr-CA" className="dark">
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
