import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { GradientBackground } from '@/components/ui/GradientBackground';
import { GlassCard } from '@/components/ui/GlassCard';
import { Avatar } from '@/components/ui/Avatar';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Colors } from '@/constants/colors';
import { api } from '@/lib/api';
import { useAuthStore } from '@/stores/auth';

// ─── Types ────────────────────────────────────────────────────────────────────

interface UserProfile {
  id?: number | string;
  full_name?: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  role?: string;
  member_number?: string;
  photo?: string | null;
  stats?: {
    presences_ce_mois?: number;
    dons_ce_mois?: number;
    heures_benevolat?: number;
  };
}

// ─── Sub-components ───────────────────────────────────────────────────────────

interface MenuItemProps {
  icon: React.ComponentProps<typeof Ionicons>['name'];
  label: string;
  onPress: () => void;
  isLast?: boolean;
}

function MenuItem({ icon, label, onPress, isLast = false }: MenuItemProps) {
  return (
    <TouchableOpacity
      onPress={onPress}
      activeOpacity={0.7}
      style={[styles.menuItem, !isLast && styles.menuItemBorder]}
    >
      <View style={styles.menuItemLeft}>
        <View style={styles.menuIconBox}>
          <Ionicons name={icon} size={18} color={Colors.primaryLight} />
        </View>
        <Text style={styles.menuLabel}>{label}</Text>
      </View>
      <Ionicons name="chevron-forward" size={16} color={Colors.textMuted} />
    </TouchableOpacity>
  );
}

interface StatCardProps {
  value: string | number;
  label: string;
  icon: React.ComponentProps<typeof Ionicons>['name'];
  color: string;
}

function StatCard({ value, label, icon, color }: StatCardProps) {
  return (
    <GlassCard style={styles.statCard}>
      <View style={styles.statInner}>
        <View style={[styles.statIconBox, { backgroundColor: `${color}20` }]}>
          <Ionicons name={icon} size={18} color={color} />
        </View>
        <Text style={styles.statValue}>{value}</Text>
        <Text style={styles.statLabel}>{label}</Text>
      </View>
    </GlassCard>
  );
}

// ─── Screen ───────────────────────────────────────────────────────────────────

export default function ProfileScreen() {
  const router = useRouter();
  const { logout } = useAuthStore();

  const profileQuery = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: () => api.auth.me() as Promise<UserProfile>,
  });

  const profile = profileQuery.data;

  const displayName =
    (profile?.full_name ??
    [profile?.first_name, profile?.last_name].filter(Boolean).join(' ')) ||
    'Membre';

  const stats = profile?.stats;

  function handleLogout() {
    logout();
    router.replace('/(auth)/login');
  }

  return (
    <GradientBackground>
      <SafeAreaView style={styles.safeArea}>
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* ── Profile header card ── */}
          <GlassCard style={styles.profileCard}>
            <View style={styles.profileCardInner}>
              <Avatar
                src={profile?.photo}
                name={displayName}
                size={80}
              />
              <Text style={styles.fullName}>
                {profileQuery.isLoading ? 'Chargement…' : displayName}
              </Text>
              {profile?.email ? (
                <Text style={styles.email}>{profile.email}</Text>
              ) : null}
              {profile?.role ? (
                <Badge label={profile.role} variant="default" />
              ) : null}
              {profile?.member_number ? (
                <Text style={styles.memberNumber}>#{profile.member_number}</Text>
              ) : null}
            </View>
          </GlassCard>

          {/* ── Stats row ── */}
          <View style={styles.statsRow}>
            <StatCard
              value={stats?.presences_ce_mois ?? '—'}
              label="Présences"
              icon="checkmark-circle-outline"
              color={Colors.success}
            />
            <StatCard
              value={
                stats?.dons_ce_mois != null
                  ? `${stats.dons_ce_mois}$`
                  : '—'
              }
              label="Dons"
              icon="heart-outline"
              color="#f43f5e"
            />
            <StatCard
              value={
                stats?.heures_benevolat != null
                  ? `${stats.heures_benevolat}h`
                  : '—'
              }
              label="Bénévolat"
              icon="people-outline"
              color={Colors.warning}
            />
          </View>

          {/* ── Mon compte ── */}
          <Text style={styles.sectionLabel}>Mon compte</Text>
          <GlassCard style={styles.menuCard}>
            <MenuItem
              icon="person-outline"
              label="Mon profil"
              onPress={() => router.push('/profile/edit' as never)}
            />
            <MenuItem
              icon="heart-outline"
              label="Mes dons"
              onPress={() => router.push('/donations' as never)}
            />
            <MenuItem
              icon="calendar-outline"
              label="Mon planning"
              onPress={() => router.push('/volunteers/schedule' as never)}
              isLast
            />
          </GlassCard>

          {/* ── Préférences ── */}
          <Text style={styles.sectionLabel}>Préférences</Text>
          <GlassCard style={styles.menuCard}>
            <MenuItem
              icon="notifications-outline"
              label="Notifications"
              onPress={() => router.push('/settings/notifications' as never)}
            />
            <MenuItem
              icon="settings-outline"
              label="Paramètres"
              onPress={() => router.push('/settings' as never)}
              isLast
            />
          </GlassCard>

          {/* ── Danger zone ── */}
          <Text style={styles.sectionLabel}>Zone critique</Text>
          <GlassCard style={styles.dangerCard}>
            <View style={styles.dangerInner}>
              <View style={styles.dangerTextRow}>
                <Ionicons name="log-out-outline" size={20} color={Colors.error} />
                <View style={{ flex: 1 }}>
                  <Text style={styles.dangerTitle}>Se déconnecter</Text>
                  <Text style={styles.dangerDesc}>
                    Vous serez redirigé vers la page de connexion
                  </Text>
                </View>
              </View>
              <Button
                title="Se déconnecter"
                variant="destructive"
                size="md"
                onPress={handleLogout}
                style={styles.logoutBtn}
              />
            </View>
          </GlassCard>

          {/* App version */}
          <Text style={styles.versionText}>EgliseConnect · v1.0.0</Text>

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
    paddingTop: 20,
    paddingBottom: 32,
  },

  // Profile card
  profileCard: {
    marginBottom: 16,
  },
  profileCardInner: {
    padding: 28,
    alignItems: 'center',
    gap: 10,
  },
  fullName: {
    fontSize: 22,
    fontWeight: '700',
    color: Colors.text,
    textAlign: 'center',
    marginTop: 4,
  },
  email: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
  memberNumber: {
    fontSize: 13,
    color: Colors.primaryLight,
    fontFamily: 'Courier',
    letterSpacing: 1,
    marginTop: 2,
  },

  // Stats
  statsRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 24,
  },
  statCard: {
    flex: 1,
  },
  statInner: {
    padding: 14,
    alignItems: 'center',
    gap: 6,
  },
  statIconBox: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 2,
  },
  statValue: {
    fontSize: 18,
    fontWeight: '800',
    color: Colors.text,
  },
  statLabel: {
    fontSize: 11,
    color: Colors.textMuted,
    textAlign: 'center',
    fontWeight: '500',
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

  // Menu
  menuCard: {
    marginBottom: 20,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  menuItemBorder: {
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  menuItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  menuIconBox: {
    width: 34,
    height: 34,
    borderRadius: 9,
    backgroundColor: 'rgba(124,58,237,0.12)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  menuLabel: {
    fontSize: 15,
    fontWeight: '500',
    color: Colors.text,
  },

  // Danger zone
  dangerCard: {
    marginBottom: 20,
    borderColor: 'rgba(244,63,94,0.2)',
  },
  dangerInner: {
    padding: 16,
    gap: 14,
  },
  dangerTextRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  dangerTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.error,
  },
  dangerDesc: {
    fontSize: 12,
    color: Colors.textMuted,
    marginTop: 2,
  },
  logoutBtn: {
    width: '100%',
  },

  // Footer
  versionText: {
    fontSize: 12,
    color: Colors.textMuted,
    textAlign: 'center',
    marginTop: 4,
  },
  bottomSpacer: {
    height: 20,
  },
});
