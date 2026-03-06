'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useInfiniteList } from './use-infinite-list';
import type { PaginatedResponse } from '@egliseconnect/types';

// ─── Session Queries ────────────────────────────────────────────────────────

export function useAttendanceSessions(params?: string) {
  return useQuery({
    queryKey: ['attendance', 'sessions', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/attendance/sessions/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useAttendanceSession(id: string) {
  return useQuery({
    queryKey: ['attendance', 'sessions', id],
    queryFn: () => api.get<unknown>(`/api/v2/attendance/sessions/${id}/`),
    enabled: !!id,
  });
}

// ─── Session Mutations ──────────────────────────────────────────────────────

export function useCreateSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/attendance/sessions/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendance', 'sessions'] });
    },
  });
}

// ─── Check-In / Check-Out ───────────────────────────────────────────────────

export function useCheckIn() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { session_id: string; member_id?: string; qr_code?: string }) =>
      api.post('/api/v2/attendance/checkin/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendance', 'sessions'] });
    },
  });
}

export function useCheckOut() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { session_id: string; member_id?: string }) =>
      api.post('/api/v2/attendance/checkout/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendance', 'sessions'] });
    },
  });
}

export function useFamilyCheckIn() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { session_id: string; family_id: string; member_ids: string[] }) =>
      api.post('/api/v2/attendance/family-checkin/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendance', 'sessions'] });
    },
  });
}

// ─── QR Code ────────────────────────────────────────────────────────────────

export function useMyQRCode() {
  return useQuery({
    queryKey: ['attendance', 'qr-code', 'mine'],
    queryFn: () => api.get<{ qr_code: string; expires_at: string }>('/api/v2/attendance/qr/'),
  });
}

export function useRegenerateQR() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post('/api/v2/attendance/qr/regenerate/'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendance', 'qr-code'] });
    },
  });
}

// ─── Absence Alerts ─────────────────────────────────────────────────────────

export function useAbsenceAlerts(params?: string) {
  return useQuery({
    queryKey: ['attendance', 'alerts', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/attendance/alerts/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (alertId: string) =>
      api.post(`/api/v2/attendance/alerts/${alertId}/acknowledge/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendance', 'alerts'] });
    },
  });
}

// ─── Visitors ───────────────────────────────────────────────────────────────

export function useVisitors(params?: string) {
  return useQuery({
    queryKey: ['attendance', 'visitors', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/attendance/visitors/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useCreateVisitor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/attendance/visitors/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendance', 'visitors'] });
    },
  });
}

// ─── Infinite Scroll Queries ─────────────────────────────────────────────────

export function useInfiniteAttendanceSessions(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['attendance', 'sessions', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/attendance/sessions/?${params}`),
    search,
    filters,
  });
}

export function useInfiniteAbsenceAlerts(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['attendance', 'alerts', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/attendance/alerts/?${params}`),
    search,
    filters,
  });
}

export function useInfiniteVisitors(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['attendance', 'visitors', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/attendance/visitors/?${params}`),
    search,
    filters,
  });
}

// ─── Recent Check-Ins ──────────────────────────────────────────────────────

export function useRecentCheckIns(sessionId?: string) {
  return useQuery({
    queryKey: ['attendance', 'recent-checkins', sessionId],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/attendance/records/${sessionId ? `?session=${sessionId}&` : '?'}ordering=-check_in_time&page_size=15`,
      ),
  });
}

// ─── Analytics ──────────────────────────────────────────────────────────────

export function useAttendanceTrends(params?: string) {
  return useQuery({
    queryKey: ['attendance', 'analytics', 'trends', params],
    queryFn: () =>
      api.get<unknown>(
        `/api/v2/attendance/analytics/trends/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useAttendanceAverageByType(params?: string) {
  return useQuery({
    queryKey: ['attendance', 'analytics', 'average-by-type', params],
    queryFn: () =>
      api.get<unknown>(
        `/api/v2/attendance/analytics/average_by_type/${params ? `?${params}` : ''}`,
      ),
  });
}

// ─── Analytics Growth & Predictions ────────────────────────────────────────

export function useAttendanceGrowth(params?: string) {
  return useQuery({
    queryKey: ['attendance', 'analytics', 'growth', params],
    queryFn: () =>
      api.get<unknown>(
        `/api/v2/attendance/analytics/growth/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useAttendancePrediction(params?: string) {
  return useQuery({
    queryKey: ['attendance', 'analytics', 'prediction', params],
    queryFn: () =>
      api.get<unknown>(
        `/api/v2/attendance/analytics/prediction/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useEngagementScore(memberId?: string) {
  return useQuery({
    queryKey: ['attendance', 'analytics', 'engagement', memberId],
    queryFn: () =>
      api.get<unknown>(
        `/api/v2/attendance/analytics/engagement_score/${memberId ? `?member=${memberId}` : ''}`,
      ),
    enabled: !!memberId,
  });
}

// ─── Child Check-In ────────────────────────────────────────────────────────

export function useInfiniteChildCheckIns(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['attendance', 'child-checkins', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/attendance/child-checkins/?${params}`),
    search,
    filters,
  });
}

export function useCreateChildCheckIn() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/attendance/child-checkins/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendance', 'child-checkins'] });
    },
  });
}

export function useChildCheckOut() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, securityCode }: { id: string; securityCode: string }) =>
      api.post(`/api/v2/attendance/child-checkins/${id}/checkout/`, { security_code: securityCode }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendance', 'child-checkins'] });
    },
  });
}

// ─── Geo-Fence ─────────────────────────────────────────────────────────────

export function useInfiniteGeoFences(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['attendance', 'geofences', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/attendance/geofences/?${params}`),
    search,
    filters,
  });
}

export function useCreateGeoFence() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/attendance/geofences/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendance', 'geofences'] });
    },
  });
}

// ─── NFC Tags ──────────────────────────────────────────────────────────────

export function useInfiniteNFCTags(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['attendance', 'nfc-tags', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/attendance/nfc-tags/?${params}`),
    search,
    filters,
  });
}

export function useCreateNFCTag() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/attendance/nfc-tags/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendance', 'nfc-tags'] });
    },
  });
}

// ─── Visitor Follow-Up ─────────────────────────────────────────────────────

export function useCompleteVisitorFollowUp() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api.post(`/api/v2/attendance/visitors/${id}/complete_followup/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendance', 'visitors'] });
    },
  });
}
