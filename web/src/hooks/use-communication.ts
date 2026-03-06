'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useInfiniteList } from './use-infinite-list';
import type { PaginatedResponse } from '@egliseconnect/types';

// ─── Newsletter Queries ─────────────────────────────────────────────────────

export function useNewsletters(params?: string) {
  return useQuery({
    queryKey: ['communication', 'newsletters', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/communication/newsletters/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useNewsletter(id: string) {
  return useQuery({
    queryKey: ['communication', 'newsletters', id],
    queryFn: () => api.get<unknown>(`/api/v2/communication/newsletters/${id}/`),
    enabled: !!id,
  });
}

// ─── Newsletter Mutations ───────────────────────────────────────────────────

export function useCreateNewsletter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/communication/newsletters/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['communication', 'newsletters'] });
    },
  });
}

export function useSendNewsletter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api.post(`/api/v2/communication/newsletters/${id}/send/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['communication', 'newsletters'] });
    },
  });
}

// ─── Notification Queries ───────────────────────────────────────────────────

export function useNotifications(params?: string) {
  return useQuery({
    queryKey: ['communication', 'notifications', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/communication/notifications/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useUnreadCount() {
  return useQuery({
    queryKey: ['communication', 'notifications', 'unread-count'],
    queryFn: () =>
      api.get<{ count: number }>('/api/v2/communication/notifications/unread_count/'),
    refetchInterval: 30000, // Poll every 30 seconds
  });
}

// ─── Notification Mutations ─────────────────────────────────────────────────

export function useMarkNotificationRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api.post('/api/v2/communication/notifications/mark-read/', { notification_ids: [id] }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['communication', 'notifications'] });
    },
  });
}

// ─── Direct Messages Queries ────────────────────────────────────────────────

export function useDirectMessages(params?: string) {
  return useQuery({
    queryKey: ['communication', 'direct-messages', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/communication/direct-messages/${params ? `?${params}` : ''}`,
      ),
  });
}

// ─── Direct Messages Mutations ──────────────────────────────────────────────

export function useCreateDirectMessage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/communication/direct-messages/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['communication', 'direct-messages'] });
    },
  });
}

// ─── Email Templates Queries ────────────────────────────────────────────────

export function useEmailTemplates(params?: string) {
  return useQuery({
    queryKey: ['communication', 'templates', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/communication/email-templates/${params ? `?${params}` : ''}`,
      ),
  });
}

// ─── SMS Queries ─────────────────────────────────────────────────────────────

export function useSmsMessages(params?: string) {
  return useQuery({
    queryKey: ['communication', 'sms', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/communication/sms/${params ? `?${params}` : ''}`,
      ),
  });
}

// ─── SMS Mutations ────────────────────────────────────────────────────────────

export function useSendSms() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/communication/sms/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['communication', 'sms'] });
    },
  });
}

// ─── Email Template Mutations ────────────────────────────────────────────────

export function useCreateEmailTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/communication/email-templates/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['communication', 'templates'] });
    },
  });
}

// ─── Automations Queries ────────────────────────────────────────────────────

export function useAutomations(params?: string) {
  return useQuery({
    queryKey: ['communication', 'automations', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/communication/automations/${params ? `?${params}` : ''}`,
      ),
  });
}

// ─── Automations Mutations ────────────────────────────────────────────────────

export function useCreateAutomation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/communication/automations/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['communication', 'automations'] });
    },
  });
}

// ─── Infinite Scroll Queries ─────────────────────────────────────────────────

export function useInfiniteNewsletters(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['communication', 'newsletters', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/communication/newsletters/?${params}`,
      ),
    search,
    filters,
  });
}

export function useInfiniteNotifications(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['communication', 'notifications', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/communication/notifications/?${params}`,
      ),
    search,
    filters,
  });
}

export function useInfiniteDirectMessages(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['communication', 'direct-messages', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/communication/direct-messages/?${params}`,
      ),
    search,
    filters,
  });
}

export function useInfiniteSmsMessages(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['communication', 'sms', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/communication/sms/?${params}`,
      ),
    search,
    filters,
  });
}

export function useInfiniteEmailTemplates(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['communication', 'templates', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/communication/email-templates/?${params}`,
      ),
    search,
    filters,
  });
}

export function useInfiniteAutomations(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['communication', 'automations', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/communication/automations/?${params}`,
      ),
    search,
    filters,
  });
}

// ─── Group Chats ───────────────────────────────────────────────────────────

export function useInfiniteGroupChats(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['communication', 'group-chats', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/communication/group-chats/?${params}`),
    search,
    filters,
  });
}

export function useCreateGroupChat() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/communication/group-chats/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['communication', 'group-chats'] });
    },
  });
}

// ─── A/B Tests ─────────────────────────────────────────────────────────────

export function useInfiniteABTests(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['communication', 'ab-tests', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/communication/ab-tests/?${params}`),
    search,
    filters,
  });
}

export function useCreateABTest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/communication/ab-tests/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['communication', 'ab-tests'] });
    },
  });
}

export function usePickABTestWinner() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api.post(`/api/v2/communication/ab-tests/${id}/pick-winner/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['communication', 'ab-tests'] });
    },
  });
}

// ─── SMS Templates ─────────────────────────────────────────────────────────

export function useInfiniteSmsTemplates(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['communication', 'sms-templates', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/communication/sms-templates/?${params}`),
    search,
    filters,
  });
}

export function useCreateSmsTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/communication/sms-templates/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['communication', 'sms-templates'] });
    },
  });
}

// ─── Push Subscriptions ────────────────────────────────────────────────────

export function usePushSubscriptions(params?: string) {
  return useQuery({
    queryKey: ['communication', 'push', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/communication/push-subscriptions/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useTestPushNotification() {
  return useMutation({
    mutationFn: (subscriptionId: string) =>
      api.post(`/api/v2/communication/push-subscriptions/${subscriptionId}/test-send/`),
  });
}

// ─── Automation Trigger ────────────────────────────────────────────────────

export function useTriggerAutomation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, memberId }: { id: string; memberId: string }) =>
      api.post(`/api/v2/communication/automations/${id}/trigger/`, { member: memberId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['communication', 'automations'] });
    },
  });
}

// ─── Schedule Newsletter ───────────────────────────────────────────────────

export function useScheduleNewsletter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, scheduledDate }: { id: string; scheduledDate: string }) =>
      api.post(`/api/v2/communication/newsletters/${id}/schedule/`, { scheduled_date: scheduledDate }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['communication', 'newsletters'] });
    },
  });
}
