import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useAuthStore } from '@/stores/auth';
import type { LoginRequest, RegisterRequest, MeResponse } from '@egliseconnect/types';

export function useLogin() {
  const { setTokens } = useAuthStore();
  return useMutation({
    mutationFn: (data: LoginRequest) => api.auth.login(data),
    onSuccess: (data) => {
      setTokens(data.access, data.refresh);
    },
  });
}

export function useRegister() {
  const { setTokens } = useAuthStore();
  return useMutation({
    mutationFn: (data: RegisterRequest) => api.auth.register(data),
    onSuccess: (data) => {
      setTokens(data.access, data.refresh);
    },
  });
}

export function useMe() {
  return useQuery<MeResponse>({
    queryKey: ['me'],
    queryFn: () => api.auth.me(),
  });
}

export function useUpdateMe() {
  return useMutation({
    mutationFn: (data: Parameters<typeof api.auth.updateMe>[0]) =>
      api.auth.updateMe(data),
  });
}
