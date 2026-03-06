import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { GlassCard } from './GlassCard';
import { Colors } from '@/constants/colors';

interface StatCardProps {
  icon: React.ComponentProps<typeof Ionicons>['name'];
  value: string;
  label: string;
  color?: string;
}

export function StatCard({
  icon,
  value,
  label,
  color = Colors.primary,
}: StatCardProps) {
  return (
    <GlassCard style={styles.card}>
      {/* Colored left accent bar */}
      <View style={[styles.accent, { backgroundColor: color }]} />

      <View style={styles.content}>
        {/* Icon */}
        <View style={[styles.iconWrapper, { backgroundColor: `${color}20` }]}>
          <Ionicons name={icon} size={20} color={color} />
        </View>

        {/* Value */}
        <Text style={styles.value}>{value}</Text>

        {/* Label */}
        <Text style={styles.label} numberOfLines={2}>
          {label}
        </Text>
      </View>
    </GlassCard>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row',
    overflow: 'hidden',
    minHeight: 100,
  },
  accent: {
    width: 4,
    borderTopLeftRadius: 16,
    borderBottomLeftRadius: 16,
    flexShrink: 0,
  },
  content: {
    flex: 1,
    padding: 14,
    gap: 6,
  },
  iconWrapper: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 2,
  },
  value: {
    fontSize: 22,
    fontWeight: '800',
    color: Colors.text,
    letterSpacing: -0.5,
  },
  label: {
    fontSize: 12,
    fontWeight: '500',
    color: Colors.textSecondary,
    lineHeight: 16,
  },
});
