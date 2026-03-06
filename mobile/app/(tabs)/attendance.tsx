import { View, Text, StyleSheet, ScrollView, FlatList, TouchableOpacity, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { GradientBackground } from '@/components/ui/GradientBackground';
import { GlassCard } from '@/components/ui/GlassCard';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Colors } from '@/constants/colors';
import { api } from '@/lib/api';
import { useInfiniteSessions } from '@/hooks/use-attendance';

// ─── Types ────────────────────────────────────────────────────────────────────

interface QrCodeData {
  qr_code_url?: string;
  member_name?: string;
  member_number?: string;
}

interface Session {
  id: number | string;
  name: string;
  date?: string;
  service_type?: string;
}

interface AttendanceRecord {
  id: number | string;
  session_name?: string;
  session_type?: string;
  date?: string;
  time_in?: string;
  time_out?: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatDate(dateStr?: string): string {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleDateString('fr-CA', { day: 'numeric', month: 'short', year: 'numeric' });
}

function formatTime(timeStr?: string): string {
  if (!timeStr) return '—';
  return timeStr.slice(0, 5);
}

function sessionTypeBadgeVariant(type?: string): 'default' | 'success' | 'warning' | 'outline' {
  if (!type) return 'outline';
  const t = type.toLowerCase();
  if (t.includes('culte') || t.includes('sunday') || t.includes('dimanche')) return 'default';
  if (t.includes('jeune') || t.includes('youth')) return 'success';
  if (t.includes('prière') || t.includes('prayer')) return 'warning';
  return 'outline';
}

// ─── Screen ───────────────────────────────────────────────────────────────────

export default function AttendanceScreen() {
  const router = useRouter();

  const qrQuery = useQuery({
    queryKey: ['attendance', 'qr-mine'],
    queryFn: () => api.attendance.qrCode.mine() as Promise<QrCodeData>,
  });

  const sessionsQuery = useQuery({
    queryKey: ['attendance', 'sessions'],
    queryFn: async () => {
      const res = await api.attendance.sessions.list();
      return (res?.results ?? []) as Session[];
    },
  });

  const historyQuery = useInfiniteSessions();

  const qr = qrQuery.data;
  const sessions = sessionsQuery.data ?? [];
  const history: AttendanceRecord[] = historyQuery.data?.pages.flatMap(
    (p) => p.results as unknown as AttendanceRecord[],
  ) ?? [];

  const historyHeader = (
    <>
      {/* ── Header ── */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Présence</Text>
        <Text style={styles.headerSubtitle}>Gérez vos présences et votre QR</Text>
      </View>

      {/* ── Ma carte QR ── */}
      <Text style={styles.sectionLabel}>Ma carte QR</Text>
      <GlassCard style={styles.qrCard}>
        <View style={styles.qrCardInner}>
          {/* QR placeholder */}
          <View style={styles.qrBox}>
            <Ionicons name="qr-code-outline" size={64} color={Colors.primaryLight} />
          </View>

          {/* Member info */}
          <Text style={styles.memberName}>
            {qr?.member_name ?? (qrQuery.isLoading ? 'Chargement…' : 'Nom du membre')}
          </Text>
          {qr?.member_number ? (
            <Text style={styles.memberNumber}>#{qr.member_number}</Text>
          ) : null}

          {/* Regenerate */}
          <Button
            title="Régénérer"
            variant="ghost"
            size="sm"
            style={styles.regenerateBtn}
            onPress={() => qrQuery.refetch()}
          />
        </View>
      </GlassCard>

      {/* ── Check-in rapide ── */}
      <Text style={styles.sectionLabel}>Check-in rapide</Text>
      <GlassCard style={styles.checkinCard}>
        <View style={styles.checkinInner}>
          {/* Session pills */}
          {sessions.length > 0 && (
            <>
              <Text style={styles.subLabel}>Séances récentes</Text>
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={styles.pillsRow}
              >
                {sessions.map((session) => (
                  <TouchableOpacity
                    key={session.id}
                    activeOpacity={0.75}
                    onPress={() => api.attendance.checkIn({ qr_code: '', session_id: String(session.id) })}
                  >
                    <GlassCard style={styles.sessionPill} intensity={30}>
                      <View style={styles.pillContent}>
                        <Text style={styles.pillText}>{session.name}</Text>
                        {session.date ? (
                          <Text style={styles.pillDate}>{formatDate(session.date)}</Text>
                        ) : null}
                      </View>
                    </GlassCard>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </>
          )}

          {sessionsQuery.isLoading && (
            <Text style={styles.loadingText}>Chargement des séances…</Text>
          )}

          {/* Action buttons */}
          <View style={styles.actionButtons}>
            <Button
              title="Scanner un QR"
              variant="primary"
              size="md"
              style={styles.scanBtn}
              onPress={() => router.push('/scanner' as never)}
            />
            <Button
              title="Check-in manuel"
              variant="secondary"
              size="md"
              style={styles.manualBtn}
              onPress={() => router.push('/checkin' as never)}
            />
          </View>

          {/* Camera icon row */}
          <View style={styles.scanHint}>
            <Ionicons name="camera-outline" size={16} color={Colors.textMuted} />
            <Text style={styles.scanHintText}>
              Scannez le code d'un autre membre pour l'enregistrer
            </Text>
          </View>
        </View>
      </GlassCard>

      {/* ── Historique ── */}
      <Text style={styles.sectionLabel}>Historique</Text>

      {historyQuery.isLoading && (
        <GlassCard style={styles.emptyCard}>
          <Text style={styles.emptyText}>Chargement de l'historique…</Text>
        </GlassCard>
      )}
    </>
  );

  return (
    <GradientBackground>
      <SafeAreaView style={styles.safeArea}>
        <FlatList
          data={history}
          keyExtractor={(item) => String(item.id)}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          ListHeaderComponent={historyHeader}
          onEndReached={() => {
            if (historyQuery.hasNextPage) historyQuery.fetchNextPage();
          }}
          onEndReachedThreshold={0.5}
          renderItem={({ item: record }) => (
            <GlassCard style={styles.historyRow}>
              <View style={styles.historyInner}>
                {/* Left: icon + date */}
                <View style={styles.historyLeft}>
                  <View style={styles.historyIconBox}>
                    <Ionicons name="checkmark-circle" size={20} color={Colors.success} />
                  </View>
                  <View>
                    <Text style={styles.historyDate}>{formatDate(record.date)}</Text>
                    <Text style={styles.historySession}>
                      {record.session_name ?? 'Séance'}
                    </Text>
                  </View>
                </View>

                {/* Right: badge + time */}
                <View style={styles.historyRight}>
                  <Badge
                    label={record.session_type ?? 'Culte'}
                    variant={sessionTypeBadgeVariant(record.session_type)}
                  />
                  <Text style={styles.historyTime}>
                    {formatTime(record.time_in)}
                    {record.time_out ? ` – ${formatTime(record.time_out)}` : ''}
                  </Text>
                </View>
              </View>
            </GlassCard>
          )}
          ListFooterComponent={
            historyQuery.isFetchingNextPage ? (
              <View style={styles.footerLoader}>
                <ActivityIndicator size="small" color={Colors.primary} />
              </View>
            ) : (
              <View style={styles.bottomSpacer} />
            )
          }
          ListEmptyComponent={
            !historyQuery.isLoading ? (
              <GlassCard style={styles.emptyCard}>
                <View style={styles.emptyInner}>
                  <Ionicons name="calendar-outline" size={32} color={Colors.textMuted} />
                  <Text style={styles.emptyText}>Aucune présence enregistrée</Text>
                </View>
              </GlassCard>
            ) : null
          }
        />
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

  // Header
  header: {
    marginBottom: 28,
  },
  headerTitle: {
    fontSize: 32,
    fontWeight: '800',
    color: Colors.text,
    letterSpacing: 0.3,
  },
  headerSubtitle: {
    fontSize: 14,
    color: Colors.textSecondary,
    marginTop: 4,
  },

  // Section labels
  sectionLabel: {
    fontSize: 13,
    fontWeight: '700',
    color: Colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 10,
    marginTop: 4,
  },

  // QR card
  qrCard: {
    marginBottom: 28,
  },
  qrCardInner: {
    padding: 28,
    alignItems: 'center',
    gap: 12,
  },
  qrBox: {
    width: 180,
    height: 180,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: Colors.primaryLight,
    borderStyle: 'dashed',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(124,58,237,0.06)',
    marginBottom: 8,
  },
  memberName: {
    fontSize: 18,
    fontWeight: '700',
    color: Colors.text,
    textAlign: 'center',
  },
  memberNumber: {
    fontSize: 13,
    color: Colors.primaryLight,
    fontFamily: 'Courier',
    letterSpacing: 1,
  },
  regenerateBtn: {
    marginTop: 4,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: 12,
    paddingHorizontal: 20,
  },

  // Check-in card
  checkinCard: {
    marginBottom: 28,
  },
  checkinInner: {
    padding: 20,
    gap: 14,
  },
  subLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
  },
  pillsRow: {
    gap: 10,
    paddingRight: 4,
  },
  sessionPill: {
    marginRight: 0,
  },
  pillContent: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    alignItems: 'center',
    minWidth: 110,
  },
  pillText: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.text,
    textAlign: 'center',
  },
  pillDate: {
    fontSize: 11,
    color: Colors.textSecondary,
    marginTop: 2,
    textAlign: 'center',
  },
  loadingText: {
    fontSize: 13,
    color: Colors.textMuted,
    textAlign: 'center',
    paddingVertical: 8,
  },
  actionButtons: {
    gap: 10,
    marginTop: 4,
  },
  scanBtn: {
    width: '100%',
  },
  manualBtn: {
    width: '100%',
  },
  scanHint: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    justifyContent: 'center',
  },
  scanHintText: {
    fontSize: 12,
    color: Colors.textMuted,
    flex: 1,
    textAlign: 'center',
  },

  // History
  emptyCard: {
    marginBottom: 12,
  },
  emptyInner: {
    padding: 32,
    alignItems: 'center',
    gap: 10,
  },
  emptyText: {
    color: Colors.textMuted,
    fontSize: 14,
    textAlign: 'center',
    padding: 24,
  },
  historyRow: {
    marginBottom: 10,
  },
  historyInner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 14,
    gap: 12,
  },
  historyLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  historyIconBox: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: 'rgba(16,185,129,0.12)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  historyDate: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.text,
  },
  historySession: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 1,
  },
  historyRight: {
    alignItems: 'flex-end',
    gap: 4,
  },
  historyTime: {
    fontSize: 11,
    color: Colors.textMuted,
    fontFamily: 'Courier',
  },

  footerLoader: {
    paddingVertical: 20,
    alignItems: 'center',
  },
  bottomSpacer: {
    height: 20,
  },
});
