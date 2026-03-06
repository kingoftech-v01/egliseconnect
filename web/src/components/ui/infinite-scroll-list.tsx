'use client';

import { useRef, useEffect } from 'react';
import { Loader2 } from 'lucide-react';

interface InfiniteScrollListProps<T> {
  /** Flattened items from all fetched pages. */
  items: T[];
  /** Total count from the first page (data.pages[0].count). */
  totalCount?: number;
  /** Render function for each item. */
  renderItem: (item: T, index: number) => React.ReactNode;
  /** Whether the initial load is in progress. */
  isLoading?: boolean;
  /** Whether a next-page fetch is in progress. */
  isFetchingNextPage?: boolean;
  /** Whether more pages exist. */
  hasNextPage?: boolean;
  /** Callback to fetch the next page. */
  fetchNextPage?: () => void;
  /** Shown when items is empty and not loading. */
  emptyMessage?: string;
  /** Shown when an error occurred. */
  error?: Error | null;
  /** Optional CSS class for the outer container. */
  className?: string;
}

/**
 * A generic infinite-scroll list container.
 *
 * Uses `IntersectionObserver` with a sentinel element to trigger
 * `fetchNextPage` when the user scrolls near the bottom.
 */
export function InfiniteScrollList<T>({
  items,
  totalCount,
  renderItem,
  isLoading = false,
  isFetchingNextPage = false,
  hasNextPage = false,
  fetchNextPage,
  emptyMessage = 'Aucune donnée',
  error,
  className,
}: InfiniteScrollListProps<T>) {
  const sentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel || !hasNextPage || !fetchNextPage) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting && !isFetchingNextPage) {
          fetchNextPage();
        }
      },
      { rootMargin: '0px 0px 200px 0px' },
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasNextPage, fetchNextPage, isFetchingNextPage]);

  // ── Loading skeleton ──
  if (isLoading) {
    return (
      <div className="rounded-2xl bg-white/[0.05] backdrop-blur-xl border border-white/[0.08] overflow-hidden">
        <div className="animate-pulse p-6 space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-16 bg-white/[0.04] rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  // ── Error state ──
  if (error) {
    return (
      <div className="rounded-2xl bg-white/[0.05] backdrop-blur-xl border border-red-500/20 p-12 text-center">
        <p className="text-red-400">Erreur : {error.message}</p>
      </div>
    );
  }

  // ── Empty state ──
  if (!items.length) {
    return (
      <div className="rounded-2xl bg-white/[0.05] backdrop-blur-xl border border-white/[0.08] p-12 text-center">
        <p className="text-white/40">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Total count badge */}
      {typeof totalCount === 'number' && (
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs text-white/40">
            {items.length} sur {totalCount} résultat{totalCount !== 1 ? 's' : ''}
          </p>
        </div>
      )}

      {/* Items */}
      <div className="space-y-3">
        {items.map((item, idx) => renderItem(item, idx))}
      </div>

      {/* Sentinel + loading spinner */}
      <div ref={sentinelRef} className="h-px" />
      {isFetchingNextPage && (
        <div className="flex justify-center py-6">
          <Loader2 className="h-5 w-5 animate-spin text-white/40" />
        </div>
      )}
    </div>
  );
}
