'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { PaginatedResponse } from '@egliseconnect/types';

// ─── Church Branding ─────────────────────────────────────────────────────────

export function useChurchBranding() {
  return useQuery({
    queryKey: ['settings', 'branding'],
    queryFn: () =>
      api.get<PaginatedResponse<ChurchBranding>>('/api/v2/core/branding/'),
  });
}

export function useUpdateChurchBranding() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<ChurchBranding> }) =>
      api.patch(`/api/v2/core/branding/${id}/`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'branding'] });
    },
  });
}

export function useCreateChurchBranding() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<ChurchBranding>) =>
      api.post('/api/v2/core/branding/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'branding'] });
    },
  });
}

// ─── Profile (via /api/v2/auth/me/) ──────────────────────────────────────────

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.patch('/api/v2/auth/me/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
    },
  });
}

// ─── Password Change ─────────────────────────────────────────────────────────

export function useChangePassword() {
  return useMutation({
    mutationFn: (data: { current_password: string; new_password: string; new_password_confirm: string }) =>
      api.post('/api/v2/auth/change-password/', data),
  });
}

// ─── Notification Preferences ────────────────────────────────────────────────

export function useNotificationPreferences() {
  return useQuery({
    queryKey: ['settings', 'notification-preferences'],
    queryFn: () =>
      api.get<NotificationPreferences>('/api/v2/communication/preferences/me/'),
  });
}

export function useUpdateNotificationPreferences() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<NotificationPreferences>) =>
      api.patch('/api/v2/communication/preferences/me/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'notification-preferences'] });
    },
  });
}

// ─── Webhooks ────────────────────────────────────────────────────────────────

export function useWebhooks() {
  return useQuery({
    queryKey: ['settings', 'webhooks'],
    queryFn: () =>
      api.get<PaginatedResponse<WebhookEndpoint>>('/api/v2/core/webhooks/'),
  });
}

export function useCreateWebhook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<WebhookEndpoint>) =>
      api.post('/api/v2/core/webhooks/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'webhooks'] });
    },
  });
}

export function useDeleteWebhook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/api/v2/core/webhooks/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'webhooks'] });
    },
  });
}

// ─── Webhook Update & Deliveries ────────────────────────────────────────────

export function useUpdateWebhook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<WebhookEndpoint> }) =>
      api.patch(`/api/v2/core/webhooks/${id}/`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'webhooks'] });
    },
  });
}

export function useWebhookDeliveries(webhookId: string) {
  return useQuery({
    queryKey: ['settings', 'webhooks', webhookId, 'deliveries'],
    queryFn: () =>
      api.get<PaginatedResponse<WebhookDelivery>>(`/api/v2/core/webhooks/${webhookId}/deliveries/`),
    enabled: !!webhookId,
  });
}

// ─── Campuses ───────────────────────────────────────────────────────────────

export function useCampuses(params?: string) {
  return useQuery({
    queryKey: ['settings', 'campuses', params],
    queryFn: () =>
      api.get<PaginatedResponse<Campus>>(`/api/v2/core/campuses/${params ? `?${params}` : ''}`),
  });
}

export function useCreateCampus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Campus>) =>
      api.post('/api/v2/core/campuses/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'campuses'] });
    },
  });
}

export function useUpdateCampus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Campus> }) =>
      api.patch(`/api/v2/core/campuses/${id}/`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'campuses'] });
    },
  });
}

export function useDeleteCampus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/api/v2/core/campuses/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'campuses'] });
    },
  });
}

// ─── Audit Logs ─────────────────────────────────────────────────────────────

export function useAuditLogs(params?: string) {
  return useQuery({
    queryKey: ['settings', 'audit-logs', params],
    queryFn: () =>
      api.get<PaginatedResponse<AuditLog>>(`/api/v2/core/audit-logs/${params ? `?${params}` : ''}`),
  });
}

// ─── Login Audits ───────────────────────────────────────────────────────────

export function useLoginAudits(params?: string) {
  return useQuery({
    queryKey: ['settings', 'login-audits', params],
    queryFn: () =>
      api.get<PaginatedResponse<LoginAudit>>(`/api/v2/audit/login-audits/${params ? `?${params}` : ''}`),
  });
}

// ─── Global Search ──────────────────────────────────────────────────────────

export function useGlobalSearch(query: string) {
  return useQuery({
    queryKey: ['search', query],
    queryFn: () =>
      api.get<SearchResults>(`/api/v2/core/search/?q=${encodeURIComponent(query)}`),
    enabled: query.length >= 2,
  });
}

// ─── Types ───────────────────────────────────────────────────────────────────

export interface ChurchBranding {
  id: string;
  church_name: string;
  logo: string | null;
  favicon: string | null;
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  address: string;
  phone: string;
  email: string;
  website: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface NotificationPreferences {
  email_newsletter: boolean;
  email_events: boolean;
  email_birthdays: boolean;
  push_enabled: boolean;
  sms_enabled: boolean;
}

export interface WebhookEndpoint {
  id: string;
  name: string;
  url: string;
  secret?: string;
  events: string[];
  headers: Record<string, string>;
  max_retries: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface WebhookDelivery {
  id: string;
  event: string;
  payload: Record<string, unknown>;
  status: string;
  response_code: number | null;
  response_body: string;
  attempts: number;
  last_attempt_at: string;
  error_message: string;
}

export interface Campus {
  id: string;
  name: string;
  address: string;
  city: string;
  province: string;
  postal_code: string;
  phone: string;
  email: string;
  pastor?: string;
  is_main: boolean;
  is_active: boolean;
}

export interface AuditLog {
  id: string;
  user: string;
  username: string;
  action: string;
  action_display: string;
  model_name: string;
  object_id: string;
  object_repr: string;
  changes: Record<string, unknown>;
  ip_address: string;
  created_at: string;
}

export interface LoginAudit {
  id: string;
  user: string | null;
  username: string;
  email_attempted: string;
  ip_address: string;
  user_agent: string;
  success: boolean;
  failure_reason: string;
  method: string;
  created_at: string;
}

export interface SearchResults {
  total_count: number;
  results: {
    category: string;
    items: { id: string; name: string; url?: string }[];
  }[];
}
