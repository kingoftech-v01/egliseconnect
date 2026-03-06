import { forwardRef, type TextareaHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean;
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          'flex min-h-[80px] w-full rounded-xl bg-white/[0.06] border border-white/[0.08] px-3 py-2 text-sm text-white/90 placeholder:text-white/30',
          'transition-all duration-200 resize-none',
          'focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/30',
          error && 'border-rose-500/50 focus:ring-rose-500/30',
          className,
        )}
        ref={ref}
        {...props}
      />
    );
  },
);
Textarea.displayName = 'Textarea';

export { Textarea };
