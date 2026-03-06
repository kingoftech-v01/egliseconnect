import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  Dimensions,
  type ViewStyle,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';

import { GradientBackground } from '@/components/ui/GradientBackground';
import { GlassCard } from '@/components/ui/GlassCard';
import { Avatar } from '@/components/ui/Avatar';
import { Button } from '@/components/ui/Button';
import { Colors } from '@/constants/colors';
import { api } from '@/lib/api';
import { useAuthStore } from '@/stores/auth';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const CARD_WIDTH = (SCREEN_WIDTH - 48 - 12) / 2; // padding 16*2 + gap 12 between 2 cards

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'Bonjour';
  if (hour < 18) return 'Bon après-midi';
  return 'Bonsoir';
}

function getFormattedDate(): string {
  return new Date().toLocaleDateString('fr-CA', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface DashboardStats {
  members_count: number;
  donations_total: string;
  events_count: number;
  volunteers_count: number;
}

interface StatCardData {
  icon: React.ComponentProps<typeof Ionicons>['name'];
  label: string;
  value: string;
  accent: string;
}

interface UpcomingEvent {
  id: number;
  title: string;
  location: string;
  date: string;     // e.g. "2026-03-15"
  time: string;     // e.g. "10:30"
  day: string;      // e.g. "15"
  month: string;    // e.g. "Mars"
}

interface ActivityItem {
  id: number;
  icon: React.ComponentProps<typeof Ionicons>['name'];
  iconColor: string;
  description: string;
  time: string;
}

// ---------------------------------------------------------------------------
// Mock data — replace with real queries once endpoints are ready
// ---------------------------------------------------------------------------

const MOCK_EVENTS: UpcomingEvent[] = [
  {
    id: 1,
    title: 'Culte du dimanche',
    location: 'Salle principale',
    date: '2026-03-08',
    time: '10h30',
    day: '08',
    month: 'Mars',
  },
  {
    id: 2,
    title: 'Groupe de prière',
    location: 'Salle de réunion B',
    date: '2026-03-11',
    time: '19h00',
    day: '11',
    month: 'Mars',
  },
  {
    id: 3,
    title: 'Repas communautaire',
    location: 'Sous-sol de l\'église',
    date: '2026-03-14',
    time: '12h00',
    day: '14',
    month: 'Mars',
  },
];

const MOCK_ACTIVITIES: ActivityItem[] = [
  {
    id: 1,
    icon: 'person-add',
    iconColor: Colors.success,
    description: 'Nouveau membre : Marie Tremblay',
    time: 'Il y a 2 h',
  },
  {
    id: 2,
    icon: 'heart',
    iconColor: '#fb7185',
    description: 'Don de 150 $ reçu',
    time: 'Il y a 4 h',
  },
  {
    id: 3,
    icon: 'calendar',
    iconColor: Colors.info,
    description: 'Événement confirmé : Culte du dimanche',
    time: 'Hier',
  },
  {
    id: 4,
    icon: 'hand-right',
    iconColor: Colors.warning,
    description: '3 nouveaux bénévoles inscrits',
    time: 'Hier',
  },
];

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function StatCard({ icon, label, value, accent }: StatCardData) {
  return (
    <GlassCard style={[styles.statCard, { width: CARD_WIDTH }]}>
      {/* Accent strip on the left */}
      <View style={[styles.accentStrip, { backgroundColor: accent }]} />
      <View style={styles.statContent}>
        <View style={[styles.statIconContainer, { backgroundColor: `${accent}20` }]}>
          <Ionicons name={icon} size={20} color={accent} />
        </View>
        <Text style={styles.statValue}>{value}</Text>
        <Text style={styles.statLabel}>{label}</Text>
      </View>
    </GlassCard>
  );
}

function EventCard({ event, onPress }: { event: UpcomingEvent; onPress: () => void }) {
  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.8}>
      <GlassCard style={styles.eventCard}>
        {/* Date badge */}
        <View style={styles.dateBadge}>
          <Text style={styles.dateBadgeDay}>{event.day}</Text>
          <Text style={styles.dateBadgeMonth}>{event.month}</Text>
        </View>

        {/* Event info */}
        <View style={styles.eventInfo}>
          <Text style={styles.eventTitle} numberOfLines={1}>
            {event.title}
          </Text>
          <View style={styles.eventMeta}>
            <Ionicons name="location-outline" size={12} color={Colors.textMuted} />
            <Text style={styles.eventMetaText} numberOfLines={1}>
              {event.location}
            </Text>
          </View>
          <View style={styles.eventMeta}>
            <Ionicons name="time-outline" size={12} color={Colors.textMuted} />
            <Text style={styles.eventMetaText}>{event.time}</Text>
          </View>
        </View>

        {/* Chevron */}
        <Ionicons name="chevron-forward" size={16} color={Colors.textMuted} />
      </GlassCard>
    </TouchableOpacity>
  );
}

function ActivityRow({ item }: { item: ActivityItem }) {
  const safeIcon = item.icon;

  return (
    <View style={styles.activityRow}>
      <View style={[styles.activityIcon, { backgroundColor: `${item.iconColor}1a` }]}>
        <Ionicons name={safeIcon} size={16} color={item.iconColor} />
      </View>
      <View style={styles.activityTextContainer}>
        <Text style={styles.activityDescription}>{item.description}</Text>
        <Text style={styles.activityTime}>{item.time}</Text>
      </View>
    </View>
  );
}

// ---------------------------------------------------------------------------
// Main screen
// ---------------------------------------------------------------------------

export default function HomeScreen() {
  const router = useRouter();

  // Auth store — user info
  const accessToken = useAuthStore((s) => s.accessToken);
  const userName = 'Utilisateur'; // TODO: replace with user.name once profile endpoint exists

  // Dashboard stats query
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: () => api.dashboard.stats() as Promise<DashboardStats>,
    enabled: !!accessToken,
  });

  // Build stat cards from API data (or show placeholders)
  const statCards: StatCardData[] = [
    {
      icon: 'people',
      label: 'Membres',
      value: statsLoading ? '—' : String(stats?.members_count ?? 0),
      accent: Colors.primary,
    },
    {
      icon: 'heart',
      label: 'Dons',
      value: statsLoading ? '—' : `${stats?.donations_total ?? '0'} $`,
      accent: '#fb7185',
    },
    {
      icon: 'calendar',
      label: 'Événements',
      value: statsLoading ? '—' : String(stats?.events_count ?? 0),
      accent: Colors.info,
    },
    {
      icon: 'hand-right',
      label: 'Bénévoles',
      value: statsLoading ? '—' : String(stats?.volunteers_count ?? 0),
      accent: Colors.warning,
    },
  ];

  return (
    <GradientBackground>
      <SafeAreaView style={styles.safeArea} edges={['top']}>
        <ScrollView
          style={styles.scroll}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* ----------------------------------------------------------------
              Header
          ---------------------------------------------------------------- */}
          <View style={styles.header}>
            <View style={styles.headerLeft}>
              <Text style={styles.greeting}>
                {getGreeting()}, {userName}
              </Text>
              <Text style={styles.dateText}>{getFormattedDate()}</Text>
            </View>
            <Avatar name={userName} size={46} />
          </View>

          {/* ----------------------------------------------------------------
              Stat cards  2x2 grid
          ---------------------------------------------------------------- */}
          <Text style={styles.sectionTitle}>Aperçu</Text>

          {statsLoading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator color={Colors.primary} size="large" />
            </View>
          ) : (
            <View style={styles.statsGrid}>
              {statCards.map((card) => (
                <StatCard key={card.label} {...card} />
              ))}
            </View>
          )}

          {/* ----------------------------------------------------------------
              Quick actions
          ---------------------------------------------------------------- */}
          <Text style={styles.sectionTitle}>Actions rapides</Text>

          <View style={styles.quickActions}>
            <Button
              title="Nouveau don"
              variant="primary"
              size="sm"
              style={styles.quickActionBtn}
              onPress={() => router.push('/(tabs)/donate')}
            />
            <Button
              title="Scanner QR"
              variant="secondary"
              size="sm"
              style={styles.quickActionBtn}
              onPress={() => router.push('/(tabs)/attendance')}
            />
            <Button
              title="Événements"
              variant="ghost"
              size="sm"
              style={{ ...styles.quickActionBtn, ...styles.ghostBtnBorder } as ViewStyle}
              onPress={() => router.push('/(tabs)/events')}
            />
          </View>

          {/* ----------------------------------------------------------------
              Upcoming events
          ---------------------------------------------------------------- */}
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Événements à venir</Text>
            <TouchableOpacity onPress={() => router.push('/(tabs)/events')}>
              <Text style={styles.seeAll}>Voir tout</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.eventsList}>
            {MOCK_EVENTS.map((event) => (
              <EventCard
                key={event.id}
                event={event}
                onPress={() => router.push(`/events/${event.id}`)}
              />
            ))}
          </View>

          {/* ----------------------------------------------------------------
              Recent activity
          ---------------------------------------------------------------- */}
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Activité récente</Text>
          </View>

          <GlassCard style={styles.activityCard}>
            {MOCK_ACTIVITIES.map((item, index) => (
              <View key={item.id}>
                <ActivityRow item={item} />
                {index < MOCK_ACTIVITIES.length - 1 && (
                  <View style={styles.activityDivider} />
                )}
              </View>
            ))}
          </GlassCard>

          {/* Bottom padding so last card clears the tab bar */}
          <View style={styles.bottomPad} />
        </ScrollView>
      </SafeAreaView>
    </GradientBackground>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 16,
  },

  // --- Header ---
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 20,
    paddingBottom: 24,
  },
  headerLeft: {
    flex: 1,
    marginRight: 12,
  },
  greeting: {
    fontSize: 22,
    fontWeight: '700',
    color: Colors.text,
    letterSpacing: 0.2,
  },
  dateText: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginTop: 3,
    textTransform: 'capitalize',
  },

  // --- Section headings ---
  sectionTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: Colors.text,
    marginBottom: 12,
    letterSpacing: 0.2,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
    marginTop: 24,
  },
  seeAll: {
    fontSize: 13,
    color: Colors.primaryLight,
    fontWeight: '600',
  },

  // --- Loading ---
  loadingContainer: {
    height: 160,
    alignItems: 'center',
    justifyContent: 'center',
  },

  // --- Stats grid ---
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 24,
  },
  statCard: {
    flexDirection: 'row',
    overflow: 'hidden',
    minHeight: 90,
  },
  accentStrip: {
    width: 4,
    borderTopLeftRadius: 16,
    borderBottomLeftRadius: 16,
  },
  statContent: {
    flex: 1,
    paddingVertical: 14,
    paddingHorizontal: 14,
  },
  statIconContainer: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10,
  },
  statValue: {
    fontSize: 22,
    fontWeight: '800',
    color: Colors.text,
    letterSpacing: -0.5,
  },
  statLabel: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 2,
    fontWeight: '500',
  },

  // --- Quick actions ---
  quickActions: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 0,
  },
  quickActionBtn: {
    flex: 1,
    borderRadius: 999,
  },
  ghostBtnBorder: {
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.15)',
  },

  // --- Event cards ---
  eventsList: {
    gap: 10,
  },
  eventCard: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 14,
    gap: 14,
    minHeight: 80,
  },
  dateBadge: {
    width: 46,
    height: 52,
    borderRadius: 12,
    backgroundColor: 'rgba(124,58,237,0.2)',
    borderWidth: 1,
    borderColor: 'rgba(124,58,237,0.35)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  dateBadgeDay: {
    fontSize: 18,
    fontWeight: '800',
    color: Colors.primaryLight,
    lineHeight: 22,
  },
  dateBadgeMonth: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  eventInfo: {
    flex: 1,
    gap: 4,
  },
  eventTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: Colors.text,
  },
  eventMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  eventMetaText: {
    fontSize: 12,
    color: Colors.textMuted,
    flex: 1,
  },

  // --- Activity feed ---
  activityCard: {
    paddingVertical: 4,
  },
  activityRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    gap: 12,
  },
  activityIcon: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  activityTextContainer: {
    flex: 1,
  },
  activityDescription: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.text,
    lineHeight: 18,
  },
  activityTime: {
    fontSize: 11,
    color: Colors.textMuted,
    marginTop: 2,
  },
  activityDivider: {
    height: 1,
    backgroundColor: Colors.border,
    marginLeft: 64,
  },

  bottomPad: {
    height: 32,
  },
});
