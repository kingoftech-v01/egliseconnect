import { View, Text, StyleSheet } from 'react-native';
import { Image } from 'expo-image';
import { Colors } from '@/constants/colors';

interface AvatarProps {
  src?: string | null;
  name?: string;
  size?: number;
}

function getInitials(name?: string): string {
  if (!name) return '?';
  const parts = name.trim().split(' ');
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  return name[0].toUpperCase();
}

export function Avatar({ src, name, size = 40 }: AvatarProps) {
  if (src) {
    return (
      <Image
        source={{ uri: src }}
        style={[styles.image, { width: size, height: size, borderRadius: size / 2 }]}
        contentFit="cover"
      />
    );
  }

  return (
    <View
      style={[
        styles.fallback,
        { width: size, height: size, borderRadius: size / 2 },
      ]}
    >
      <Text style={[styles.initials, { fontSize: size * 0.38 }]}>
        {getInitials(name)}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  image: {
    borderWidth: 2,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  fallback: {
    backgroundColor: 'rgba(124,58,237,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  initials: {
    color: Colors.primaryLight,
    fontWeight: '700',
  },
});
