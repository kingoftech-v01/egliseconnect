'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useAuthStore } from '@/stores/auth';
import type { LoginRequest, RegisterRequest } from '@egliseconnect/types';

export function useLogin() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);

  return useMutation({
    mutationFn: (data: LoginRequest) => api.auth.login(data),
    onSuccess: (data) => {
      setAuth(data);
      router.push('/');
    },
  });
}

export function useRegister() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);

  return useMutation({
    mutationFn: (data: RegisterRequest) => api.auth.register(data),
    onSuccess: (data) => {
      setAuth(data);
      router.push('/');
    },
  });
}

export function useLogout() {
  const router = useRouter();
  const { refreshToken, logout } = useAuthStore();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => {
      if (refreshToken) {
        return api.auth.logout({ refresh: refreshToken });
      }
      return Promise.resolve();
    },
    onSettled: () => {
      logout();
      queryClient.clear();
      router.push('/login');
    },
  });
}

export function useForgotPassword() {
  return useMutation({
    mutationFn: (data: { email: string }) =>
      api.post('/api/v2/auth/forgot-password/', data),
  });
}

export function useResetPassword() {
  return useMutation({
    mutationFn: (data: { uid: string; token: string; new_password: string; new_password_confirm: string }) =>
      api.post('/api/v2/auth/reset-password/', data),
  });
}

export function useMe() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const setMember = useAuthStore((s) => s.setMember);

  return useQuery({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      const data = await api.auth.me();
      if (data.member) {
        setMember(data.member);
      }
      return data;
    },
    enabled: isAuthenticated,
  });
}
