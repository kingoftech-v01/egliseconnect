'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useInfiniteList } from './use-infinite-list';
import type { PaginatedResponse } from '@egliseconnect/types';

// ─── Payment Queries ────────────────────────────────────────────────────────

export function usePayments(params?: string) {
  return useQuery({
    queryKey: ['payments', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/payments/payments/${params ? `?${params}` : ''}`,
      ),
  });
}

// ─── Payment Mutations ──────────────────────────────────────────────────────

export function useCreatePaymentIntent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { amount: number; currency?: string; donation_id?: string; metadata?: Record<string, unknown> }) =>
      api.post('/api/v2/payments/payments/create_intent/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payments'] });
      queryClient.invalidateQueries({ queryKey: ['donations'] });
    },
  });
}

// ─── Recurring Donations ────────────────────────────────────────────────────

export function useRecurringDonations(params?: string) {
  return useQuery({
    queryKey: ['payments', 'recurring', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/payments/recurring/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useCreateRecurring() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/payments/recurring/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payments', 'recurring'] });
    },
  });
}

export function useCancelRecurring() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api.post(`/api/v2/payments/recurring/${id}/cancel/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payments', 'recurring'] });
    },
  });
}

// ─── Giving Statements ──────────────────────────────────────────────────────

export function useGivingStatements(params?: string) {
  return useQuery({
    queryKey: ['payments', 'statements', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/payments/statements/${params ? `?${params}` : ''}`,
      ),
  });
}

// ─── Giving Goals ───────────────────────────────────────────────────────────

export function useGivingGoals(params?: string) {
  return useQuery({
    queryKey: ['payments', 'goals', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/payments/goals/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useCreateGivingGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/payments/goals/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payments', 'goals'] });
    },
  });
}

// ─── Payment Plans ──────────────────────────────────────────────────────────

export function useCreatePaymentPlan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/payments/plans/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payments', 'plans'] });
    },
  });
}

export function useGenerateStatement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { year: number }) =>
      api.post('/api/v2/payments/statements/generate/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payments', 'statements'] });
    },
  });
}

export function usePaymentPlans(params?: string) {
  return useQuery({
    queryKey: ['payments', 'plans', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/payments/plans/${params ? `?${params}` : ''}`,
      ),
  });
}

// ─── Giving Campaigns ───────────────────────────────────────────────────────

export function useGivingCampaigns(params?: string) {
  return useQuery({
    queryKey: ['payments', 'campaigns', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/payments/campaigns/${params ? `?${params}` : ''}`,
      ),
  });
}

// ─── Infinite Scroll Queries ─────────────────────────────────────────────────

export function useInfinitePayments(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['payments', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/payments/payments/?${params}`),
    search,
    filters,
  });
}

export function useInfiniteRecurringDonations(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['payments', 'recurring', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/payments/recurring/?${params}`),
    search,
    filters,
  });
}

export function useInfiniteGivingStatements(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['payments', 'statements', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/payments/statements/?${params}`),
    search,
    filters,
  });
}

export function useInfiniteGivingGoals(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['payments', 'goals', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/payments/goals/?${params}`),
    search,
    filters,
  });
}

export function useInfinitePaymentPlans(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['payments', 'plans', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/payments/plans/?${params}`),
    search,
    filters,
  });
}

export function useInfiniteGivingCampaigns(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['payments', 'campaigns', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/payments/campaigns/?${params}`),
    search,
    filters,
  });
}

// ─── Refund ──────────────────────────────────────────────────────────────────

export function useRefundPayment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api.post(`/api/v2/payments/payments/${id}/refund/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payments'] });
    },
  });
}

// ─── Update Recurring ────────────────────────────────────────────────────────

export function useUpdateRecurring() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
      api.post(`/api/v2/payments/recurring/${id}/update_subscription/`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payments', 'recurring'] });
    },
  });
}

// ─── Statement Email ─────────────────────────────────────────────────────────

export function useSendStatementEmail() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api.post(`/api/v2/payments/statements/${id}/send_email/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payments', 'statements'] });
    },
  });
}

// ─── Goal Progress & Summary ─────────────────────────────────────────────────

export function useGivingGoalProgress() {
  return useQuery({
    queryKey: ['payments', 'goals', 'progress'],
    queryFn: () => api.get<unknown>('/api/v2/payments/goals/progress/'),
  });
}

export function useGivingGoalSummary() {
  return useQuery({
    queryKey: ['payments', 'goals', 'summary'],
    queryFn: () => api.get<unknown>('/api/v2/payments/goals/summary/'),
  });
}

// ─── Complete Plan Early ─────────────────────────────────────────────────────

export function useCompletePlanEarly() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api.post(`/api/v2/payments/plans/${id}/complete_early/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payments', 'plans'] });
    },
  });
}

// ─── Employer Match ──────────────────────────────────────────────────────────

export function useEmployerMatches(params?: string) {
  return useQuery({
    queryKey: ['payments', 'employer-matches', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/payments/employer-matches/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useInfiniteEmployerMatches(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['payments', 'employer-matches', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/payments/employer-matches/?${params}`),
    search,
    filters,
  });
}

export function useCreateEmployerMatch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/payments/employer-matches/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payments', 'employer-matches'] });
    },
  });
}

// ─── SMS Donations ───────────────────────────────────────────────────────────

export function useInfiniteSMSDonations(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['payments', 'sms-donations', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/payments/sms-donations/?${params}`),
    search,
    filters,
  });
}

// ─── Kiosk Sessions ──────────────────────────────────────────────────────────

export function useInfiniteKioskSessions(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['payments', 'kiosk-sessions', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/payments/kiosk-sessions/?${params}`),
    search,
    filters,
  });
}

export function useReconcileKioskSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api.post(`/api/v2/payments/kiosk-sessions/${id}/reconcile/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payments', 'kiosk-sessions'] });
    },
  });
}
