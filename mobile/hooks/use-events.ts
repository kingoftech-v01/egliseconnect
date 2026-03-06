import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useInfiniteList } from './use-infinite-list';
import type { EventListItem, Event, PaginatedResponse } from '@egliseconnect/types';

export function useEvents(params?: string) {
  return useQuery<PaginatedResponse<EventListItem>>({
    queryKey: ['events', params],
    queryFn: () =>
      api.events.list(params) as Promise<PaginatedResponse<EventListItem>>,
  });
}

export function useInfiniteEvents(options?: { search?: string; enabled?: boolean }) {
  return useInfiniteList<EventListItem>(
    ['events'],
    (params) => api.events.list(params),
    options,
  );
}

export function useEvent(id: string) {
  return useQuery<Event>({
    queryKey: ['events', id],
    queryFn: () => api.events.get(id) as Promise<Event>,
    enabled: !!id,
  });
}
