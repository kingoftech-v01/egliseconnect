'use client';

import { useRef, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Column } from './data-table';

interface InfiniteScrollTableProps<T extends Record<string, unknown>> {
  /** Column definitions (same interface as DataTable). */
  columns: Column<T>[];
  /** Flattened items from all fetched pages. */
  data: T[];
  /** Total count from the first page. */
  totalCount?: number;
  /** Whether the initial load is in progress. */
  isLoading?: boolean;
  /** Whether a next-page fetch is in progress. */
  isFetchingNextPage?: boolean;
  /** Whether more pages exist. */
  hasNextPage?: boolean;
  /** Callback to fetch the next page. */
  fetchNextPage?: () => void;
  /** Shown when data is empty and not loading. */
  emptyMessage?: string;
  /** Shown when an error occurred. */
  error?: Error | null;
  /** Optional row-click handler. */
  onRowClick?: (item: T) => void;
}

/**
 * Infinite-scroll table that reuses the `Column<T>` interface from DataTable.
 *
 * Renders a glass-morphism table with an IntersectionObserver sentinel after
 * the last row to trigger `fetchNextPage`.
 */
export function InfiniteScrollTable<T extends Record<string, unknown>>({
  columns,
  data,
  totalCount,
  isLoading = false,
  isFetchingNextPage = false,
  hasNextPage = false,
  fetchNextPage,
  emptyMessage = 'Aucune donnée',
  error,
  onRowClick,
}: InfiniteScrollTableProps<T>) {
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
            <div key={i} className="h-10 bg-white/[0.04] rounded-xl" />
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
  if (!data.length) {
    return (
      <div className="rounded-2xl bg-white/[0.05] backdrop-blur-xl border border-white/[0.08] p-12 text-center">
        <p className="text-white/40">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div>
      {/* Total count */}
      {typeof totalCount === 'number' && (
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs text-white/40">
            {data.length} sur {totalCount} résultat{totalCount !== 1 ? 's' : ''}
          </p>
        </div>
      )}

      <div className="rounded-2xl bg-white/[0.05] backdrop-blur-xl border border-white/[0.08] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/[0.06]">
                {columns.map((col) => (
                  <th
                    key={col.key}
                    className={cn(
                      'px-4 py-3 text-left text-xs font-medium text-white/40 uppercase tracking-wider',
                      col.className,
                    )}
                  >
                    {col.header || col.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((item, idx) => (
                <tr
                  key={idx}
                  onClick={() => onRowClick?.(item)}
                  className={cn(
                    'border-b border-white/[0.04] transition-colors',
                    onRowClick && 'cursor-pointer hover:bg-white/[0.04]',
                  )}
                >
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={cn(
                        'px-4 py-3 text-sm text-white/70',
                        col.className,
                      )}
                    >
                      {col.render
                        ? col.render(item)
                        : (item[col.key] as React.ReactNode)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Sentinel inside the card, after the table */}
        <div ref={sentinelRef} className="h-px" />

        {/* Fetching indicator */}
        {isFetchingNextPage && (
          <div className="flex justify-center py-4 border-t border-white/[0.06]">
            <Loader2 className="h-5 w-5 animate-spin text-white/40" />
          </div>
        )}
      </div>
    </div>
  );
}
