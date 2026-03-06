import { useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
} from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { GradientBackground } from '@/components/ui/GradientBackground';
import { GlassCard } from '@/components/ui/GlassCard';
import { Colors } from '@/constants/colors';

// ─── Types ────────────────────────────────────────────────────────────────────

type NotificationType = 'info' | 'success' | 'warning' | 'alert';

interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  time: string;
  read: boolean;
}

// ─── Mock Data ────────────────────────────────────────────────────────────────

const MOCK_NOTIFICATIONS: Notification[] = [
  {
    id: '1',
    type: 'info',
    title: 'Rappel d\'événement',
    message: 'Le culte de dimanche commence dans 2 heures. Soyez prêts pour un temps de louange extraordinaire.',
    time: 'Il y a 30 min',
    read: false,
  },
  {
    id: '2',
    type: 'success',
    title: 'Don reçu',
    message: 'Votre don de 50,00 $ a été enregistré avec succès. Merci pour votre générosité.',
    time: 'Il y a 2 h',
    read: false,
  },
  {
    id: '3',
    type: 'warning',
    title: 'Inscription requise',
    message: 'La retraite de printemps se remplit rapidement — il ne reste que 5 places. Inscrivez-vous dès maintenant.',
    time: 'Il y a 5 h',
    read: false,
  },
  {
    id: '4',
    type: 'alert',
    title: 'Demande d\'aide urgente',
    message: 'Une famille de la communauté a besoin d\'un soutien immédiat. Contactez le bureau pastoral.',
    time: 'Hier, 18 h',
    read: true,
  },
  {
    id: '5',
    type: 'info',
    title: 'Nouveau message de groupe',
    message: 'Votre groupe de cellule a publié un nouveau message dans le fil de discussion.',
    time: 'Hier, 14 h',
    read: true,
  },
  {
    id: '6',
    type: 'success',
    title: 'Présence enregistrée',
    message: 'Votre présence au culte du dimanche a été enregistrée avec succès via le code QR.',
    time: 'Il y a 3 jours',
    read: true,
  },
  {
    id: '7',
    type: 'info',
    title: 'Infolettre disponible',
    message: 'La nouvelle infolettre mensuelle de l\'église est maintenant disponible. Découvrez les nouvelles de la communauté.',
    time: 'Il y a 4 jours',
    read: true,
  },
  {
    id: '8',
    type: 'warning',
    title: 'Mise à jour du profil',
    message: 'Votre profil est incomplet. Veuillez mettre à jour vos coordonnées pour rester en contact avec la communauté.',
    time: 'Il y a 1 sem.',
    read: true,
  },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

const TYPE_CONFIG: Record<
  NotificationType,
  { icon: React.ComponentProps<typeof Ionicons>['name']; color: string; bg: string }
> = {
  info: {
    icon: 'information-circle',
    color: Colors.info,
    bg: 'rgba(59,130,246,0.15)',
  },
  success: {
    icon: 'checkmark-circle',
    color: Colors.success,
    bg: 'rgba(16,185,129,0.15)',
  },
  warning: {
    icon: 'warning',
    color: Colors.warning,
    bg: 'rgba(245,158,11,0.15)',
  },
  alert: {
    icon: 'alert-circle',
    color: Colors.error,
    bg: 'rgba(244,63,94,0.15)',
  },
};

// ─── Notification Item ────────────────────────────────────────────────────────

function NotificationItem({
  item,
  onPress,
}: {
  item: Notification;
  onPress: (id: string) => void;
}) {
  const config = TYPE_CONFIG[item.type];

  return (
    <TouchableOpacity
      onPress={() => onPress(item.id)}
      activeOpacity={0.75}
      style={styles.itemWrapper}
    >
      <GlassCard style={[styles.card, !item.read && styles.cardUnread]}>
        <View style={styles.cardContent}>
          {/* Icon */}
          <View style={[styles.iconContainer, { backgroundColor: config.bg }]}>
            <Ionicons name={config.icon} size={22} color={config.color} />
          </View>

          {/* Body */}
          <View style={styles.body}>
            <View style={styles.titleRow}>
              <Text style={styles.title} numberOfLines={1}>
                {item.title}
              </Text>
              <Text style={styles.time}>{item.time}</Text>
            </View>
            <Text style={styles.message} numberOfLines={2}>
              {item.message}
            </Text>
          </View>

          {/* Unread dot */}
          {!item.read && <View style={styles.unreadDot} />}
        </View>
      </GlassCard>
    </TouchableOpacity>
  );
}

// ─── Main Screen ──────────────────────────────────────────────────────────────

export default function NotificationsScreen() {
  const [notifications, setNotifications] =
    useState<Notification[]>(MOCK_NOTIFICATIONS);

  const unreadCount = notifications.filter((n) => !n.read).length;

  function markAllRead() {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  }

  function markOneRead(id: string) {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  }

  return (
    <GradientBackground>
      <SafeAreaView style={styles.safeArea}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity
            onPress={() => router.back()}
            style={styles.backButton}
            activeOpacity={0.7}
          >
            <Ionicons name="chevron-back" size={24} color={Colors.text} />
          </TouchableOpacity>

          <View style={styles.headerCenter}>
            <Text style={styles.headerTitle}>Notifications</Text>
            {unreadCount > 0 && (
              <View style={styles.badge}>
                <Text style={styles.badgeText}>{unreadCount}</Text>
              </View>
            )}
          </View>

          {unreadCount > 0 ? (
            <TouchableOpacity
              onPress={markAllRead}
              style={styles.markAllButton}
              activeOpacity={0.7}
            >
              <Text style={styles.markAllText}>Tout lire</Text>
            </TouchableOpacity>
          ) : (
            <View style={styles.headerSpacer} />
          )}
        </View>

        {/* List */}
        <FlatList
          data={notifications}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <NotificationItem item={item} onPress={markOneRead} />
          )}
          contentContainerStyle={
            notifications.length === 0
              ? styles.emptyContainer
              : styles.listContent
          }
          showsVerticalScrollIndicator={false}
          ListEmptyComponent={
            <View style={styles.emptyState}>
              <View style={styles.emptyIconWrapper}>
                <Ionicons
                  name="notifications-off-outline"
                  size={48}
                  color={Colors.textMuted}
                />
              </View>
              <Text style={styles.emptyTitle}>Aucune notification</Text>
              <Text style={styles.emptySubtitle}>
                Vous êtes à jour — revenez plus tard.
              </Text>
            </View>
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

  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: Colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  headerCenter: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginHorizontal: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: Colors.text,
  },
  badge: {
    backgroundColor: Colors.primary,
    borderRadius: 999,
    minWidth: 20,
    height: 20,
    paddingHorizontal: 6,
    alignItems: 'center',
    justifyContent: 'center',
  },
  badgeText: {
    color: Colors.white,
    fontSize: 11,
    fontWeight: '700',
  },
  markAllButton: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  markAllText: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.primaryLight,
  },
  headerSpacer: {
    width: 68,
  },

  // List
  listContent: {
    padding: 16,
    gap: 10,
  },

  // Item
  itemWrapper: {
    marginBottom: 10,
  },
  card: {
    // no extra padding — content handles it
  },
  cardUnread: {
    borderColor: Colors.borderLight,
  },
  cardContent: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: 14,
    gap: 12,
  },
  iconContainer: {
    width: 44,
    height: 44,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  body: {
    flex: 1,
    gap: 4,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
  },
  title: {
    flex: 1,
    fontSize: 14,
    fontWeight: '700',
    color: Colors.text,
  },
  time: {
    fontSize: 11,
    color: Colors.textMuted,
    flexShrink: 0,
  },
  message: {
    fontSize: 13,
    color: Colors.textSecondary,
    lineHeight: 18,
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.primary,
    marginTop: 4,
    flexShrink: 0,
  },

  // Empty state
  emptyContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  emptyState: {
    alignItems: 'center',
    gap: 12,
  },
  emptyIconWrapper: {
    width: 88,
    height: 88,
    borderRadius: 999,
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: Colors.text,
  },
  emptySubtitle: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 20,
  },
});
