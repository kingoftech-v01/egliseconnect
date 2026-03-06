'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useInfiniteList } from './use-infinite-list';
import type { PaginatedResponse } from '@egliseconnect/types';

// ─── Help Request Queries ───────────────────────────────────────────────────

export function useHelpRequests(params?: string) {
  return useQuery({
    queryKey: ['help-requests', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/help-requests/requests/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useHelpRequest(id: string) {
  return useQuery({
    queryKey: ['help-requests', id],
    queryFn: () => api.get<unknown>(`/api/v2/help-requests/requests/${id}/`),
    enabled: !!id,
  });
}

export function useMyHelpRequests(params?: string) {
  return useQuery({
    queryKey: ['help-requests', 'mine', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/help-requests/requests/my_requests/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useHelpRequestCategories() {
  return useQuery({
    queryKey: ['help-requests', 'categories'],
    queryFn: () =>
      api.get<unknown[]>('/api/v2/help-requests/categories/'),
    staleTime: 5 * 60 * 1000,
  });
}

// ─── Help Request Mutations ─────────────────────────────────────────────────

export function useCreateHelpRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/help-requests/requests/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['help-requests'] });
    },
  });
}

export function useAssignHelpRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, assigneeId }: { id: string; assigneeId: string }) =>
      api.post(`/api/v2/help-requests/requests/${id}/assign/`, { assignee_id: assigneeId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['help-requests'] });
    },
  });
}

export function useResolveHelpRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, resolution }: { id: string; resolution?: string }) =>
      api.post(`/api/v2/help-requests/requests/${id}/resolve/`, { resolution }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['help-requests'] });
    },
  });
}

export function useCommentHelpRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, comment }: { id: string; comment: string }) =>
      api.post(`/api/v2/help-requests/requests/${id}/comment/`, { comment }),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['help-requests', variables.id] });
    },
  });
}

// ─── Prayer Requests ────────────────────────────────────────────────────────

export function usePrayerRequests(params?: string) {
  return useQuery({
    queryKey: ['help-requests', 'prayer-requests', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/help-requests/prayer-requests/${params ? `?${params}` : ''}`,
      ),
  });
}

export function usePrayerWall(params?: string) {
  return useQuery({
    queryKey: ['help-requests', 'prayer-wall', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/help-requests/prayer-requests/wall/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useCreatePrayerRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/help-requests/prayer-requests/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['help-requests', 'prayer-requests'] });
      queryClient.invalidateQueries({ queryKey: ['help-requests', 'prayer-wall'] });
    },
  });
}

// ─── Pastoral Care ──────────────────────────────────────────────────────────

export function useCreatePastoralCare() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/help-requests/pastoral-care/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['help-requests', 'pastoral-care'] });
    },
  });
}

export function usePastoralCare(params?: string) {
  return useQuery({
    queryKey: ['help-requests', 'pastoral-care', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/help-requests/pastoral-care/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useCareTeams(params?: string) {
  return useQuery({
    queryKey: ['help-requests', 'care-teams', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/help-requests/care-teams/${params ? `?${params}` : ''}`,
      ),
  });
}

// ─── Benevolence ────────────────────────────────────────────────────────────

export function useCreateBenevolenceRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/help-requests/benevolence-requests/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['help-requests', 'benevolence', 'requests'] });
    },
  });
}

export function useBenevolenceFunds(params?: string) {
  return useQuery({
    queryKey: ['help-requests', 'benevolence', 'funds', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/help-requests/benevolence-funds/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useBenevolenceRequests(params?: string) {
  return useQuery({
    queryKey: ['help-requests', 'benevolence', 'requests', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/help-requests/benevolence-requests/${params ? `?${params}` : ''}`,
      ),
  });
}

// ─── Meal Trains ────────────────────────────────────────────────────────────

export function useMealTrainSignup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (trainId: string) =>
      api.post(`/api/v2/help-requests/meal-trains/${trainId}/signup/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['help-requests', 'meal-trains'] });
    },
  });
}

export function useMealTrains(params?: string) {
  return useQuery({
    queryKey: ['help-requests', 'meal-trains', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/help-requests/meal-trains/${params ? `?${params}` : ''}`,
      ),
  });
}

// ─── Infinite Scroll Queries ─────────────────────────────────────────────────

export function useInfiniteHelpRequests(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['help-requests', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/help-requests/requests/?${params}`),
    search,
    filters,
  });
}

export function useInfinitePrayerRequests(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['help-requests', 'prayer-requests', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/help-requests/prayer-requests/?${params}`),
    search,
    filters,
  });
}

export function useInfinitePrayerWall(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['help-requests', 'prayer-wall', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/help-requests/prayer-requests/wall/?${params}`),
    search,
    filters,
  });
}

export function useInfinitePastoralCare(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['help-requests', 'pastoral-care', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/help-requests/pastoral-care/?${params}`),
    search,
    filters,
  });
}

export function useInfiniteCareTeams(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['help-requests', 'care-teams', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/help-requests/care-teams/?${params}`),
    search,
    filters,
  });
}

export function useInfiniteBenevolenceFunds(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['help-requests', 'benevolence', 'funds', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/help-requests/benevolence-funds/?${params}`),
    search,
    filters,
  });
}

export function useInfiniteBenevolenceRequests(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['help-requests', 'benevolence', 'requests', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/help-requests/benevolence-requests/?${params}`),
    search,
    filters,
  });
}

export function useInfiniteMealTrains(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['help-requests', 'meal-trains', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/help-requests/meal-trains/?${params}`),
    search,
    filters,
  });
}
