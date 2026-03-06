'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useInfiniteList } from './use-infinite-list';
import type { PaginatedResponse } from '@egliseconnect/types';

type DashboardSection = 'members' | 'donations' | 'events' | 'volunteers' | 'helpRequests';

// ─── Dashboard Queries ──────────────────────────────────────────────────────

export function useReportsDashboard(section: DashboardSection, params?: string) {
  return useQuery({
    queryKey: ['reports', 'dashboard', section, params],
    queryFn: () =>
      api.get<unknown>(
        `/api/v2/reports/dashboard/${section}/${params ? `?${params}` : ''}`,
      ),
  });
}

// ─── Specific Report Queries ────────────────────────────────────────────────

export function useAttendanceReport(params?: string) {
  return useQuery({
    queryKey: ['reports', 'attendance', params],
    queryFn: () =>
      api.get<unknown>(
        `/api/v2/reports/attendance/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useDonationReport(params?: string) {
  return useQuery({
    queryKey: ['reports', 'donations', params],
    queryFn: () =>
      api.get<unknown>(
        `/api/v2/reports/donations/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useVolunteerReport(params?: string) {
  return useQuery({
    queryKey: ['reports', 'volunteers', params],
    queryFn: () =>
      api.get<unknown>(
        `/api/v2/reports/volunteers/${params ? `?${params}` : ''}`,
      ),
  });
}

// ─── Report Schedules ───────────────────────────────────────────────────────

export function useReportSchedules(params?: string) {
  return useQuery({
    queryKey: ['reports', 'schedules', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/reports/schedules/${params ? `?${params}` : ''}`,
      ),
  });
}

// ─── Saved Reports ──────────────────────────────────────────────────────────

export function useSavedReports(params?: string) {
  return useQuery({
    queryKey: ['reports', 'saved', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/reports/saved-reports/${params ? `?${params}` : ''}`,
      ),
  });
}

// ─── Saved Report Mutations ─────────────────────────────────────────────────

export function useCreateSavedReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/reports/saved-reports/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports', 'saved'] });
    },
  });
}

// ─── Infinite Scroll Queries ─────────────────────────────────────────────────

export function useInfiniteReportSchedules(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['reports', 'schedules', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/reports/schedules/?${params}`),
    search,
    filters,
  });
}

export function useInfiniteSavedReports(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['reports', 'saved', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/reports/saved-reports/?${params}`),
    search,
    filters,
  });
}
