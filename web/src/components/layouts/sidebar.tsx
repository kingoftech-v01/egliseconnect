'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Home, Users, Heart, Calendar, HandHelping,
  Mail, BarChart3, UserPlus, ClipboardCheck,
  CreditCard, Music, Settings, ChevronLeft,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/stores/auth';

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  roles?: string[];
}

const navigation: NavItem[] = [
  { label: 'Tableau de bord', href: '/', icon: Home },
  { label: 'Membres', href: '/members', icon: Users },
  { label: 'Dons', href: '/donations', icon: Heart, roles: ['treasurer', 'pastor', 'admin'] },
  { label: 'Événements', href: '/events', icon: Calendar },
  { label: 'Bénévoles', href: '/volunteers', icon: HandHelping },
  { label: 'Communication', href: '/communication', icon: Mail, roles: ['pastor', 'admin'] },
  { label: 'Demandes d\'aide', href: '/help-requests', icon: HandHelping },
  { label: 'Rapports', href: '/reports', icon: BarChart3, roles: ['treasurer', 'pastor', 'admin'] },
  { label: 'Intégration', href: '/onboarding', icon: UserPlus, roles: ['pastor', 'admin'] },
  { label: 'Présence', href: '/attendance', icon: ClipboardCheck },
  { label: 'Paiements', href: '/payments', icon: CreditCard, roles: ['treasurer', 'pastor', 'admin'] },
  { label: 'Culte', href: '/worship', icon: Music },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  mobileOpen?: boolean;
  isMobile?: boolean;
}

export function Sidebar({ collapsed, onToggle, mobileOpen, isMobile }: SidebarProps) {
  const pathname = usePathname();
  const member = useAuthStore((s) => s.member);
  const userRole = member?.role || 'member';

  const visibleItems = navigation.filter(
    (item) => !item.roles || item.roles.includes(userRole),
  );

  // On mobile: show/hide via translate. On desktop: collapse width.
  const isVisible = isMobile ? mobileOpen : true;

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 z-50 h-screen transition-all duration-300',
        'bg-white/[0.03] backdrop-blur-xl border-r border-white/[0.08]',
        isMobile
          ? cn('w-64', isVisible ? 'translate-x-0' : '-translate-x-full')
          : collapsed ? 'w-16' : 'w-64',
      )}
    >
      <div className="flex h-16 items-center justify-between px-4 border-b border-white/[0.08]">
        {(!collapsed || isMobile) && (
          <Link href="/" className="text-lg font-bold bg-gradient-to-r from-purple-400 to-violet-300 bg-clip-text text-transparent">
            ÉgliseConnect
          </Link>
        )}
        <button
          onClick={onToggle}
          className="p-1.5 rounded-lg hover:bg-white/[0.06] text-white/50 transition-colors"
        >
          <ChevronLeft
            className={cn('h-5 w-5 transition-transform', !isMobile && collapsed && 'rotate-180')}
          />
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto py-4 px-2">
        <ul className="space-y-1">
          {visibleItems.map((item) => {
            const isActive =
              pathname === item.href ||
              (item.href !== '/' && pathname.startsWith(item.href));

            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  onClick={() => { if (isMobile) onToggle(); }}
                  className={cn(
                    'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-all duration-200',
                    isActive
                      ? 'bg-primary/20 text-purple-300 font-medium shadow-[0_0_15px_rgba(124,58,237,0.15)]'
                      : 'text-white/60 hover:bg-white/[0.06] hover:text-white/80',
                    !isMobile && collapsed && 'justify-center px-2',
                  )}
                  title={!isMobile && collapsed ? item.label : undefined}
                >
                  <item.icon className={cn('h-5 w-5 shrink-0', isActive && 'text-purple-400')} />
                  {(isMobile || !collapsed) && <span>{item.label}</span>}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="border-t border-white/[0.08] p-2">
        <Link
          href="/settings"
          onClick={() => { if (isMobile) onToggle(); }}
          className={cn(
            'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-white/60 hover:bg-white/[0.06] hover:text-white/80 transition-all duration-200',
            !isMobile && collapsed && 'justify-center px-2',
          )}
          title={!isMobile && collapsed ? 'Parametres' : undefined}
        >
          <Settings className="h-5 w-5 shrink-0" />
          {(isMobile || !collapsed) && <span>Parametres</span>}
        </Link>
      </div>
    </aside>
  );
}
