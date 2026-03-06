import { View, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

export function GradientBackground({ children }: { children: React.JSX.Element | React.JSX.Element[] }) {
  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['#0f0a2e', '#1a1145', '#2d1b69'] as const}
        style={StyleSheet.absoluteFill}
      />
      {/* Decorative orbs */}
      <View style={StyleSheet.flatten([styles.orb, styles.orbPurple])} />
      <View style={StyleSheet.flatten([styles.orb, styles.orbBlue])} />
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  orb: {
    position: 'absolute',
    borderRadius: 999,
    opacity: 0.15,
  },
  orbPurple: {
    width: 300,
    height: 300,
    backgroundColor: '#7c3aed',
    top: -100,
    left: -50,
  },
  orbBlue: {
    width: 250,
    height: 250,
    backgroundColor: '#3b82f6',
    bottom: -80,
    right: -60,
  },
});
