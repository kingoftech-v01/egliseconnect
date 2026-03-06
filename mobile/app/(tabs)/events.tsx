import {
  View,
  Text,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useState } from 'react';

import { GradientBackground } from '@/components/ui/GradientBackground';
import { GlassCard } from '@/components/ui/GlassCard';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Colors } from '@/constants/colors';
import { useInfiniteEvents } from '@/hooks/use-events';

// ─── Types ────────────────────────────────────────────────────────────────────

interface Event {
  id: number;
  title: string;
  event_type: string;
  event_type_display?: string;
  start_datetime: string;
  end_datetime?: string;
  location?: string;
  description?: string;
  capacity?: number;
  attendees_count?: number;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const MONTHS_FR = [
  'JAN', 'FÉV', 'MAR', 'AVR', 'MAI', 'JUN',
  'JUL', 'AOÛ', 'SEP', 'OCT', 'NOV', 'DÉC',
];

function parseDate(iso: string) {
  const d = new Date(iso);
  return {
    month: MONTHS_FR[d.getMonth()],
    day: d.getDate(),
    time: d.toLocaleTimeString('fr-CA', { hour: '2-digit', minute: '2-digit' }),
  };
}

function eventTypeBadgeVariant(type: string): 'default' | 'success' | 'warning' | 'outline' {
  switch (type?.toLowerCase()) {
    case 'culte':       return 'default';
    case 'groupe':      return 'success';
    case 'special':
    case 'spécial':     return 'warning';
    default:            return 'outline';
  }
}

function eventTypeLabel(event: Event): string {
  if (event.event_type_display) return event.event_type_display;
  const map: Record<string, string> = {
    culte: 'Culte',
    groupe: 'Groupe',
    special: 'Spécial',
  };
  return map[event.event_type?.toLowerCase()] ?? event.event_type ?? 'Autre';
}

// ─── Event Card ───────────────────────────────────────────────────────────────

interface EventCardProps {
  item: Event;
  onPress: () => void;
}

function EventCard({ item, onPress }: EventCardProps) {
  const { month, day, time } = parseDate(item.start_datetime);
  const label = eventTypeLabel(item);
  const variant = eventTypeBadgeVariant(item.event_type);

  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.75} style={styles.cardTouchable}>
      <GlassCard style={styles.card}>
        <View style={styles.cardInner}>
          {/* Date block */}
          <View style={styles.dateBlock}>
            <Text style={styles.dateMonth}>{month}</Text>
            <Text style={styles.dateDay}>{day}</Text>
          </View>

          {/* Content */}
          <View style={styles.cardContent}>
            <View style={styles.cardTop}>
              <Badge label={label} variant={variant} />
            </View>
            <Text style={styles.eventTitle} numberOfLines={2}>{item.title}</Text>

            {item.location ? (
              <View style={styles.metaRow}>
                <Ionicons name="location-outline" size={13} color={Colors.textMuted} />
                <Text style={styles.metaText} numberOfLines={1}>{item.location}</Text>
              </View>
            ) : null}

            <View style={styles.metaRow}>
              <Ionicons name="time-outline" size={13} color={Colors.textMuted} />
              <Text style={styles.metaText}>{time}</Text>
              {item.attendees_count != null ? (
                <>
                  <View style={styles.metaDot} />
                  <Ionicons name="people-outline" size={13} color={Colors.textMuted} />
                  <Text style={styles.metaText}>{item.attendees_count}</Text>
                  {item.capacity ? (
                    <Text style={styles.metaMuted}>/{item.capacity}</Text>
                  ) : null}
                </>
              ) : null}
            </View>
          </View>

          {/* Chevron */}
          <Ionicons name="chevron-forward" size={16} color={Colors.textMuted} style={styles.chevron} />
        </View>
      </GlassCard>
    </TouchableOpacity>
  );
}

// ─── Main Screen ──────────────────────────────────────────────────────────────

export default function EventsScreen() {
  const router = useRouter();
  const [search, setSearch] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  const {
    data,
    isLoading,
    isError,
    refetch,
    hasNextPage,
    fetchNextPage,
    isFetchingNextPage,
  } = useInfiniteEvents({ search: search || undefined });

  const events: Event[] = data?.pages.flatMap((p) => p.results as unknown as Event[]) ?? [];

  const onRefresh = async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  };

  return (
    <GradientBackground>
      <SafeAreaView style={styles.safe}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Événements</Text>
          <Text style={styles.headerSub}>
            {data?.pages[0]?.count ?? events.length} événement{(data?.pages[0]?.count ?? events.length) !== 1 ? 's' : ''}
          </Text>
        </View>

        {/* Search */}
        <View style={styles.searchWrap}>
          <Input
            placeholder="Rechercher un événement..."
            value={search}
            onChangeText={setSearch}
            style={styles.searchInput}
          />
          <Ionicons name="search" size={18} color={Colors.textMuted} style={styles.searchIcon} />
        </View>

        {/* States */}
        {isLoading && !refreshing ? (
          <View style={styles.centered}>
            <ActivityIndicator size="large" color={Colors.primary} />
            <Text style={styles.loadingText}>Chargement des événements…</Text>
          </View>
        ) : isError ? (
          <View style={styles.centered}>
            <Ionicons name="cloud-offline-outline" size={48} color={Colors.textMuted} />
            <Text style={styles.emptyTitle}>Impossible de charger</Text>
            <Text style={styles.emptyText}>Vérifiez votre connexion et réessayez.</Text>
          </View>
        ) : (
          <FlatList
            data={events}
            keyExtractor={(item) => String(item.id)}
            contentContainerStyle={styles.list}
            showsVerticalScrollIndicator={false}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={onRefresh}
                tintColor={Colors.primary}
                colors={[Colors.primary]}
              />
            }
            onEndReached={() => {
              if (hasNextPage) fetchNextPage();
            }}
            onEndReachedThreshold={0.5}
            renderItem={({ item }) => (
              <EventCard
                item={item}
                onPress={() => router.push(`/events/${item.id}` as any)}
              />
            )}
            ListFooterComponent={
              isFetchingNextPage ? (
                <View style={styles.footerLoader}>
                  <ActivityIndicator size="small" color={Colors.primary} />
                </View>
              ) : null
            }
            ListEmptyComponent={
              <View style={styles.emptyWrap}>
                <Ionicons name="calendar-outline" size={56} color={Colors.textMuted} />
                <Text style={styles.emptyTitle}>Aucun événement</Text>
                <Text style={styles.emptyText}>
                  {search
                    ? 'Aucun résultat pour votre recherche.'
                    : 'Il n\'y a aucun événement à afficher pour le moment.'}
                </Text>
              </View>
            }
          />
        )}
      </SafeAreaView>
    </GradientBackground>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  safe: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 4,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: Colors.text,
    letterSpacing: -0.5,
  },
  headerSub: {
    fontSize: 13,
    color: Colors.textMuted,
    marginTop: 2,
  },
  searchWrap: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    position: 'relative',
  },
  searchInput: {
    paddingLeft: 40,
  },
  searchIcon: {
    position: 'absolute',
    left: 32,
    top: '50%',
    transform: [{ translateY: -9 }],
  },
  list: {
    paddingHorizontal: 20,
    paddingBottom: 24,
    gap: 12,
  },
  cardTouchable: {
    borderRadius: 16,
  },
  card: {
    borderRadius: 16,
  },
  cardInner: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
    gap: 14,
  },
  dateBlock: {
    width: 50,
    height: 60,
    borderRadius: 12,
    backgroundColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 8,
    elevation: 6,
    flexShrink: 0,
  },
  dateMonth: {
    fontSize: 10,
    fontWeight: '700',
    color: 'rgba(255,255,255,0.8)',
    letterSpacing: 1,
  },
  dateDay: {
    fontSize: 22,
    fontWeight: '800',
    color: Colors.white,
    lineHeight: 26,
  },
  cardContent: {
    flex: 1,
    gap: 4,
  },
  cardTop: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  eventTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.text,
    lineHeight: 20,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    flexWrap: 'nowrap',
  },
  metaText: {
    fontSize: 12,
    color: Colors.textMuted,
  },
  metaMuted: {
    fontSize: 12,
    color: Colors.textMuted,
    opacity: 0.6,
  },
  metaDot: {
    width: 3,
    height: 3,
    borderRadius: 999,
    backgroundColor: Colors.textMuted,
    marginHorizontal: 2,
  },
  chevron: {
    flexShrink: 0,
  },
  centered: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    paddingHorizontal: 40,
  },
  loadingText: {
    fontSize: 14,
    color: Colors.textMuted,
    marginTop: 8,
  },
  footerLoader: {
    paddingVertical: 20,
    alignItems: 'center',
  },
  emptyWrap: {
    alignItems: 'center',
    paddingTop: 80,
    gap: 10,
    paddingHorizontal: 32,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.textSecondary,
    marginTop: 8,
  },
  emptyText: {
    fontSize: 14,
    color: Colors.textMuted,
    textAlign: 'center',
    lineHeight: 20,
  },
});
