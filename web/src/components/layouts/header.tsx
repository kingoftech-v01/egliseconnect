'use client';

import { Bell, Search, LogOut, User, Menu } from 'lucide-react';
import { Avatar } from '@/components/ui/avatar';
import { useAuthStore } from '@/stores/auth';
import { useLogout } from '@/hooks/use-auth';
import { useState, useRef, useEffect } from 'react';

interface HeaderProps {
  onMenuToggle?: () => void;
  isMobile?: boolean;
}

export function Header({ onMenuToggle, isMobile }: HeaderProps) {
  const member = useAuthStore((s) => s.member);
  const user = useAuthStore((s) => s.user);
  const { mutate: logout } = useLogout();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between bg-white/[0.03] backdrop-blur-xl border-b border-white/[0.08] px-4 sm:px-6">
      <div className="flex items-center gap-3 flex-1">
        {isMobile && (
          <button
            onClick={onMenuToggle}
            className="p-2 rounded-xl hover:bg-white/[0.06] text-white/50 transition-colors"
          >
            <Menu className="h-5 w-5" />
          </button>
        )}
        <div className="relative max-w-md flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
          <input
            type="search"
            placeholder="Rechercher..."
            className="h-9 w-full rounded-xl bg-white/[0.06] border border-white/[0.08] pl-9 pr-4 text-sm text-white/90 placeholder:text-white/30 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/30 transition-all"
          />
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        <button className="relative p-2 rounded-xl hover:bg-white/[0.06] text-white/50 transition-colors">
          <Bell className="h-5 w-5" />
          <span className="absolute -top-0.5 -right-0.5 h-4 w-4 rounded-full bg-primary text-[10px] font-bold text-white flex items-center justify-center shadow-[0_0_10px_rgba(124,58,237,0.5)]">
            3
          </span>
        </button>

        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="flex items-center gap-2 rounded-xl p-1.5 hover:bg-white/[0.06] transition-colors"
          >
            <Avatar
              src={member?.photo}
              fallback={member?.full_name || user?.email || '?'}
              size="sm"
            />
            <span className="text-sm font-medium text-white/80 hidden md:block">
              {member?.full_name || user?.email}
            </span>
          </button>

          {menuOpen && (
            <div className="absolute right-0 mt-2 w-48 rounded-xl bg-white/[0.08] backdrop-blur-xl border border-white/[0.1] shadow-2xl py-1 z-50">
              <a
                href="/settings/profile"
                className="flex items-center gap-2 px-4 py-2.5 text-sm text-white/80 hover:bg-white/[0.06] transition-colors"
              >
                <User className="h-4 w-4" />
                Mon profil
              </a>
              <button
                onClick={() => logout()}
                className="flex items-center gap-2 px-4 py-2.5 text-sm text-rose-400 hover:bg-white/[0.06] w-full text-left transition-colors"
              >
                <LogOut className="h-4 w-4" />
                Deconnexion
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
