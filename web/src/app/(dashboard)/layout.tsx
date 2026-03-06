'use client';

import { useState, useEffect } from 'react';
import { Sidebar } from '@/components/layouts/sidebar';
import { Header } from '@/components/layouts/header';
import { AuthGuard } from '@/components/layouts/auth-guard';
import { cn } from '@/lib/utils';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const mql = window.matchMedia('(max-width: 1023px)');
    const onChange = (e: MediaQueryListEvent | MediaQueryList) => {
      setIsMobile(e.matches);
      if (e.matches) setSidebarOpen(false);
    };
    onChange(mql);
    mql.addEventListener('change', onChange);
    return () => mql.removeEventListener('change', onChange);
  }, []);

  return (
    <AuthGuard>
      <div className="min-h-screen relative">
        {/* Gradient background */}
        <div className="fixed inset-0 bg-gradient-to-br from-[#0f0a2e] via-[#1a1145] to-[#2d1b69]" />

        {/* Animated gradient orbs for visual depth */}
        <div className="fixed top-[-20%] left-[-10%] w-[500px] h-[500px] rounded-full bg-purple-600/20 blur-[120px] pointer-events-none" />
        <div className="fixed bottom-[-20%] right-[-10%] w-[400px] h-[400px] rounded-full bg-indigo-600/15 blur-[100px] pointer-events-none" />
        <div className="fixed top-[40%] right-[20%] w-[300px] h-[300px] rounded-full bg-violet-500/10 blur-[80px] pointer-events-none" />

        {/* Mobile overlay */}
        {isMobile && sidebarOpen && (
          <div
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Content */}
        <div className="relative z-10">
          <Sidebar
            collapsed={!isMobile && sidebarCollapsed}
            onToggle={() => {
              if (isMobile) {
                setSidebarOpen(false);
              } else {
                setSidebarCollapsed(!sidebarCollapsed);
              }
            }}
            mobileOpen={sidebarOpen}
            isMobile={isMobile}
          />
          <div
            className={cn(
              'transition-all duration-300',
              isMobile
                ? 'ml-0'
                : sidebarCollapsed
                  ? 'ml-16'
                  : 'ml-64',
            )}
          >
            <Header onMenuToggle={() => setSidebarOpen(!sidebarOpen)} isMobile={isMobile} />
            <main className="p-4 sm:p-6">{children}</main>
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
