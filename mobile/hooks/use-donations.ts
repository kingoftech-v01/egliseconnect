import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useInfiniteList } from './use-infinite-list';
import type {
  DonationListItem,
  DonationCreateRequest,
  PaginatedResponse,
} from '@egliseconnect/types';

export function useDonations(params?: string) {
  return useQuery<PaginatedResponse<DonationListItem>>({
    queryKey: ['donations', params],
    queryFn: () =>
      api.donations.list(params) as Promise<PaginatedResponse<DonationListItem>>,
  });
}

export function useInfiniteDonations(options?: { search?: string; enabled?: boolean }) {
  return useInfiniteList<DonationListItem>(
    ['donations'],
    (params) => api.donations.list(params),
    options,
  );
}

export function useCreateDonation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: DonationCreateRequest) =>
      api.donations.create(data) as Promise<DonationListItem>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['donations'] });
    },
  });
}
