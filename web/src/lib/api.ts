/** Singleton API client configured for the web app. */
import { ApiClient } from '@egliseconnect/api-client';
import { useAuthStore } from '@/stores/auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

export const api = new ApiClient({
  baseUrl: API_BASE_URL,
  getAccessToken: () => useAuthStore.getState().accessToken,
  getRefreshToken: () => useAuthStore.getState().refreshToken,
  onTokenRefreshed: (access, refresh) => {
    useAuthStore.getState().setTokens(access, refresh || null);
  },
  onAuthError: () => {
    useAuthStore.getState().logout();
  },
});
