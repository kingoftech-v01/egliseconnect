import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useInfiniteList } from './use-infinite-list';
import type { PaginatedResponse } from '@egliseconnect/types';

interface AttendanceSession {
  id: string;
  title: string;
  session_type: string;
  date: string;
  start_time: string;
  end_time: string | null;
  location: string;
  attendance_count: number;
  is_active: boolean;
  created_at: string;
}

interface QrCode {
  id: string;
  code: string;
  qr_image: string | null;
  is_active: boolean;
  created_at: string;
}

interface CheckInData {
  qr_code: string;
  session_id: string;
}

interface CheckInResponse {
  success: boolean;
  message: string;
  member_name?: string;
  checked_in_at?: string;
}

export function useSessions(params?: string) {
  return useQuery<PaginatedResponse<AttendanceSession>>({
    queryKey: ['attendance', 'sessions', params],
    queryFn: () =>
      api.attendance.sessions.list(params) as Promise<
        PaginatedResponse<AttendanceSession>
      >,
  });
}

export function useMyQrCode() {
  return useQuery<QrCode>({
    queryKey: ['attendance', 'qr-code'],
    queryFn: () => api.attendance.qrCode.mine() as Promise<QrCode>,
  });
}

export function useInfiniteSessions(options?: { search?: string; enabled?: boolean }) {
  return useInfiniteList<AttendanceSession>(
    ['attendance', 'sessions'],
    (params) => api.attendance.sessions.list(params),
    options,
  );
}

export function useCheckIn() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CheckInData) =>
      api.attendance.checkIn(data) as Promise<CheckInResponse>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendance', 'sessions'] });
    },
  });
}
