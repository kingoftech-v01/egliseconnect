import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Linking,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { GradientBackground } from '@/components/ui/GradientBackground';
import { GlassCard } from '@/components/ui/GlassCard';
import { Avatar } from '@/components/ui/Avatar';
import { Badge } from '@/components/ui/Badge';
import { Colors } from '@/constants/colors';
import { api } from '@/lib/api';

// ─── Types ────────────────────────────────────────────────────────────────────

interface MemberGroup {
  id: number | string;
  name: string;
}

interface MemberDetail {
  id: number | string;
  full_name?: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
  address?: string;
  role?: string;
  member_number?: string;
  photo?: string | null;
  groups?: MemberGroup[];
}

// ─── Quick action button ──────────────────────────────────────────────────────

interface ActionButtonProps {
  icon: React.ComponentProps<typeof Ionicons>['name'];
  label: string;
  onPress: () => void;
  color?: string;
}

function ActionButton({ icon, label, onPress, color = Colors.primaryLight }: ActionButtonProps) {
  return (
    <TouchableOpacity style={styles.actionBtn} onPress={onPress} activeOpacity={0.75}>
      <View style={[styles.actionIconBox, { borderColor: color }]}>
        <Ionicons name={icon} size={22} color={color} />
      </View>
      <Text style={[styles.actionLabel, { color }]}>{label}</Text>
    </TouchableOpacity>
  );
}

// ─── Contact row ─────────────────────────────────────────────────────────────

interface ContactRowProps {
  icon: React.ComponentProps<typeof Ionicons>['name'];
  value?: string;
  label: string;
  isLast?: boolean;
}

function ContactRow({ icon, value, label, isLast = false }: ContactRowProps) {
  if (!value) return null;
  return (
    <View style={[styles.contactRow, !isLast && styles.contactRowBorder]}>
      <View style={styles.contactIconBox}>
        <Ionicons name={icon} size={16} color={Colors.primaryLight} />
      </View>
      <View style={{ flex: 1 }}>
        <Text style={styles.contactLabel}>{label}</Text>
        <Text style={styles.contactValue}>{value}</Text>
      </View>
    </View>
  );
}

// ─── Screen ───────────────────────────────────────────────────────────────────

export default function MemberDetailScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();

  const memberQuery = useQuery<MemberDetail>({
    queryKey: ['members', id],
    queryFn: () => (api as unknown as Record<string, Record<string, (id: string) => Promise<MemberDetail>>>).members.detail(id),
    enabled: !!id,
  });

  const member = memberQuery.data;

  const displayName =
    (member?.full_name ??
    [member?.first_name, member?.last_name].filter(Boolean).join(' ')) ||
    'Membre';

  // ── Quick action handlers ──
  function handleCall() {
    if (member?.phone) {
      Linking.openURL(`tel:${member.phone}`);
    }
  }

  function handleEmail() {
    if (member?.email) {
      Linking.openURL(`mailto:${member.email}`);
    }
  }

  function handleSms() {
    if (member?.phone) {
      Linking.openURL(`sms:${member.phone}`);
    }
  }

  return (
    <GradientBackground>
      <SafeAreaView style={styles.safeArea}>
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* ── Back button ── */}
          <TouchableOpacity
            style={styles.backBtn}
            onPress={() => router.back()}
            activeOpacity={0.7}
          >
            <Ionicons name="chevron-back" size={22} color={Colors.text} />
            <Text style={styles.backLabel}>Retour</Text>
          </TouchableOpacity>

          {/* ── Hero section ── */}
          <View style={styles.hero}>
            {memberQuery.isLoading ? (
              <View style={styles.avatarPlaceholder}>
                <Ionicons name="person-outline" size={40} color={Colors.textMuted} />
              </View>
            ) : (
              <Avatar src={member?.photo} name={displayName} size={88} />
            )}
            <Text style={styles.heroName}>
              {memberQuery.isLoading ? 'Chargement…' : displayName}
            </Text>
            {member?.role ? (
              <Badge label={member.role} variant="default" />
            ) : null}
            {member?.member_number ? (
              <Text style={styles.memberNumber}>#{member.member_number}</Text>
            ) : null}
          </View>

          {/* ── Coordonnées ── */}
          {(member?.email || member?.phone || member?.address) && (
            <>
              <Text style={styles.sectionLabel}>Coordonnées</Text>
              <GlassCard style={styles.contactCard}>
                <ContactRow
                  icon="mail-outline"
                  label="Courriel"
                  value={member?.email}
                />
                <ContactRow
                  icon="call-outline"
                  label="Téléphone"
                  value={member?.phone}
                />
                <ContactRow
                  icon="location-outline"
                  label="Adresse"
                  value={member?.address}
                  isLast
                />
              </GlassCard>
            </>
          )}

          {/* ── Groupes ── */}
          {member?.groups && member.groups.length > 0 && (
            <>
              <Text style={styles.sectionLabel}>Groupes</Text>
              <GlassCard style={styles.groupsCard}>
                <View style={styles.groupsInner}>
                  {member.groups.map((group) => (
                    <Badge key={group.id} label={group.name} variant="outline" />
                  ))}
                </View>
              </GlassCard>
            </>
          )}

          {/* ── Actions rapides ── */}
          <Text style={styles.sectionLabel}>Actions rapides</Text>
          <GlassCard style={styles.actionsCard}>
            <View style={styles.actionsRow}>
              <ActionButton
                icon="call-outline"
                label="Appeler"
                onPress={handleCall}
                color={Colors.success}
              />
              <View style={styles.actionDivider} />
              <ActionButton
                icon="mail-outline"
                label="Courriel"
                onPress={handleEmail}
                color={Colors.primaryLight}
              />
              <View style={styles.actionDivider} />
              <ActionButton
                icon="chatbubble-outline"
                label="Message"
                onPress={handleSms}
                color={Colors.info}
              />
            </View>
          </GlassCard>

          {/* Error state */}
          {memberQuery.isError && (
            <GlassCard style={styles.errorCard}>
              <View style={styles.errorInner}>
                <Ionicons name="alert-circle-outline" size={32} color={Colors.error} />
                <Text style={styles.errorText}>
                  Impossible de charger le profil de ce membre.
                </Text>
                <TouchableOpacity onPress={() => memberQuery.refetch()} activeOpacity={0.7}>
                  <Text style={styles.retryText}>Réessayer</Text>
                </TouchableOpacity>
              </View>
            </GlassCard>
          )}

          <View style={styles.bottomSpacer} />
        </ScrollView>
      </SafeAreaView>
    </GradientBackground>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 32,
  },

  // Back button
  backBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginBottom: 20,
    alignSelf: 'flex-start',
  },
  backLabel: {
    fontSize: 16,
    color: Colors.text,
    fontWeight: '500',
  },

  // Hero
  hero: {
    alignItems: 'center',
    gap: 10,
    marginBottom: 28,
  },
  avatarPlaceholder: {
    width: 88,
    height: 88,
    borderRadius: 44,
    backgroundColor: Colors.surfaceStrong,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: Colors.border,
  },
  heroName: {
    fontSize: 24,
    fontWeight: '700',
    color: Colors.text,
    textAlign: 'center',
    marginTop: 4,
  },
  memberNumber: {
    fontSize: 13,
    color: Colors.primaryLight,
    fontFamily: 'Courier',
    letterSpacing: 1,
  },

  // Section label
  sectionLabel: {
    fontSize: 13,
    fontWeight: '700',
    color: Colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 10,
    marginTop: 4,
  },

  // Contact card
  contactCard: {
    marginBottom: 20,
  },
  contactRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    paddingHorizontal: 16,
    paddingVertical: 13,
  },
  contactRowBorder: {
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  contactIconBox: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: 'rgba(124,58,237,0.12)',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
  },
  contactLabel: {
    fontSize: 11,
    color: Colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    fontWeight: '600',
    marginBottom: 2,
  },
  contactValue: {
    fontSize: 14,
    color: Colors.text,
    fontWeight: '500',
    lineHeight: 20,
  },

  // Groups card
  groupsCard: {
    marginBottom: 20,
  },
  groupsInner: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    padding: 16,
  },

  // Actions card
  actionsCard: {
    marginBottom: 24,
  },
  actionsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 8,
  },
  actionBtn: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 14,
    gap: 8,
  },
  actionIconBox: {
    width: 48,
    height: 48,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.surfaceStrong,
    borderWidth: 1,
  },
  actionLabel: {
    fontSize: 12,
    fontWeight: '600',
  },
  actionDivider: {
    width: 1,
    height: 56,
    backgroundColor: Colors.border,
  },

  // Error
  errorCard: {
    marginBottom: 20,
    borderColor: 'rgba(244,63,94,0.2)',
  },
  errorInner: {
    padding: 28,
    alignItems: 'center',
    gap: 10,
  },
  errorText: {
    color: Colors.textSecondary,
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
  },
  retryText: {
    color: Colors.primaryLight,
    fontSize: 14,
    fontWeight: '600',
    marginTop: 4,
  },

  bottomSpacer: {
    height: 20,
  },
});
