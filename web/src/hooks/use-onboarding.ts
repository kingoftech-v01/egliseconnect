'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useInfiniteList } from './use-infinite-list';
import type { PaginatedResponse } from '@egliseconnect/types';

// ─── Status & Stats ─────────────────────────────────────────────────────────

export function useOnboardingStatus() {
  return useQuery({
    queryKey: ['onboarding', 'status'],
    queryFn: () => api.get<unknown>('/api/v2/onboarding/status/'),
  });
}

export function useOnboardingStats() {
  return useQuery({
    queryKey: ['onboarding', 'stats'],
    queryFn: () => api.get<unknown>('/api/v2/onboarding/stats/'),
  });
}

// ─── Courses ────────────────────────────────────────────────────────────────

export function useCourses(params?: string) {
  return useQuery({
    queryKey: ['onboarding', 'courses', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/onboarding/courses/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useCourse(id: string) {
  return useQuery({
    queryKey: ['onboarding', 'courses', id],
    queryFn: () => api.get<unknown>(`/api/v2/onboarding/courses/${id}/`),
    enabled: !!id,
  });
}

export function useCreateCourse() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/onboarding/courses/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding', 'courses'] });
    },
  });
}

// ─── Trainings ──────────────────────────────────────────────────────────────

export function useTrainings(params?: string) {
  return useQuery({
    queryKey: ['onboarding', 'trainings', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/onboarding/trainings/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useTraining(id: string) {
  return useQuery({
    queryKey: ['onboarding', 'trainings', id],
    queryFn: () => api.get<unknown>(`/api/v2/onboarding/trainings/${id}/`),
    enabled: !!id,
  });
}

// ─── Interviews ─────────────────────────────────────────────────────────────

export function useInterviews(params?: string) {
  return useQuery({
    queryKey: ['onboarding', 'interviews', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/onboarding/interviews/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useInterview(id: string) {
  return useQuery({
    queryKey: ['onboarding', 'interviews', id],
    queryFn: () => api.get<unknown>(`/api/v2/onboarding/interviews/${id}/`),
    enabled: !!id,
  });
}

export function useAcceptInterview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api.post(`/api/v2/onboarding/interviews/${id}/accept/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding', 'interviews'] });
    },
  });
}

export function useCounterProposeInterview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, proposedDate }: { id: string; proposedDate: string }) =>
      api.post(`/api/v2/onboarding/interviews/${id}/counter_propose/`, {
        proposed_date: proposedDate,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding', 'interviews'] });
    },
  });
}

// ─── Invitation Codes ───────────────────────────────────────────────────────

export function useInvitationCodes(params?: string) {
  return useQuery({
    queryKey: ['onboarding', 'invitations', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/onboarding/invitations/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useCreateInvitationCode() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/onboarding/invitations/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding', 'invitations'] });
    },
  });
}

// ─── Mentors ────────────────────────────────────────────────────────────────

export function useMentors(params?: string) {
  return useQuery({
    queryKey: ['onboarding', 'mentors', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/onboarding/mentors/${params ? `?${params}` : ''}`,
      ),
  });
}

// ─── Documents ──────────────────────────────────────────────────────────────

export function useOnboardingDocuments(params?: string) {
  return useQuery({
    queryKey: ['onboarding', 'documents', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/onboarding/documents/${params ? `?${params}` : ''}`,
      ),
  });
}

// ─── Quiz ───────────────────────────────────────────────────────────────────

export function useQuiz(courseId: string) {
  return useQuery({
    queryKey: ['onboarding', 'quiz', courseId],
    queryFn: () => api.get<unknown>(`/api/v2/onboarding/quizzes/?course=${courseId}`),
    enabled: !!courseId,
  });
}

export function useSubmitQuiz(courseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { answers: Record<string, unknown> }) =>
      api.post('/api/v2/onboarding/quiz-attempts/submit/', { ...data, course: courseId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding', 'quiz', courseId] });
      queryClient.invalidateQueries({ queryKey: ['onboarding', 'courses', courseId] });
      queryClient.invalidateQueries({ queryKey: ['onboarding', 'status'] });
    },
  });
}

// ─── Infinite Scroll Queries ─────────────────────────────────────────────────

export function useInfiniteCourses(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['onboarding', 'courses', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/onboarding/courses/?${params}`),
    search,
    filters,
  });
}

export function useInfiniteTrainings(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['onboarding', 'trainings', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/onboarding/trainings/?${params}`),
    search,
    filters,
  });
}

export function useInfiniteInterviews(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['onboarding', 'interviews', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/onboarding/interviews/?${params}`),
    search,
    filters,
  });
}

export function useInfiniteInvitationCodes(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['onboarding', 'invitations', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/onboarding/invitations/?${params}`),
    search,
    filters,
  });
}

export function useInfiniteMentors(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['onboarding', 'mentors', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/onboarding/mentors/?${params}`),
    search,
    filters,
  });
}

export function useInfiniteOnboardingDocuments(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['onboarding', 'documents', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/onboarding/documents/?${params}`),
    search,
    filters,
  });
}

// ─── Welcome Sequences ─────────────────────────────────────────────────────

export function useWelcomeSequences(params?: string) {
  return useQuery({
    queryKey: ['onboarding', 'welcome-sequences', params],
    queryFn: () =>
      api.get<PaginatedResponse<unknown>>(
        `/api/v2/onboarding/welcome-sequences/${params ? `?${params}` : ''}`,
      ),
  });
}

export function useInfiniteWelcomeSequences(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['onboarding', 'welcome-sequences', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/onboarding/welcome-sequences/?${params}`),
    search,
    filters,
  });
}

export function useCreateWelcomeSequence() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/onboarding/welcome-sequences/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding', 'welcome-sequences'] });
    },
  });
}

// ─── Visitor Follow-Ups ────────────────────────────────────────────────────

export function useInfiniteVisitors(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['onboarding', 'visitors', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/onboarding/visitors/?${params}`),
    search,
    filters,
  });
}

export function useCreateVisitorFollowUp() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/onboarding/visitors/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding', 'visitors'] });
    },
  });
}

// ─── Achievements ──────────────────────────────────────────────────────────

export function useInfiniteAchievements(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['onboarding', 'achievements', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/onboarding/achievements/?${params}`),
    search,
    filters,
  });
}

export function useCreateAchievement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/onboarding/achievements/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding', 'achievements'] });
    },
  });
}

// ─── Onboarding Tracks ─────────────────────────────────────────────────────

export function useInfiniteTracks(search?: string, filters?: Record<string, string | number | boolean | undefined>) {
  return useInfiniteList<unknown>({
    queryKey: ['onboarding', 'tracks', 'infinite'],
    fetchFn: (params) =>
      api.get<PaginatedResponse<unknown>>(`/api/v2/onboarding/tracks/?${params}`),
    search,
    filters,
  });
}

export function useCreateTrack() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/onboarding/tracks/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding', 'tracks'] });
    },
  });
}

// ─── Mentor Actions ────────────────────────────────────────────────────────

export function useCreateMentorAssignment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post('/api/v2/onboarding/mentor-assignments/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding', 'mentors'] });
    },
  });
}

export function useCompleteMentorAssignment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api.post(`/api/v2/onboarding/mentor-assignments/${id}/complete/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding', 'mentors'] });
    },
  });
}

export function useLogMentorCheckin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, notes }: { id: string; notes: string }) =>
      api.post(`/api/v2/onboarding/mentor-assignments/${id}/checkin/`, { notes }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding', 'mentors'] });
    },
  });
}

// ─── Document Signatures ───────────────────────────────────────────────────

export function useSignDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { document: string; signature_text: string }) =>
      api.post('/api/v2/onboarding/signatures/sign/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding', 'documents'] });
    },
  });
}
