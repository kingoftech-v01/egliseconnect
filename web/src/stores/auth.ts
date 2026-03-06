/** Zustand auth store - manages JWT tokens and user state. */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { AuthUser, MemberProfile } from '@egliseconnect/types';

function setAuthCookie(authenticated: boolean) {
  if (typeof document === 'undefined') return;
  if (authenticated) {
    document.cookie = 'ec-auth=1; path=/; max-age=604800; SameSite=Lax';
  } else {
    document.cookie = 'ec-auth=; path=/; max-age=0';
  }
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: AuthUser | null;
  member: MemberProfile | null;
  isAuthenticated: boolean;

  setAuth: (data: {
    access: string;
    refresh: string;
    user: AuthUser;
    member: MemberProfile | null;
  }) => void;
  setTokens: (access: string, refresh: string | null) => void;
  setMember: (member: MemberProfile) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      member: null,
      isAuthenticated: false,

      setAuth: (data) => {
        setAuthCookie(true);
        set({
          accessToken: data.access,
          refreshToken: data.refresh,
          user: data.user,
          member: data.member,
          isAuthenticated: true,
        });
      },

      setTokens: (access, refresh) =>
        set((state) => ({
          accessToken: access,
          refreshToken: refresh ?? state.refreshToken,
        })),

      setMember: (member) => set({ member }),

      logout: () => {
        setAuthCookie(false);
        set({
          accessToken: null,
          refreshToken: null,
          user: null,
          member: null,
          isAuthenticated: false,
        });
      },
    }),
    {
      name: 'egliseconnect-auth',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        member: state.member,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
);
