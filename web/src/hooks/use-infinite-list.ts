'use client';

import { useInfiniteQuery } from '@tanstack/react-query';
import type { PaginatedResponse } from '@egliseconnect/types';

interface UseInfiniteListOptions<T> {
  queryKey: unknown[];
  fetchFn: (params: string) => Promise<PaginatedResponse<T>>;
  search?: string;
  filters?: Record<string, string | number | boolean | undefined>;
  pageSize?: number;
  enabled?: boolean;
}

/**
 * Generic infinite-scroll hook wrapping React Query v5 `useInfiniteQuery`.
 *
 * - Derives `initialPageParam = 1` and computes `getNextPageParam` from the
 *   `next` URL returned by the DRF paginator.
 * - Merges `search` and arbitrary `filters` into the query string for every
 *   page request.
 * - Returns the standard `useInfiniteQuery` result (data, fetchNextPage,
 *   hasNextPage, isFetchingNextPage, ...).
 */
export function useInfiniteList<T>({
  queryKey,
  fetchFn,
  search,
  filters,
  pageSize = 20,
  enabled = true,
}: UseInfiniteListOptions<T>) {
  return useInfiniteQuery<PaginatedResponse<T>>({
    queryKey: [...queryKey, { search, filters }],
    queryFn: ({ pageParam }) => {
      const params = new URLSearchParams();
      params.set('page', String(pageParam));
      params.set('page_size', String(pageSize));
      if (search) params.set('search', search);
      if (filters) {
        Object.entries(filters).forEach(([k, v]) => {
          if (v !== undefined && v !== '') params.set(k, String(v));
        });
      }
      return fetchFn(params.toString());
    },
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      if (!lastPage.next) return undefined;
      try {
        const url = new URL(lastPage.next, 'http://localhost');
        const nextPage = url.searchParams.get('page');
        return nextPage ? Number(nextPage) : undefined;
      } catch {
        return undefined;
      }
    },
    enabled,
  });
}
