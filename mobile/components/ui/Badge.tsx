import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '@/constants/colors';

type BadgeVariant = 'default' | 'success' | 'warning' | 'destructive' | 'outline';

const variantStyles: Record<BadgeVariant, { bg: string; text: string; border: string }> = {
  default: { bg: 'rgba(124,58,237,0.2)', text: '#a78bfa', border: 'rgba(124,58,237,0.3)' },
  success: { bg: 'rgba(16,185,129,0.2)', text: '#34d399', border: 'rgba(16,185,129,0.3)' },
  warning: { bg: 'rgba(245,158,11,0.2)', text: '#fbbf24', border: 'rgba(245,158,11,0.3)' },
  destructive: { bg: 'rgba(244,63,94,0.2)', text: '#fb7185', border: 'rgba(244,63,94,0.3)' },
  outline: { bg: 'transparent', text: Colors.textSecondary, border: Colors.borderLight },
};

interface BadgeProps {
  label: string;
  variant?: BadgeVariant;
}

export function Badge({ label, variant = 'default' }: BadgeProps) {
  const v = variantStyles[variant];
  return (
    <View style={[styles.badge, { backgroundColor: v.bg, borderColor: v.border }]}>
      <Text style={[styles.text, { color: v.text }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 999,
    borderWidth: 1,
    alignSelf: 'flex-start',
  },
  text: {
    fontSize: 11,
    fontWeight: '600',
  },
});
