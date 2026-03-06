'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useInfiniteList } from './use-infinite-list';
import type { PaginatedResponse } from '@egliseconnect/types';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface Position {
  id: string;
  name: string;
  description?: string;
  position_type: string;
  min_volunteers: number;
  max_volunteers: number;
  active_volunteer_count?: number;
  is_active: boolean;
}

export interface Schedule {
  id: string;
  member_name?: string;
  member?: string;
  position_name?: string;
  position?: string;
  scheduled_date: string;
  status: 'pending' | 'confirmed' | 'absent' | 'replaced';
  notes?: string;
}

export interface Availability {
  id: string;
  member_name?: string;
  member?: string;
  day_of_week?: number;
  day_of_week_display?: string;
  start_time?: string;
  end_time?: string;
  is_available: boolean;
  notes?: string;
}

export interface SwapRequest {
  id: string;
  requester_name?: string;
  requester?: string;
  target_name?: string;
  target?: string;
  schedule_name?: string;
  schedule?: string;
  status: 'pending' | 'accepted' | 'rejected' | 'cancelled';
  reason?: string;
  created_at?: string;
}

// ─── Queries ──────────────────────────────────────────────────────────────────

export function usePositions(params?: string) {
  return useQuery({
    queryKey: ['volunteers', 'positions', params],
    queryFn: () =>
      api.volunteers.positions.list(params) as Promise<PaginatedResponse<Position>>,
  });
}

export function usePosition(id: string) {
  return useQuery({
    queryKey: ['volunteers', 'positions', id],
    queryFn: () => api.volunteers.positions.get(id) as Promise<Position>,
    enabled: !!id,
  });
}

export function useSchedules(params?: string) {
  return useQuery({
    queryKey: ['volunteers', 'schedules', params],
    queryFn: () =>
      api.volunteers.schedules.list(params) as Promise<PaginatedResponse<Schedule>>,
  });
}

export function useMySchedule() {
  return useQuery({
    queryKey: ['volunteers', 'my-schedule'],
    queryFn: () => api.volunteers.schedules.mySchedule() as Promise<Schedule[]>,
  });
}

export function useAvailability(params?: string) {
  return useQuery({
    queryKey: ['volunteers', 'availability', params],
    queryFn: () =>
      api.volunteers.availability.list(params) as Promise<PaginatedResponse<Availability>>,
  });
}

export function useSwapRequests(params?: string) {
  return useQuery({
    queryKey: ['volunteers', 'swap-requests', params],
    queryFn: () =>
      api.volunteers.swapRequests.list(params) as Promise<PaginatedResponse<SwapRequest>>,
  });
}

// ─── Infinite Scroll Queries ─────────────────────────────────────────────────

export function useInfinitePositions(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<Position>({
    queryKey: ['volunteers', 'positions', 'infinite'],
    fetchFn: (params) => api.volunteers.positions.list(params) as Promise<PaginatedResponse<Position>>,
    search,
    filters,
  });
}

export function useInfiniteSchedules(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<Schedule>({
    queryKey: ['volunteers', 'schedules', 'infinite'],
    fetchFn: (params) => api.volunteers.schedules.list(params) as Promise<PaginatedResponse<Schedule>>,
    search,
    filters,
  });
}

export function useInfiniteAvailability(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<Availability>({
    queryKey: ['volunteers', 'availability', 'infinite'],
    fetchFn: (params) => api.volunteers.availability.list(params) as Promise<PaginatedResponse<Availability>>,
    search,
    filters,
  });
}

export function useInfiniteSwapRequests(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<SwapRequest>({
    queryKey: ['volunteers', 'swap-requests', 'infinite'],
    fetchFn: (params) => api.volunteers.swapRequests.list(params) as Promise<PaginatedResponse<SwapRequest>>,
    search,
    filters,
  });
}

// ─── Mutations ────────────────────────────────────────────────────────────────

export function useCreatePosition() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.volunteers.positions.create(data) as Promise<Position>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['volunteers', 'positions'] });
    },
  });
}

export function useCreateSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.volunteers.schedules.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['volunteers', 'schedules'] });
      queryClient.invalidateQueries({ queryKey: ['volunteers', 'my-schedule'] });
    },
  });
}

export function useConfirmSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (scheduleId: string) =>
      api.volunteers.schedules.confirm(scheduleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['volunteers', 'schedules'] });
      queryClient.invalidateQueries({ queryKey: ['volunteers', 'my-schedule'] });
    },
  });
}

export function useCreateAvailability() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.volunteers.availability.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['volunteers', 'availability'] });
    },
  });
}

export function useCreateSwapRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.volunteers.swapRequests.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['volunteers', 'swap-requests'] });
    },
  });
}

// ─── Skills ──────────────────────────────────────────────────────────────────

export function useSkills(params?: string) {
  return useQuery({
    queryKey: ['volunteers', 'skills', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/volunteers/skills/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useInfiniteSkills(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['volunteers', 'skills', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/volunteers/skills/?${params}`),
    search,
    filters,
  });
}

export function useCreateSkill() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/volunteers/skills/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['volunteers', 'skills'] });
    },
  });
}

// ─── Planned Absences ────────────────────────────────────────────────────────

export function useInfinitePlannedAbsences(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['volunteers', 'absences', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/volunteers/planned-absences/?${params}`),
    search,
    filters,
  });
}

export function useCreatePlannedAbsence() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/volunteers/planned-absences/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['volunteers', 'absences'] });
    },
  });
}

// ─── Volunteer Hours ─────────────────────────────────────────────────────────

export function useVolunteerHours(params?: string) {
  return useQuery({
    queryKey: ['volunteers', 'hours', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/volunteers/hours/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useInfiniteVolunteerHours(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['volunteers', 'hours', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/volunteers/hours/?${params}`),
    search,
    filters,
  });
}

export function useLogVolunteerHours() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/volunteers/hours/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['volunteers', 'hours'] });
    },
  });
}
