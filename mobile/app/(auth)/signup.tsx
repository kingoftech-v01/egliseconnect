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

// ----- helpers ---------------------------------------------------------------

function isValidEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
}

// ----- component -------------------------------------------------------------

export default function SignupScreen() {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [invitationCode, setInvitationCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Per-field validation errors
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const { setTokens } = useAuthStore();

  function clearFieldError(field: string) {
    if (fieldErrors[field]) {
      setFieldErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
    if (error) setError(null);
  }

  function validate(): boolean {
    const errors: Record<string, string> = {};

    if (!firstName.trim()) errors.firstName = 'Le prénom est requis.';
    if (!lastName.trim()) errors.lastName = 'Le nom est requis.';
    if (!email.trim()) {
      errors.email = "L'adresse courriel est requise.";
    } else if (!isValidEmail(email)) {
      errors.email = "L'adresse courriel n'est pas valide.";
    }
    if (!password) {
      errors.password = 'Le mot de passe est requis.';
    } else if (password.length < 8) {
      errors.password = 'Le mot de passe doit contenir au moins 8 caractères.';
    }
    if (!confirmPassword) {
      errors.confirmPassword = 'Veuillez confirmer votre mot de passe.';
    } else if (password !== confirmPassword) {
      errors.confirmPassword = 'Les mots de passe ne correspondent pas.';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function handleSignup() {
    setError(null);
    if (!validate()) return;

    setLoading(true);
    try {
      const payload = {
        email: email.trim(),
        password,
        password_confirm: confirmPassword,
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        ...(invitationCode.trim() ? { invitation_code: invitationCode.trim() } : {}),
      };

      const result = await api.auth.register(payload) as { access: string; refresh: string };
      setTokens(result.access, result.refresh);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message || "Une erreur est survenue lors de l'inscription.");
      } else {
        setError("Une erreur est survenue lors de l'inscription.");
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
            {/* Back button */}
            <TouchableOpacity
              style={styles.backButton}
              onPress={() => router.back()}
              activeOpacity={0.7}
            >
              <Text style={styles.backArrow}>←</Text>
              <Text style={styles.backLabel}>Retour</Text>
            </TouchableOpacity>

            {/* Heading */}
            <View style={styles.headingArea}>
              <Text style={styles.heading}>Créer un compte</Text>
              <Text style={styles.subtitle}>
                Rejoignez votre communauté paroissiale
              </Text>
            </View>

            {/* Form card */}
            <GlassCard style={styles.card}>
              <View style={styles.cardInner}>

                {/* First name + Last name side-by-side */}
                <View style={styles.nameRow}>
                  <View style={styles.nameField}>
                    <Input
                      label="Prénom"
                      placeholder="Jean"
                      value={firstName}
                      onChangeText={(t) => {
                        setFirstName(t);
                        clearFieldError('firstName');
                      }}
                      autoCapitalize="words"
                      autoComplete="given-name"
                      returnKeyType="next"
                      error={fieldErrors.firstName}
                    />
                  </View>
                  <View style={styles.nameField}>
                    <Input
                      label="Nom"
                      placeholder="Tremblay"
                      value={lastName}
                      onChangeText={(t) => {
                        setLastName(t);
                        clearFieldError('lastName');
                      }}
                      autoCapitalize="words"
                      autoComplete="family-name"
                      returnKeyType="next"
                      error={fieldErrors.lastName}
                    />
                  </View>
                </View>

                <Input
                  label="Adresse courriel"
                  placeholder="vous@exemple.com"
                  value={email}
                  onChangeText={(t) => {
                    setEmail(t);
                    clearFieldError('email');
                  }}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  autoCorrect={false}
                  autoComplete="email"
                  returnKeyType="next"
                  error={fieldErrors.email}
                />

                <Input
                  label="Mot de passe"
                  placeholder="Au moins 8 caractères"
                  value={password}
                  onChangeText={(t) => {
                    setPassword(t);
                    clearFieldError('password');
                    if (confirmPassword && fieldErrors.confirmPassword) {
                      clearFieldError('confirmPassword');
                    }
                  }}
                  secureTextEntry
                  autoCapitalize="none"
                  autoComplete="new-password"
                  returnKeyType="next"
                  error={fieldErrors.password}
                />

                <Input
                  label="Confirmer le mot de passe"
                  placeholder="Répétez votre mot de passe"
                  value={confirmPassword}
                  onChangeText={(t) => {
                    setConfirmPassword(t);
                    clearFieldError('confirmPassword');
                  }}
                  secureTextEntry
                  autoCapitalize="none"
                  returnKeyType="next"
                  error={fieldErrors.confirmPassword}
                />

                {/* Divider */}
                <View style={styles.dividerRow}>
                  <View style={styles.dividerLine} />
                  <Text style={styles.dividerLabel}>Optionnel</Text>
                  <View style={styles.dividerLine} />
                </View>

                <Input
                  label="Code d'invitation"
                  placeholder="Laissez vide si vous n'en avez pas"
                  value={invitationCode}
                  onChangeText={setInvitationCode}
                  autoCapitalize="characters"
                  autoCorrect={false}
                  returnKeyType="done"
                  onSubmitEditing={handleSignup}
                />

                {/* Global error */}
                {error && (
                  <View style={styles.errorContainer}>
                    <Text style={styles.errorIcon}>⚠</Text>
                    <Text style={styles.errorText}>{error}</Text>
                  </View>
                )}

                <Button
                  title="S'inscrire"
                  onPress={handleSignup}
                  loading={loading}
                  size="lg"
                  style={styles.submitButton}
                />
              </View>
            </GlassCard>

            {/* Login link */}
            <View style={styles.footer}>
              <Text style={styles.footerText}>Déjà un compte?</Text>
              <TouchableOpacity
                onPress={() => router.replace('/(auth)/login')}
                activeOpacity={0.7}
              >
                <Text style={styles.footerLink}>Se connecter</Text>
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
    paddingTop: 24,
    paddingBottom: 32,
  },

  // Back button
  backButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 28,
    alignSelf: 'flex-start',
  },
  backArrow: {
    fontSize: 20,
    color: Colors.primaryLight,
    lineHeight: 24,
  },
  backLabel: {
    fontSize: 15,
    color: Colors.primaryLight,
    fontWeight: '500',
  },

  // Heading
  headingArea: {
    marginBottom: 28,
  },
  heading: {
    fontSize: 30,
    fontWeight: '700',
    color: Colors.text,
    marginBottom: 6,
  },
  subtitle: {
    fontSize: 14,
    color: Colors.textSecondary,
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

  // Name row
  nameRow: {
    flexDirection: 'row',
    gap: 12,
  },
  nameField: {
    flex: 1,
  },

  // Divider
  dividerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginVertical: 2,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: Colors.border,
  },
  dividerLabel: {
    fontSize: 11,
    color: Colors.textMuted,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
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
