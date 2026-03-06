import { useInfiniteQuery } from '@tanstack/react-query';

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export function useInfiniteList<T>(
  queryKey: string[],
  fetchFn: (params?: string) => Promise<any>,
  options?: { search?: string; enabled?: boolean }
) {
  return useInfiniteQuery({
    queryKey: [...queryKey, options?.search],
    queryFn: async ({ pageParam = 1 }) => {
      const params = new URLSearchParams();
      params.set('page', String(pageParam));
      if (options?.search) params.set('search', options.search);
      const res = await fetchFn(params.toString());
      return res as PaginatedResponse<T>;
    },
    initialPageParam: 1,
    getNextPageParam: (lastPage, allPages) => {
      if (!lastPage?.next) return undefined;
      return allPages.length + 1;
    },
    enabled: options?.enabled ?? true,
  });
}
