import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useState } from 'react';

import { GradientBackground } from '@/components/ui/GradientBackground';
import { GlassCard } from '@/components/ui/GlassCard';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Avatar } from '@/components/ui/Avatar';
import { Colors } from '@/constants/colors';
import { api } from '@/lib/api';

// ─── Types ────────────────────────────────────────────────────────────────────

interface Attendee {
  id: number;
  name: string;
  avatar?: string | null;
}

interface EventDetail {
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
  attendees?: Attendee[];
  image?: string | null;
}

type RsvpStatus = 'confirmed' | 'maybe' | 'declined' | null;

// ─── Helpers ──────────────────────────────────────────────────────────────────

const MONTHS_FR = [
  'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
  'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre',
];
const DAYS_FR = ['dimanche', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi'];

function formatLongDate(iso: string) {
  const d = new Date(iso);
  return `${DAYS_FR[d.getDay()]} ${d.getDate()} ${MONTHS_FR[d.getMonth()]} ${d.getFullYear()}`;
}

function formatTime(iso: string) {
  const d = new Date(iso);
  return d.toLocaleTimeString('fr-CA', { hour: '2-digit', minute: '2-digit' });
}

function eventTypeLabel(event: EventDetail): string {
  if (event.event_type_display) return event.event_type_display;
  const map: Record<string, string> = { culte: 'Culte', groupe: 'Groupe', special: 'Spécial' };
  return map[event.event_type?.toLowerCase()] ?? event.event_type ?? 'Autre';
}

function eventTypeBadgeVariant(type: string): 'default' | 'success' | 'warning' | 'outline' {
  switch (type?.toLowerCase()) {
    case 'culte':    return 'default';
    case 'groupe':   return 'success';
    case 'special':
    case 'spécial':  return 'warning';
    default:         return 'outline';
  }
}

// ─── Capacity Bar ─────────────────────────────────────────────────────────────

function CapacityBar({ current, max }: { current: number; max: number }) {
  const pct = Math.min(current / max, 1);
  const color = pct >= 0.9 ? Colors.error : pct >= 0.7 ? Colors.warning : Colors.success;
  return (
    <View>
      <View style={styles.capRow}>
        <Text style={styles.capLabel}>Capacité</Text>
        <Text style={[styles.capCount, { color }]}>
          {current} / {max} places
        </Text>
      </View>
      <View style={styles.barTrack}>
        <View style={[styles.barFill, { width: `${pct * 100}%` as any, backgroundColor: color }]} />
      </View>
    </View>
  );
}

// ─── RSVP Button ──────────────────────────────────────────────────────────────

interface RsvpButtonProps {
  status: RsvpStatus;
  value: RsvpStatus;
  icon: string;
  label: string;
  onPress: () => void;
}

function RsvpButton({ status, value, icon, label, onPress }: RsvpButtonProps) {
  const active = status === value;
  return (
    <TouchableOpacity
      onPress={onPress}
      activeOpacity={0.7}
      style={[
        styles.rsvpBtn,
        active && styles.rsvpBtnActive,
      ]}
    >
      <Ionicons
        name={icon as any}
        size={18}
        color={active ? Colors.white : Colors.textSecondary}
      />
      <Text style={[styles.rsvpLabel, active && styles.rsvpLabelActive]}>
        {label}
      </Text>
    </TouchableOpacity>
  );
}

// ─── Main Screen ──────────────────────────────────────────────────────────────

export default function EventDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [rsvp, setRsvp] = useState<RsvpStatus>(null);

  const { data: event, isLoading, isError } = useQuery<EventDetail>({
    queryKey: ['events', id],
    queryFn: () => api.events.get(id!) as Promise<EventDetail>,
    enabled: !!id,
  });

  const rsvpMutation = useMutation({
    mutationFn: (status: RsvpStatus) =>
      (api as any).events.rsvp?.(Number(id), { status }) ?? Promise.resolve(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events', id] });
    },
  });

  const handleRsvp = (status: RsvpStatus) => {
    const next = rsvp === status ? null : status;
    setRsvp(next);
    rsvpMutation.mutate(next);
  };

  if (isLoading) {
    return (
      <GradientBackground>
        <SafeAreaView style={styles.safe}>
          <View style={styles.centered}>
            <ActivityIndicator size="large" color={Colors.primary} />
            <Text style={styles.loadingText}>Chargement…</Text>
          </View>
        </SafeAreaView>
      </GradientBackground>
    );
  }

  if (isError || !event) {
    return (
      <GradientBackground>
        <SafeAreaView style={styles.safe}>
          <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
            <Ionicons name="arrow-back" size={22} color={Colors.text} />
          </TouchableOpacity>
          <View style={styles.centered}>
            <Ionicons name="alert-circle-outline" size={48} color={Colors.error} />
            <Text style={styles.errorTitle}>Événement introuvable</Text>
            <Text style={styles.emptyText}>Impossible de charger cet événement.</Text>
          </View>
        </SafeAreaView>
      </GradientBackground>
    );
  }

  const typeLabel = eventTypeLabel(event);
  const badgeVariant = eventTypeBadgeVariant(event.event_type);
  const hasCapacity = event.capacity != null && event.capacity > 0;
  const attendees: Attendee[] = event.attendees ?? [];

  return (
    <GradientBackground>
      <SafeAreaView style={styles.safe}>
        {/* Back button — floats over hero */}
        <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={22} color={Colors.white} />
        </TouchableOpacity>

        <ScrollView
          style={styles.scroll}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Hero image area */}
          <View style={styles.hero}>
            <LinearGradient
              colors={['#2d1b69', '#7c3aed', '#1a1145']}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={styles.heroGradient}
            />
            {/* Pattern overlay */}
            <View style={styles.heroOverlay} />
            {/* Icon centerpiece */}
            <View style={styles.heroIconWrap}>
              <Ionicons name="calendar" size={52} color="rgba(255,255,255,0.25)" />
            </View>
            {/* Badge overlay */}
            <View style={styles.heroBadge}>
              <Badge label={typeLabel} variant={badgeVariant} />
            </View>
          </View>

          {/* Content body */}
          <View style={styles.body}>
            {/* Title */}
            <Text style={styles.title}>{event.title}</Text>

            {/* Date + time */}
            <View style={styles.infoRow}>
              <View style={styles.infoIconWrap}>
                <Ionicons name="calendar-outline" size={16} color={Colors.primaryLight} />
              </View>
              <View style={styles.infoText}>
                <Text style={styles.infoLabel}>Date</Text>
                <Text style={styles.infoValue}>{formatLongDate(event.start_datetime)}</Text>
              </View>
            </View>

            <View style={styles.infoRow}>
              <View style={styles.infoIconWrap}>
                <Ionicons name="time-outline" size={16} color={Colors.primaryLight} />
              </View>
              <View style={styles.infoText}>
                <Text style={styles.infoLabel}>Heure</Text>
                <Text style={styles.infoValue}>
                  {formatTime(event.start_datetime)}
                  {event.end_datetime ? ` – ${formatTime(event.end_datetime)}` : ''}
                </Text>
              </View>
            </View>

            {event.location ? (
              <View style={styles.infoRow}>
                <View style={styles.infoIconWrap}>
                  <Ionicons name="location-outline" size={16} color={Colors.primaryLight} />
                </View>
                <View style={styles.infoText}>
                  <Text style={styles.infoLabel}>Lieu</Text>
                  <Text style={styles.infoValue}>{event.location}</Text>
                </View>
              </View>
            ) : null}

            {/* Description */}
            {event.description ? (
              <GlassCard style={styles.descCard}>
                <View style={styles.descInner}>
                  <Text style={styles.sectionTitle}>À propos</Text>
                  <Text style={styles.descText}>{event.description}</Text>
                </View>
              </GlassCard>
            ) : null}

            {/* Capacity */}
            {hasCapacity ? (
              <GlassCard style={styles.capCard}>
                <View style={styles.descInner}>
                  <CapacityBar
                    current={event.attendees_count ?? 0}
                    max={event.capacity!}
                  />
                </View>
              </GlassCard>
            ) : null}

            {/* RSVP */}
            <GlassCard style={styles.rsvpCard}>
              <View style={styles.descInner}>
                <Text style={styles.sectionTitle}>Votre réponse</Text>
                <View style={styles.rsvpRow}>
                  <RsvpButton
                    status={rsvp}
                    value="confirmed"
                    icon="checkmark-circle-outline"
                    label="Confirmer"
                    onPress={() => handleRsvp('confirmed')}
                  />
                  <RsvpButton
                    status={rsvp}
                    value="maybe"
                    icon="help-circle-outline"
                    label="Peut-être"
                    onPress={() => handleRsvp('maybe')}
                  />
                  <RsvpButton
                    status={rsvp}
                    value="declined"
                    icon="close-circle-outline"
                    label="Décliner"
                    onPress={() => handleRsvp('declined')}
                  />
                </View>
                {rsvp && (
                  <Text style={styles.rsvpConfirmText}>
                    {rsvp === 'confirmed'
                      ? 'Vous avez confirmé votre présence.'
                      : rsvp === 'maybe'
                      ? 'Vous avez répondu « peut-être ».'
                      : 'Vous avez décliné cet événement.'}
                  </Text>
                )}
              </View>
            </GlassCard>

            {/* Attendees */}
            {attendees.length > 0 ? (
              <View style={styles.attendeesSection}>
                <Text style={styles.sectionTitle}>
                  Participants ({event.attendees_count ?? attendees.length})
                </Text>
                <FlatList
                  data={attendees}
                  keyExtractor={(a) => String(a.id)}
                  horizontal
                  showsHorizontalScrollIndicator={false}
                  contentContainerStyle={styles.attendeesList}
                  renderItem={({ item }) => (
                    <View style={styles.attendeeItem}>
                      <Avatar src={item.avatar} name={item.name} size={44} />
                      <Text style={styles.attendeeName} numberOfLines={1}>
                        {item.name.split(' ')[0]}
                      </Text>
                    </View>
                  )}
                />
              </View>
            ) : null}
          </View>
        </ScrollView>
      </SafeAreaView>
    </GradientBackground>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  safe: {
    flex: 1,
  },
  backBtn: {
    position: 'absolute',
    top: 56,
    left: 20,
    zIndex: 20,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(0,0,0,0.35)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 40,
  },

  // Hero
  hero: {
    height: 220,
    position: 'relative',
    overflow: 'hidden',
  },
  heroGradient: {
    ...StyleSheet.absoluteFillObject,
  },
  heroOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.2)',
  },
  heroIconWrap: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  heroBadge: {
    position: 'absolute',
    bottom: 16,
    left: 20,
  },

  // Body
  body: {
    padding: 20,
    gap: 14,
  },
  title: {
    fontSize: 26,
    fontWeight: '800',
    color: Colors.text,
    letterSpacing: -0.5,
    lineHeight: 32,
  },

  // Info rows
  infoRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  infoIconWrap: {
    width: 32,
    height: 32,
    borderRadius: 10,
    backgroundColor: 'rgba(124,58,237,0.15)',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    marginTop: 2,
  },
  infoText: {
    flex: 1,
    gap: 1,
  },
  infoLabel: {
    fontSize: 11,
    color: Colors.textMuted,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  infoValue: {
    fontSize: 15,
    color: Colors.text,
    fontWeight: '500',
  },

  // Cards
  descCard: {
    marginTop: 4,
  },
  descInner: {
    padding: 16,
    gap: 10,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: Colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
  },
  descText: {
    fontSize: 15,
    color: Colors.textSecondary,
    lineHeight: 22,
  },

  // Capacity
  capCard: {
    marginTop: 4,
  },
  capRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  capLabel: {
    fontSize: 14,
    fontWeight: '700',
    color: Colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
  },
  capCount: {
    fontSize: 13,
    fontWeight: '600',
  },
  barTrack: {
    height: 8,
    borderRadius: 999,
    backgroundColor: 'rgba(255,255,255,0.08)',
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
    borderRadius: 999,
  },

  // RSVP
  rsvpCard: {
    marginTop: 4,
  },
  rsvpRow: {
    flexDirection: 'row',
    gap: 8,
    justifyContent: 'space-between',
  },
  rsvpBtn: {
    flex: 1,
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    paddingVertical: 10,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.border,
    backgroundColor: 'rgba(255,255,255,0.04)',
  },
  rsvpBtnActive: {
    backgroundColor: Colors.primary,
    borderColor: Colors.primary,
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 8,
    elevation: 6,
  },
  rsvpLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.textSecondary,
  },
  rsvpLabelActive: {
    color: Colors.white,
  },
  rsvpConfirmText: {
    fontSize: 13,
    color: Colors.textMuted,
    textAlign: 'center',
    fontStyle: 'italic',
  },

  // Attendees
  attendeesSection: {
    gap: 12,
    marginTop: 4,
  },
  attendeesList: {
    gap: 14,
    paddingRight: 4,
  },
  attendeeItem: {
    alignItems: 'center',
    gap: 6,
    width: 56,
  },
  attendeeName: {
    fontSize: 11,
    color: Colors.textMuted,
    textAlign: 'center',
  },

  // Misc
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
  errorTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.textSecondary,
  },
  emptyText: {
    fontSize: 14,
    color: Colors.textMuted,
    textAlign: 'center',
    lineHeight: 20,
  },
});
