import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setTokens: (access: string, refresh: string | null) => void;
  logout: () => void;
  loadTokens: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: true,

  setTokens: (access, refresh) => {
    SecureStore.setItemAsync('access_token', access);
    if (refresh) SecureStore.setItemAsync('refresh_token', refresh);
    set({ accessToken: access, refreshToken: refresh, isAuthenticated: true });
  },

  logout: () => {
    SecureStore.deleteItemAsync('access_token');
    SecureStore.deleteItemAsync('refresh_token');
    set({ accessToken: null, refreshToken: null, isAuthenticated: false });
  },

  loadTokens: async () => {
    try {
      const access = await SecureStore.getItemAsync('access_token');
      const refresh = await SecureStore.getItemAsync('refresh_token');
      set({
        accessToken: access,
        refreshToken: refresh,
        isAuthenticated: !!access,
        isLoading: false,
      });
    } catch {
      set({ isLoading: false });
    }
  },
}));
