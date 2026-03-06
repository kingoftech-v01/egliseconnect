'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useInfiniteList } from './use-infinite-list';
import type { PaginatedResponse } from '@egliseconnect/types';

// ─── Events ─────────────────────────────────────────────────────────────────

export function useEvents(params?: string) {
  return useQuery({
    queryKey: ['events', params],
    queryFn: () => api.events.list(params) as Promise<PaginatedResponse<unknown>>,
  });
}

export function useInfiniteEvents(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['events', 'infinite'],
    fetchFn: (params) => api.events.list(params) as Promise<PaginatedResponse<unknown>>,
    search,
    filters,
  });
}

export function useEvent(id: string) {
  return useQuery({
    queryKey: ['events', id],
    queryFn: () => api.events.get(id),
    enabled: !!id,
  });
}

export function useCreateEvent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => api.events.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] });
    },
  });
}

export function useUpdateEvent(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => api.events.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] });
      queryClient.invalidateQueries({ queryKey: ['events', id] });
    },
  });
}

export function useDeleteEvent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.events.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] });
    },
  });
}

export function useEventRSVP(eventId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { status: string }) =>
      api.post(`/api/v2/events/${eventId}/rsvp/`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] });
      queryClient.invalidateQueries({ queryKey: ['events', eventId] });
    },
  });
}

// ─── Upcoming Events ────────────────────────────────────────────────────────

export function useUpcomingEvents(params?: string) {
  return useQuery({
    queryKey: ['events', 'upcoming', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/events/events/upcoming/${params ? `?${params}` : ''}`,
      ),
  });
}

// ─── Calendar ───────────────────────────────────────────────────────────────

export function useCalendarEvents(params?: string) {
  return useQuery({
    queryKey: ['events', 'calendar', params],
    queryFn: () =>
      api.get<unknown>(
        `/api/v2/events/events/calendar/${params ? `?${params}` : ''}`,
      ),
  });
}

// ─── Rooms ──────────────────────────────────────────────────────────────────

export function useRooms(params?: string) {
  return useQuery({
    queryKey: ['events', 'rooms', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/events/rooms/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useInfiniteRooms(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['events', 'rooms', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/events/rooms/?${params}`),
    search,
    filters,
  });
}

export function useCreateRoom() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/events/rooms/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events', 'rooms'] });
    },
  });
}

// ─── Room Bookings ──────────────────────────────────────────────────────────

export function useInfiniteRoomBookings(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['events', 'bookings', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/events/bookings/?${params}`),
    search,
    filters,
  });
}

export function useCreateRoomBooking() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/events/bookings/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events', 'bookings'] });
    },
  });
}

// ─── Event Templates ────────────────────────────────────────────────────────

export function useInfiniteEventTemplates(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['events', 'templates', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/events/templates/?${params}`),
    search,
    filters,
  });
}

export function useCreateEventTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/events/templates/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events', 'templates'] });
    },
  });
}
