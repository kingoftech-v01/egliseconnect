import { View, StyleSheet, type ViewStyle, type StyleProp } from 'react-native';
import { BlurView } from 'expo-blur';
import { Colors } from '@/constants/colors';

interface GlassCardProps {
  intensity?: number;
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
}

export function GlassCard({ children, style, intensity = 40 }: GlassCardProps) {
  return (
    <View
      style={StyleSheet.flatten([
        {
          borderRadius: 16,
          overflow: 'hidden' as const,
          borderWidth: 1,
          borderColor: Colors.border,
        },
        style as ViewStyle,
      ])}
    >
      <BlurView intensity={intensity} tint="dark" style={{ flex: 1 }}>
        <View style={{ backgroundColor: Colors.surface, flex: 1 }}>
          {children as any}
        </View>
      </BlurView>
    </View>
  );
}
