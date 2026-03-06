import { TouchableOpacity, Text, ActivityIndicator, StyleSheet, type ViewStyle } from 'react-native';
import { Colors } from '@/constants/colors';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'destructive';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: ButtonVariant;
  loading?: boolean;
  disabled?: boolean;
  style?: ViewStyle;
  size?: 'sm' | 'md' | 'lg';
}

export function Button({
  title,
  onPress,
  variant = 'primary',
  loading = false,
  disabled = false,
  style,
  size = 'md',
}: ButtonProps) {
  const isDisabled = disabled || loading;

  const bgColors: Record<ButtonVariant, string> = {
    primary: Colors.primary,
    secondary: Colors.surfaceStrong,
    ghost: 'transparent',
    destructive: '#f43f5e',
  };

  const heights: Record<string, number> = { sm: 36, md: 44, lg: 52 };

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={isDisabled}
      style={[
        styles.button,
        {
          backgroundColor: bgColors[variant],
          height: heights[size],
          opacity: isDisabled ? 0.5 : 1,
          borderWidth: variant === 'ghost' ? 0 : variant === 'secondary' ? 1 : 0,
          borderColor: Colors.border,
        },
        variant === 'primary' && styles.glow,
        style,
      ]}
      activeOpacity={0.7}
    >
      {loading ? (
        <ActivityIndicator color={Colors.white} size="small" />
      ) : (
        <Text style={[styles.text, variant === 'ghost' && { color: Colors.textSecondary }]}>
          {title}
        </Text>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    borderRadius: 12,
    paddingHorizontal: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  text: {
    color: Colors.white,
    fontWeight: '600',
    fontSize: 15,
  },
  glow: {
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 12,
    elevation: 8,
  },
});
