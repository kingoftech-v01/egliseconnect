'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useInfiniteList } from './use-infinite-list';
import type { PaginatedResponse } from '@egliseconnect/types';

// ─── Worship Services ───────────────────────────────────────────────────────

export function useWorshipServices(params?: string) {
  return useQuery({
    queryKey: ['worship', 'services', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/worship/services/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useWorshipService(id: string) {
  return useQuery({
    queryKey: ['worship', 'services', id],
    queryFn: () => api.get<unknown>(`/api/v2/worship/services/${id}/`),
    enabled: !!id,
  });
}

export function useCreateWorshipService() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/worship/services/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['worship', 'services'] });
    },
  });
}

// ─── Service Sections ───────────────────────────────────────────────────────

export function useServiceSections(serviceId: string, params?: string) {
  return useQuery({
    queryKey: ['worship', 'sections', serviceId, params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/worship/sections/${params ? `?${params}` : ''}`,
      ),
    enabled: !!serviceId,
  });
}

export function useCreateSection(serviceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/worship/sections/', { ...data, service: serviceId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['worship', 'sections', serviceId] });
      queryClient.invalidateQueries({ queryKey: ['worship', 'services', serviceId] });
    },
  });
}

// ─── Assignments ────────────────────────────────────────────────────────────

export function useAssignments(params?: string) {
  return useQuery({
    queryKey: ['worship', 'assignments', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/worship/assignments/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useMyAssignments(params?: string) {
  return useQuery({
    queryKey: ['worship', 'assignments', 'mine', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/worship/assignments/my-assignments/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useConfirmAssignment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api.post(`/api/v2/worship/assignments/${id}/confirm/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['worship', 'assignments'] });
    },
  });
}

export function useDeclineAssignment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) =>
      api.post(`/api/v2/worship/assignments/${id}/decline/`, { reason }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['worship', 'assignments'] });
    },
  });
}

// ─── Sermons ────────────────────────────────────────────────────────────────

export function useSermons(params?: string) {
  return useQuery({
    queryKey: ['worship', 'sermons', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/worship/sermons/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useSermon(id: string) {
  return useQuery({
    queryKey: ['worship', 'sermons', id],
    queryFn: () => api.get<unknown>(`/api/v2/worship/sermons/${id}/`),
    enabled: !!id,
  });
}

export function useCreateSermon() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/worship/sermons/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['worship', 'sermons'] });
    },
  });
}

// ─── Songs ──────────────────────────────────────────────────────────────────

export function useSongs(params?: string) {
  return useQuery({
    queryKey: ['worship', 'songs', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/worship/songs/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useSong(id: string) {
  return useQuery({
    queryKey: ['worship', 'songs', id],
    queryFn: () => api.get<unknown>(`/api/v2/worship/songs/${id}/`),
    enabled: !!id,
  });
}

export function useCreateSong() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/worship/songs/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['worship', 'songs'] });
    },
  });
}

// ─── Setlists ───────────────────────────────────────────────────────────────

export function useCreateSetlist() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/worship/setlists/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['worship', 'setlists'] });
    },
  });
}

export function useSetlists(params?: string) {
  return useQuery({
    queryKey: ['worship', 'setlists', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/worship/setlists/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useSetlist(id: string) {
  return useQuery({
    queryKey: ['worship', 'setlists', id],
    queryFn: () => api.get<unknown>(`/api/v2/worship/setlists/${id}/`),
    enabled: !!id,
  });
}

// ─── Rehearsals ─────────────────────────────────────────────────────────────

export function useCreateRehearsal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/worship/rehearsals/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['worship', 'rehearsals'] });
    },
  });
}

export function useRehearsalRSVP() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (rehearsalId: string) =>
      api.post(`/api/v2/worship/rehearsals/${rehearsalId}/rsvp/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['worship', 'rehearsals'] });
    },
  });
}

export function useRehearsals(params?: string) {
  return useQuery({
    queryKey: ['worship', 'rehearsals', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/worship/rehearsals/${params ? `?${params}` : ''}`,
      ),
  });
}

// ─── Song Requests ──────────────────────────────────────────────────────────

export function useSongRequests(params?: string) {
  return useQuery({
    queryKey: ['worship', 'song-requests', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/worship/song-requests/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useCreateSongRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/worship/song-requests/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['worship', 'song-requests'] });
    },
  });
}

// ─── Live Streams ───────────────────────────────────────────────────────────

export function useLiveStreams(params?: string) {
  return useQuery({
    queryKey: ['worship', 'live-streams', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/worship/livestreams/${params ? `?${params}` : ''}`,
      ),
  });
}

// ─── Infinite Scroll Queries ─────────────────────────────────────────────────

export function useInfiniteWorshipServices(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['worship', 'services', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/worship/services/?${params}`),
    search,
    filters,
  });
}

export function useInfiniteAssignments(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['worship', 'assignments', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/worship/assignments/?${params}`),
    search,
    filters,
  });
}

export function useInfiniteSermons(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['worship', 'sermons', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/worship/sermons/?${params}`),
    search,
    filters,
  });
}

export function useInfiniteSongs(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['worship', 'songs', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/worship/songs/?${params}`),
    search,
    filters,
  });
}

export function useInfiniteSetlists(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['worship', 'setlists', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/worship/setlists/?${params}`),
    search,
    filters,
  });
}

export function useInfiniteRehearsals(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['worship', 'rehearsals', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/worship/rehearsals/?${params}`),
    search,
    filters,
  });
}

export function useInfiniteSongRequests(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['worship', 'song-requests', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/worship/song-requests/?${params}`),
    search,
    filters,
  });
}

export function useInfiniteLiveStreams(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['worship', 'live-streams', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/worship/livestreams/?${params}`),
    search,
    filters,
  });
}

// ─── Sermon Series ─────────────────────────────────────────────────────────

export function useSermonSeries(params?: string) {
  return useQuery({
    queryKey: ['worship', 'sermon-series', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/worship/sermon-series/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useInfiniteSermonSeries(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['worship', 'sermon-series', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/worship/sermon-series/?${params}`),
    search,
    filters,
  });
}

export function useCreateSermonSeries() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/worship/sermon-series/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['worship', 'sermon-series'] });
    },
  });
}

// ─── Live Stream Mutations ─────────────────────────────────────────────────

export function useCreateLiveStream() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/worship/livestreams/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['worship', 'live-streams'] });
    },
  });
}

// ─── Eligible Member Lists ─────────────────────────────────────────────────

export function useInfiniteEligibleLists(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['worship', 'eligible-lists', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/worship/eligible-lists/?${params}`),
    search,
    filters,
  });
}

export function useCreateEligibleList() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/worship/eligible-lists/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['worship', 'eligible-lists'] });
    },
  });
}
