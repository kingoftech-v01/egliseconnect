'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useInfiniteList } from './use-infinite-list';
import type { PaginatedResponse, DonationListItem, Donation, DonationCreateRequest } from '@egliseconnect/types';

// ─── Donations ──────────────────────────────────────────────────────────────

export function useDonations(params?: string) {
  return useQuery({
    queryKey: ['donations', params],
    queryFn: () => api.donations.list(params) as Promise<PaginatedResponse<DonationListItem>>,
  });
}

export function useInfiniteDonations(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<DonationListItem>({
    queryKey: ['donations', 'infinite'],
    fetchFn: (params) => api.donations.list(params) as Promise<PaginatedResponse<DonationListItem>>,
    search,
    filters,
  });
}

export function useDonation(id: string) {
  return useQuery({
    queryKey: ['donations', id],
    queryFn: () => api.donations.get(id) as Promise<Donation>,
    enabled: !!id,
  });
}

export function useCreateDonation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: DonationCreateRequest) => api.donations.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['donations'] });
    },
  });
}

export function useUpdateDonation(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<DonationCreateRequest>) => api.donations.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['donations'] });
      queryClient.invalidateQueries({ queryKey: ['donations', id] });
    },
  });
}

export function useDeleteDonation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.donations.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['donations'] });
    },
  });
}

// ─── Campaigns ──────────────────────────────────────────────────────────────

export function useDonationCampaigns(params?: string) {
  return useQuery({
    queryKey: ['donations', 'campaigns', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/donations/campaigns/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useInfiniteDonationCampaigns(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['donations', 'campaigns', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/donations/campaigns/?${params}`),
    search,
    filters,
  });
}

export function useCreateDonationCampaign() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/donations/campaigns/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['donations', 'campaigns'] });
    },
  });
}

// ─── Pledges ────────────────────────────────────────────────────────────────

export function useInfinitePledges(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['donations', 'pledges', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/donations/pledges/?${params}`),
    search,
    filters,
  });
}

export function useCreatePledge() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/donations/pledges/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['donations', 'pledges'] });
    },
  });
}

// ─── Tax Receipts ───────────────────────────────────────────────────────────

export function useInfiniteTaxReceipts(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['donations', 'receipts', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/donations/receipts/?${params}`),
    search,
    filters,
  });
}

export function useGenerateTaxReceipts() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { year: number }) =>
      api.post('/api/v2/donations/receipts/generate/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['donations', 'receipts'] });
    },
  });
}

// ─── Giving Statements ──────────────────────────────────────────────────────

export function useInfiniteDonationStatements(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['donations', 'statements', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/donations/statements/?${params}`),
    search,
    filters,
  });
}

export function useGenerateDonationStatements() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { year: number }) =>
      api.post('/api/v2/donations/statements/generate/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['donations', 'statements'] });
    },
  });
}

// ─── Analytics ──────────────────────────────────────────────────────────────

export function useDonationAnalytics(params?: string) {
  return useQuery({
    queryKey: ['donations', 'analytics', params],
    queryFn: () =>
      api.get<unknown>(
        `/api/v2/donations/analytics/dashboard/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useDonationTrends(params?: string) {
  return useQuery({
    queryKey: ['donations', 'analytics', 'trends', params],
    queryFn: () =>
      api.get<unknown>(
        `/api/v2/donations/analytics/trends/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useTopDonors(params?: string) {
  return useQuery({
    queryKey: ['donations', 'analytics', 'top-donors', params],
    queryFn: () =>
      api.get<unknown>(
        `/api/v2/donations/analytics/top_donors/${params ? `?${params}` : ''}`,
      ),
  });
}
