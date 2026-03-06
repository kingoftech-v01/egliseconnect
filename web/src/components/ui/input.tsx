import { forwardRef, type InputHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, error, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          'flex h-10 w-full rounded-xl bg-white/[0.06] border border-white/[0.08] px-3 py-2 text-sm text-white/90 placeholder:text-white/30',
          'transition-all duration-200',
          'focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/30',
          'file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-white/60',
          error && 'border-rose-500/50 focus:ring-rose-500/30',
          className,
        )}
        ref={ref}
        {...props}
      />
    );
  },
);
Input.displayName = 'Input';

export { Input };
