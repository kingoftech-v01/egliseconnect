'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useInfiniteList } from './use-infinite-list';
import type { PaginatedResponse, MemberListItem, Member, MemberCreateRequest } from '@egliseconnect/types';

// ─── Members ────────────────────────────────────────────────────────────────

export function useMembers(params?: string) {
  return useQuery({
    queryKey: ['members', params],
    queryFn: () => api.members.list(params) as Promise<PaginatedResponse<MemberListItem>>,
  });
}

export function useInfiniteMembers(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<MemberListItem>({
    queryKey: ['members', 'infinite'],
    fetchFn: (params) => api.members.list(params) as Promise<PaginatedResponse<MemberListItem>>,
    search,
    filters,
  });
}

export function useMember(id: string) {
  return useQuery({
    queryKey: ['members', id],
    queryFn: () => api.members.get(id) as Promise<Member>,
    enabled: !!id,
  });
}

export function useCreateMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: MemberCreateRequest) => api.members.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members'] });
    },
  });
}

export function useUpdateMember(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<MemberCreateRequest>) => api.members.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members'] });
      queryClient.invalidateQueries({ queryKey: ['members', id] });
    },
  });
}

export function useDeleteMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.members.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members'] });
    },
  });
}

// ─── Birthdays ──────────────────────────────────────────────────────────────

export function useBirthdays(period: 'today' | 'week' | 'month' = 'month') {
  return useQuery({
    queryKey: ['members', 'birthdays', period],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/members/members/birthdays/?period=${period}`,
      ),
  });
}

// ─── Directory ──────────────────────────────────────────────────────────────

export function useDirectory(search?: string) {
  return useQuery({
    queryKey: ['members', 'directory', search],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/members/members/directory/${search ? `?search=${encodeURIComponent(search)}` : ''}`,
      ),
  });
}

// ─── Families ───────────────────────────────────────────────────────────────

export function useFamilies(params?: string) {
  return useQuery({
    queryKey: ['members', 'families', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/members/families/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useInfiniteFamilies(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['members', 'families', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/members/families/?${params}`),
    search,
    filters,
  });
}

export function useFamily(id: string) {
  return useQuery({
    queryKey: ['members', 'families', id],
    queryFn: () => api.get<unknown>(`/api/v2/members/families/${id}/`),
    enabled: !!id,
  });
}

export function useCreateFamily() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/members/families/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members', 'families'] });
    },
  });
}

export function useUpdateFamily(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.patch(`/api/v2/members/families/${id}/`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members', 'families'] });
    },
  });
}

export function useDeleteFamily() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/api/v2/members/families/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members', 'families'] });
    },
  });
}

// ─── Groups ─────────────────────────────────────────────────────────────────

export function useGroups(params?: string) {
  return useQuery({
    queryKey: ['members', 'groups', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/members/groups/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useInfiniteGroups(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['members', 'groups', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/members/groups/?${params}`),
    search,
    filters,
  });
}

export function useGroup(id: string) {
  return useQuery({
    queryKey: ['members', 'groups', id],
    queryFn: () => api.get<unknown>(`/api/v2/members/groups/${id}/`),
    enabled: !!id,
  });
}

export function useCreateGroup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/members/groups/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members', 'groups'] });
    },
  });
}

export function useUpdateGroup(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.patch(`/api/v2/members/groups/${id}/`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members', 'groups'] });
    },
  });
}

export function useDeleteGroup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/api/v2/members/groups/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members', 'groups'] });
    },
  });
}

export function useGroupMembers(groupId: string) {
  return useQuery({
    queryKey: ['members', 'groups', groupId, 'members'],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/members/groups/${groupId}/members/`),
    enabled: !!groupId,
  });
}

export function useAddGroupMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ groupId, memberId, role }: { groupId: string; memberId: string; role?: string }) =>
      api.post(`/api/v2/members/groups/${groupId}/add_member/`, { member_id: memberId, role }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members', 'groups'] });
    },
  });
}

export function useRemoveGroupMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ groupId, memberId }: { groupId: string; memberId: string }) =>
      api.post(`/api/v2/members/groups/${groupId}/remove_member/`, { member_id: memberId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members', 'groups'] });
    },
  });
}
