import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useInfiniteList } from './use-infinite-list';
import type { MemberListItem, Member, PaginatedResponse } from '@egliseconnect/types';

export function useMembers(params?: string) {
  return useQuery<PaginatedResponse<MemberListItem>>({
    queryKey: ['members', params],
    queryFn: () =>
      api.members.list(params) as Promise<PaginatedResponse<MemberListItem>>,
  });
}

export function useInfiniteMembers(options?: { search?: string; enabled?: boolean }) {
  return useInfiniteList<MemberListItem>(
    ['members'],
    (params) => api.members.list(params),
    options,
  );
}

export function useMember(id: string) {
  return useQuery<Member>({
    queryKey: ['members', id],
    queryFn: () => api.members.get(id) as Promise<Member>,
    enabled: !!id,
  });
}
