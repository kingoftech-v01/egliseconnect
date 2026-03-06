'use client';

import { useState, createContext, useContext, type ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface TabsContextValue {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const TabsContext = createContext<TabsContextValue | null>(null);

interface TabsProps {
  defaultValue: string;
  children: ReactNode;
  className?: string;
  onValueChange?: (value: string) => void;
}

export function Tabs({ defaultValue, children, className, onValueChange }: TabsProps) {
  const [activeTab, setActiveTabState] = useState(defaultValue);
  const setActiveTab = (tab: string) => {
    setActiveTabState(tab);
    onValueChange?.(tab);
  };
  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  );
}

export function TabsList({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={cn(
        'flex gap-1 rounded-xl bg-white/[0.04] p-1 border border-white/[0.06]',
        className,
      )}
    >
      {children}
    </div>
  );
}

export function TabsTrigger({
  value,
  children,
  className,
}: {
  value: string;
  children: ReactNode;
  className?: string;
}) {
  const ctx = useContext(TabsContext);
  if (!ctx) throw new Error('TabsTrigger must be in Tabs');
  const isActive = ctx.activeTab === value;

  return (
    <button
      onClick={() => ctx.setActiveTab(value)}
      className={cn(
        'px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200',
        isActive
          ? 'bg-primary/20 text-purple-300 shadow-[0_0_10px_rgba(124,58,237,0.15)]'
          : 'text-white/50 hover:text-white/70 hover:bg-white/[0.04]',
        className,
      )}
    >
      {children}
    </button>
  );
}

export function TabsContent({
  value,
  children,
  className,
}: {
  value: string;
  children: ReactNode;
  className?: string;
}) {
  const ctx = useContext(TabsContext);
  if (!ctx) throw new Error('TabsContent must be in Tabs');
  if (ctx.activeTab !== value) return null;

  return <div className={cn('mt-4', className)}>{children}</div>;
}
