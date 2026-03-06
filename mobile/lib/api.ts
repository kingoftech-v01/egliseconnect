import { ApiClient } from '@egliseconnect/api-client';
import { useAuthStore } from '@/stores/auth';

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://10.0.2.2:8080';

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
