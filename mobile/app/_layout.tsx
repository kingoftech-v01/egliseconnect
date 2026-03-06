import { useEffect } from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '@/lib/query-client';
import { useAuthStore } from '@/stores/auth';
import { useRouter, useSegments } from 'expo-router';
import '../global.css';

function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, loadTokens } = useAuthStore();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    loadTokens();
  }, [loadTokens]);

  useEffect(() => {
    if (isLoading) return;
    const inAuth = segments[0] === '(auth)';

    if (!isAuthenticated && !inAuth) {
      router.replace('/(auth)/login');
    } else if (isAuthenticated && inAuth) {
      router.replace('/(tabs)');
    }
  }, [isAuthenticated, isLoading, segments, router]);

  if (isLoading) return null;
  return <>{children}</>;
}

export default function RootLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthGuard>
        <Stack
          screenOptions={{
            headerShown: false,
            contentStyle: { backgroundColor: '#0f0a2e' },
            animation: 'slide_from_right',
          }}
        >
          <Stack.Screen name="(auth)" />
          <Stack.Screen name="(tabs)" />
          <Stack.Screen name="events/[id]" options={{ presentation: 'card' }} />
          <Stack.Screen name="members/[id]" options={{ presentation: 'card' }} />
        </Stack>
        <StatusBar style="light" />
      </AuthGuard>
    </QueryClientProvider>
  );
}
