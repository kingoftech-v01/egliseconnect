import { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  KeyboardAvoidingView,
  ScrollView,
  Platform,
  TouchableOpacity,
} from 'react-native';
import { router } from 'expo-router';
import { GradientBackground } from '@/components/ui/GradientBackground';
import { GlassCard } from '@/components/ui/GlassCard';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Colors } from '@/constants/colors';
import { api } from '@/lib/api';
import { useAuthStore } from '@/stores/auth';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { setTokens } = useAuthStore();

  async function handleLogin() {
    setError(null);

    if (!email.trim() || !password.trim()) {
      setError('Veuillez remplir tous les champs.');
      return;
    }

    setLoading(true);
    try {
      const result = await api.auth.login({ email: email.trim(), password });
      setTokens(result.access, result.refresh);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message || 'Identifiants incorrects. Veuillez réessayer.');
      } else {
        setError('Identifiants incorrects. Veuillez réessayer.');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <GradientBackground>
      <SafeAreaView style={styles.safeArea}>
        <KeyboardAvoidingView
          style={styles.keyboardView}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
        >
          <ScrollView
            contentContainerStyle={styles.scrollContent}
            keyboardShouldPersistTaps="handled"
            showsVerticalScrollIndicator={false}
          >
            {/* Logo area */}
            <View style={styles.logoArea}>
              <View style={styles.logoIconContainer}>
                <Text style={styles.logoIcon}>✝</Text>
              </View>
              <Text style={styles.logoText}>EgliseConnect</Text>
              <View style={styles.logoDivider} />
            </View>

            {/* Heading */}
            <View style={styles.headingArea}>
              <Text style={styles.heading}>Bienvenue</Text>
              <Text style={styles.subtitle}>
                Connectez-vous à votre espace communautaire
              </Text>
            </View>

            {/* Form card */}
            <GlassCard style={styles.card}>
              <View style={styles.cardInner}>
                <Input
                  label="Adresse courriel"
                  placeholder="vous@exemple.com"
                  value={email}
                  onChangeText={(t) => {
                    setEmail(t);
                    if (error) setError(null);
                  }}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  autoCorrect={false}
                  autoComplete="email"
                  returnKeyType="next"
                />

                <Input
                  label="Mot de passe"
                  placeholder="Votre mot de passe"
                  value={password}
                  onChangeText={(t) => {
                    setPassword(t);
                    if (error) setError(null);
                  }}
                  secureTextEntry
                  autoCapitalize="none"
                  autoComplete="password"
                  returnKeyType="done"
                  onSubmitEditing={handleLogin}
                />

                {error && (
                  <View style={styles.errorContainer}>
                    <Text style={styles.errorIcon}>⚠</Text>
                    <Text style={styles.errorText}>{error}</Text>
                  </View>
                )}

                <Button
                  title="Se connecter"
                  onPress={handleLogin}
                  loading={loading}
                  size="lg"
                  style={styles.submitButton}
                />
              </View>
            </GlassCard>

            {/* Sign-up link */}
            <View style={styles.footer}>
              <Text style={styles.footerText}>Vous n'avez pas de compte?</Text>
              <TouchableOpacity
                onPress={() => router.push('/(auth)/signup')}
                activeOpacity={0.7}
              >
                <Text style={styles.footerLink}>Créer un compte</Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </GradientBackground>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingTop: 48,
    paddingBottom: 32,
    justifyContent: 'center',
  },

  // Logo
  logoArea: {
    alignItems: 'center',
    marginBottom: 32,
  },
  logoIconContainer: {
    width: 72,
    height: 72,
    borderRadius: 20,
    backgroundColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 14,
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.5,
    shadowRadius: 16,
    elevation: 10,
  },
  logoIcon: {
    fontSize: 32,
    color: Colors.white,
  },
  logoText: {
    fontSize: 28,
    fontWeight: '800',
    color: Colors.white,
    letterSpacing: 0.5,
  },
  logoDivider: {
    width: 48,
    height: 3,
    borderRadius: 2,
    backgroundColor: Colors.primary,
    marginTop: 12,
    opacity: 0.8,
  },

  // Heading
  headingArea: {
    alignItems: 'center',
    marginBottom: 28,
  },
  heading: {
    fontSize: 32,
    fontWeight: '700',
    color: Colors.text,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 20,
  },

  // Card
  card: {
    marginBottom: 24,
  },
  cardInner: {
    padding: 24,
    gap: 16,
  },

  // Error
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: 'rgba(244,63,94,0.12)',
    borderWidth: 1,
    borderColor: 'rgba(244,63,94,0.3)',
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 10,
    gap: 8,
  },
  errorIcon: {
    fontSize: 14,
    color: Colors.error,
    marginTop: 1,
  },
  errorText: {
    flex: 1,
    color: Colors.error,
    fontSize: 13,
    lineHeight: 18,
  },

  // Submit
  submitButton: {
    marginTop: 4,
  },

  // Footer
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 6,
  },
  footerText: {
    color: Colors.textSecondary,
    fontSize: 14,
  },
  footerLink: {
    color: Colors.primaryLight,
    fontSize: 14,
    fontWeight: '600',
  },
});
