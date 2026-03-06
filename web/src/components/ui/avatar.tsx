import { cn } from '@/lib/utils';

interface AvatarProps {
  src?: string | null;
  fallback: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizeClasses = {
  sm: 'h-8 w-8 text-xs',
  md: 'h-10 w-10 text-sm',
  lg: 'h-12 w-12 text-base',
};

export function Avatar({ src, fallback, size = 'md', className }: AvatarProps) {
  const initials = fallback
    .split(' ')
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  if (src) {
    return (
      <img
        src={src}
        alt={fallback}
        className={cn(
          'rounded-full object-cover ring-2 ring-white/10',
          sizeClasses[size],
          className,
        )}
      />
    );
  }

  return (
    <div
      className={cn(
        'rounded-full bg-primary/20 flex items-center justify-center font-medium text-purple-300 ring-2 ring-white/10',
        sizeClasses[size],
        className,
      )}
    >
      {initials}
    </div>
  );
}
