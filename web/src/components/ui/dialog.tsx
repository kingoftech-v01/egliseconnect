'use client';

import { useEffect, useRef, type ReactNode } from 'react';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface DialogProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  className?: string;
}

export function Dialog({ open, onClose, children, className }: DialogProps) {
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [open]);

  useEffect(() => {
    function handleEsc(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    if (open) document.addEventListener('keydown', handleEsc);
    return () => document.removeEventListener('keydown', handleEsc);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        ref={overlayRef}
        className="fixed inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      <div
        className={cn(
          'relative z-10 w-full max-w-lg rounded-2xl bg-[#1a1145]/90 backdrop-blur-xl border border-white/[0.1]',
          'shadow-[0_20px_60px_rgba(0,0,0,0.5)]',
          'animate-in fade-in slide-in-from-bottom-4 duration-200',
          className,
        )}
      >
        {children}
      </div>
    </div>
  );
}

export function DialogHeader({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn('flex flex-col space-y-1.5 p-6 pb-4', className)}>
      {children}
    </div>
  );
}

export function DialogTitle({ children, className }: { children: ReactNode; className?: string }) {
  return <h2 className={cn('text-lg font-semibold text-white', className)}>{children}</h2>;
}

export function DialogDescription({ children, className }: { children: ReactNode; className?: string }) {
  return <p className={cn('text-sm text-white/50', className)}>{children}</p>;
}

export function DialogContent({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn('px-6 pb-4', className)}>{children}</div>;
}

export function DialogFooter({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn('flex justify-end gap-2 p-6 pt-2', className)}>{children}</div>;
}

export function DialogClose({ onClose, className }: { onClose: () => void; className?: string }) {
  return (
    <button
      onClick={onClose}
      className={cn(
        'absolute right-4 top-4 p-1 rounded-lg text-white/40 hover:text-white/70 hover:bg-white/[0.06] transition-colors',
        className,
      )}
    >
      <X className="h-4 w-4" />
    </button>
  );
}
