'use client';

import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from './button';
import { cn } from '@/lib/utils';

export interface Column<T> {
  key: string;
  header?: string;
  label?: string;
  render?: (item: T) => React.ReactNode;
  className?: string;
}

interface PaginationProps {
  count: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}

interface DataTableProps<T extends Record<string, unknown>> {
  columns: Column<T>[];
  data: T[];
  isLoading?: boolean;
  loading?: boolean;
  emptyMessage?: string;
  page?: number;
  totalPages?: number;
  onPageChange?: (page: number) => void;
  onRowClick?: (item: T) => void;
  pagination?: PaginationProps;
}

export function DataTable<T extends Record<string, unknown>>({
  columns,
  data,
  isLoading,
  loading,
  emptyMessage = 'Aucune donnée',
  page: pageProp,
  totalPages: totalPagesProp,
  onPageChange: onPageChangeProp,
  onRowClick,
  pagination,
}: DataTableProps<T>) {
  const isLoadingFinal = isLoading ?? loading ?? false;
  const page = pagination?.page ?? pageProp ?? 1;
  const totalPages = pagination
    ? Math.ceil(pagination.count / pagination.pageSize)
    : (totalPagesProp ?? 1);
  const onPageChange = pagination?.onPageChange ?? onPageChangeProp;

  if (isLoadingFinal) {
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

  if (!data.length) {
    return (
      <div className="rounded-2xl bg-white/[0.05] backdrop-blur-xl border border-white/[0.08] p-12 text-center">
        <p className="text-white/40">{emptyMessage}</p>
      </div>
    );
  }

  return (
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
                  <td key={col.key} className={cn('px-4 py-3 text-sm text-white/70', col.className)}>
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

      {totalPages > 1 && onPageChange && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-white/[0.06]">
          <p className="text-xs text-white/40">
            Page {page} sur {totalPages}
          </p>
          <div className="flex gap-1">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className="h-8 w-8"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              className="h-8 w-8"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
