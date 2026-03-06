import { forwardRef, type SelectHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';
import { ChevronDown } from 'lucide-react';

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  error?: boolean;
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, error, children, ...props }, ref) => {
    return (
      <div className="relative">
        <select
          className={cn(
            'flex h-10 w-full appearance-none rounded-xl bg-white/[0.06] border border-white/[0.08] px-3 py-2 pr-8 text-sm text-white/90',
            'transition-all duration-200',
            'focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/30',
            error && 'border-rose-500/50 focus:ring-rose-500/30',
            className,
          )}
          ref={ref}
          {...props}
        >
          {children}
        </select>
        <ChevronDown className="absolute right-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30 pointer-events-none" />
      </div>
    );
  },
);
Select.displayName = 'Select';

export { Select };
