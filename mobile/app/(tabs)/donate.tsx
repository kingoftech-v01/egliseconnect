import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useMutation } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { useState } from 'react';

import { GradientBackground } from '@/components/ui/GradientBackground';
import { GlassCard } from '@/components/ui/GlassCard';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Colors } from '@/constants/colors';
import { api } from '@/lib/api';

// ─── Constants ────────────────────────────────────────────────────────────────

const PRESET_AMOUNTS = [25, 50, 100, 250];

type DonationType = 'dime' | 'offrande' | 'missions' | 'special';
type PaymentMethod = 'carte' | 'virement';

const DONATION_TYPES: { value: DonationType; label: string }[] = [
  { value: 'dime',      label: 'Dîme' },
  { value: 'offrande',  label: 'Offrande' },
  { value: 'missions',  label: 'Missions' },
  { value: 'special',   label: 'Spécial' },
];

const PAYMENT_METHODS: { value: PaymentMethod; label: string; icon: string }[] = [
  { value: 'carte',    label: 'Carte',     icon: 'card-outline' },
  { value: 'virement', label: 'Virement',  icon: 'swap-horizontal-outline' },
];

// ─── Sub-components ───────────────────────────────────────────────────────────

interface PillButtonProps {
  label: string;
  active: boolean;
  onPress: () => void;
  icon?: string;
}

function PillButton({ label, active, onPress, icon }: PillButtonProps) {
  return (
    <TouchableOpacity
      onPress={onPress}
      activeOpacity={0.7}
      style={[styles.pill, active && styles.pillActive]}
    >
      {icon ? (
        <Ionicons
          name={icon as any}
          size={14}
          color={active ? Colors.white : Colors.textSecondary}
          style={styles.pillIcon}
        />
      ) : null}
      <Text style={[styles.pillText, active && styles.pillTextActive]}>{label}</Text>
    </TouchableOpacity>
  );
}

interface PresetAmountCardProps {
  amount: number;
  selected: boolean;
  onPress: () => void;
}

function PresetAmountCard({ amount, selected, onPress }: PresetAmountCardProps) {
  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.7} style={styles.presetTouchable}>
      <GlassCard
        style={[
          styles.presetCard,
          selected && styles.presetCardSelected,
        ]}
      >
        <View style={styles.presetInner}>
          <Text style={styles.presetCurrency}>$</Text>
          <Text style={[styles.presetAmount, selected && styles.presetAmountSelected]}>
            {amount}
          </Text>
        </View>
      </GlassCard>
    </TouchableOpacity>
  );
}

// ─── Success Card ─────────────────────────────────────────────────────────────

function SuccessCard({ amount, type }: { amount: string; type: DonationType }) {
  const typeLabel = DONATION_TYPES.find((t) => t.value === type)?.label ?? type;
  return (
    <GlassCard style={styles.successCard}>
      <View style={styles.successInner}>
        <View style={styles.successIconWrap}>
          <Ionicons name="checkmark-circle" size={52} color={Colors.success} />
        </View>
        <Text style={styles.successTitle}>Don reçu !</Text>
        <Text style={styles.successSub}>
          Merci pour votre don de{' '}
          <Text style={styles.successAmount}>${amount}</Text>
          {' '}({typeLabel}).
        </Text>
        <Text style={styles.successNote}>
          Votre générosité contribue à la mission de notre communauté. Dieu bénisse votre don.
        </Text>
      </View>
    </GlassCard>
  );
}

// ─── Main Screen ──────────────────────────────────────────────────────────────

export default function DonateScreen() {
  const [selectedPreset, setSelectedPreset] = useState<number | null>(50);
  const [customAmount, setCustomAmount] = useState('');
  const [donationType, setDonationType] = useState<DonationType>('offrande');
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('carte');
  const [success, setSuccess] = useState(false);

  const effectiveAmount = customAmount !== '' ? customAmount : String(selectedPreset ?? '');

  const { mutate, isPending, isError } = useMutation({
    mutationFn: (data: {
      amount: string;
      donation_type: DonationType;
      payment_method: PaymentMethod;
    }) => api.donations.create(data),
    onSuccess: () => {
      setSuccess(true);
    },
  });

  const handlePresetPress = (amount: number) => {
    setSelectedPreset(amount);
    setCustomAmount('');
  };

  const handleCustomChange = (text: string) => {
    const cleaned = text.replace(/[^0-9.]/g, '');
    setCustomAmount(cleaned);
    if (cleaned !== '') {
      setSelectedPreset(null);
    }
  };

  const handleDonate = () => {
    if (!effectiveAmount || Number(effectiveAmount) <= 0) return;
    mutate({
      amount: effectiveAmount,
      donation_type: donationType,
      payment_method: paymentMethod,
    });
  };

  const handleReset = () => {
    setSuccess(false);
    setSelectedPreset(50);
    setCustomAmount('');
    setDonationType('offrande');
    setPaymentMethod('carte');
  };

  return (
    <GradientBackground>
      <SafeAreaView style={styles.safe}>
        <KeyboardAvoidingView
          style={styles.keyboardView}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          keyboardVerticalOffset={0}
        >
          <ScrollView
            style={styles.scroll}
            contentContainerStyle={styles.scrollContent}
            showsVerticalScrollIndicator={false}
            keyboardShouldPersistTaps="handled"
          >
            {/* Header */}
            <View style={styles.header}>
              <View style={styles.headerIconWrap}>
                <Ionicons name="heart" size={24} color={Colors.primary} />
              </View>
              <View style={styles.headerText}>
                <Text style={styles.headerTitle}>Faire un don</Text>
                <Text style={styles.headerSub}>
                  Chaque don fait une différence
                </Text>
              </View>
            </View>

            {success ? (
              /* ── Success state ───────────────────────────────────────── */
              <View style={styles.successWrap}>
                <SuccessCard amount={effectiveAmount} type={donationType} />
                <Button
                  title="Faire un autre don"
                  onPress={handleReset}
                  variant="secondary"
                  size="lg"
                  style={styles.resetBtn}
                />
              </View>
            ) : (
              /* ── Form state ──────────────────────────────────────────── */
              <View style={styles.form}>
                {/* Quick amounts */}
                <View style={styles.section}>
                  <Text style={styles.sectionLabel}>Montant rapide</Text>
                  <View style={styles.presetGrid}>
                    {PRESET_AMOUNTS.map((amt) => (
                      <PresetAmountCard
                        key={amt}
                        amount={amt}
                        selected={selectedPreset === amt && customAmount === ''}
                        onPress={() => handlePresetPress(amt)}
                      />
                    ))}
                  </View>
                </View>

                {/* Custom amount */}
                <View style={styles.section}>
                  <Text style={styles.sectionLabel}>Montant personnalisé</Text>
                  <GlassCard style={styles.customCard}>
                    <View style={styles.customInner}>
                      <Text style={styles.dollarSign}>$</Text>
                      <Input
                        value={customAmount}
                        onChangeText={handleCustomChange}
                        placeholder="0.00"
                        keyboardType="decimal-pad"
                        style={styles.customInput}
                        returnKeyType="done"
                      />
                    </View>
                  </GlassCard>
                </View>

                {/* Donation type */}
                <View style={styles.section}>
                  <Text style={styles.sectionLabel}>Type de don</Text>
                  <View style={styles.pillRow}>
                    {DONATION_TYPES.map((t) => (
                      <PillButton
                        key={t.value}
                        label={t.label}
                        active={donationType === t.value}
                        onPress={() => setDonationType(t.value)}
                      />
                    ))}
                  </View>
                </View>

                {/* Payment method */}
                <View style={styles.section}>
                  <Text style={styles.sectionLabel}>Mode de paiement</Text>
                  <View style={styles.pillRow}>
                    {PAYMENT_METHODS.map((m) => (
                      <PillButton
                        key={m.value}
                        label={m.label}
                        active={paymentMethod === m.value}
                        onPress={() => setPaymentMethod(m.value)}
                        icon={m.icon}
                      />
                    ))}
                  </View>
                </View>

                {/* Summary */}
                {effectiveAmount && Number(effectiveAmount) > 0 ? (
                  <GlassCard style={styles.summaryCard}>
                    <View style={styles.summaryInner}>
                      <View style={styles.summaryRow}>
                        <Text style={styles.summaryLabel}>Montant</Text>
                        <Text style={styles.summaryValue}>${effectiveAmount}</Text>
                      </View>
                      <View style={styles.summaryRow}>
                        <Text style={styles.summaryLabel}>Type</Text>
                        <Text style={styles.summaryValue}>
                          {DONATION_TYPES.find((t) => t.value === donationType)?.label}
                        </Text>
                      </View>
                      <View style={styles.summaryRow}>
                        <Text style={styles.summaryLabel}>Paiement</Text>
                        <Text style={styles.summaryValue}>
                          {PAYMENT_METHODS.find((m) => m.value === paymentMethod)?.label}
                        </Text>
                      </View>
                    </View>
                  </GlassCard>
                ) : null}

                {/* Error state */}
                {isError ? (
                  <View style={styles.errorRow}>
                    <Ionicons name="alert-circle-outline" size={16} color={Colors.error} />
                    <Text style={styles.errorText}>
                      Une erreur est survenue. Veuillez réessayer.
                    </Text>
                  </View>
                ) : null}

                {/* Submit */}
                <Button
                  title={isPending ? 'Traitement…' : 'Donner'}
                  onPress={handleDonate}
                  variant="primary"
                  size="lg"
                  loading={isPending}
                  disabled={!effectiveAmount || Number(effectiveAmount) <= 0}
                  style={styles.submitBtn}
                />

                <Text style={styles.disclaimer}>
                  Votre don est sécurisé et confidentiel. Un reçu vous sera envoyé par courriel.
                </Text>
              </View>
            )}
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </GradientBackground>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  safe: {
    flex: 1,
  },
  keyboardView: {
    flex: 1,
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 40,
  },

  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    marginBottom: 24,
  },
  headerIconWrap: {
    width: 48,
    height: 48,
    borderRadius: 16,
    backgroundColor: 'rgba(124,58,237,0.15)',
    borderWidth: 1,
    borderColor: 'rgba(124,58,237,0.25)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerText: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 26,
    fontWeight: '800',
    color: Colors.text,
    letterSpacing: -0.5,
  },
  headerSub: {
    fontSize: 13,
    color: Colors.textMuted,
    marginTop: 2,
  },

  // Form sections
  form: {
    gap: 20,
  },
  section: {
    gap: 10,
  },
  sectionLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: Colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },

  // Preset grid (2x2)
  presetGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  presetTouchable: {
    width: '47%',
    borderRadius: 16,
  },
  presetCard: {
    borderRadius: 16,
  },
  presetCardSelected: {
    borderColor: Colors.primary,
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.5,
    shadowRadius: 10,
    elevation: 8,
  },
  presetInner: {
    paddingVertical: 18,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 2,
  },
  presetCurrency: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.textSecondary,
    marginTop: 4,
  },
  presetAmount: {
    fontSize: 28,
    fontWeight: '800',
    color: Colors.text,
  },
  presetAmountSelected: {
    color: Colors.primaryLight,
  },

  // Custom amount
  customCard: {
    borderRadius: 16,
  },
  customInner: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 6,
    gap: 8,
  },
  dollarSign: {
    fontSize: 28,
    fontWeight: '700',
    color: Colors.textSecondary,
  },
  customInput: {
    flex: 1,
    fontSize: 28,
    fontWeight: '700',
    color: Colors.text,
    backgroundColor: 'transparent',
    borderWidth: 0,
    paddingHorizontal: 0,
    paddingVertical: 8,
  },

  // Pills
  pillRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  pill: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 9,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: Colors.border,
    backgroundColor: 'rgba(255,255,255,0.04)',
  },
  pillActive: {
    backgroundColor: Colors.primary,
    borderColor: Colors.primary,
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.4,
    shadowRadius: 6,
    elevation: 5,
  },
  pillIcon: {
    marginRight: 5,
  },
  pillText: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.textSecondary,
  },
  pillTextActive: {
    color: Colors.white,
  },

  // Summary
  summaryCard: {
    borderRadius: 16,
  },
  summaryInner: {
    padding: 16,
    gap: 10,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  summaryLabel: {
    fontSize: 13,
    color: Colors.textMuted,
  },
  summaryValue: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.text,
  },

  // Error
  errorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: 'rgba(244,63,94,0.1)',
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: 'rgba(244,63,94,0.2)',
  },
  errorText: {
    fontSize: 13,
    color: Colors.error,
    flex: 1,
  },

  // Submit
  submitBtn: {
    marginTop: 4,
  },
  disclaimer: {
    fontSize: 12,
    color: Colors.textMuted,
    textAlign: 'center',
    lineHeight: 18,
  },

  // Success
  successWrap: {
    gap: 16,
  },
  successCard: {
    borderRadius: 20,
  },
  successInner: {
    padding: 28,
    alignItems: 'center',
    gap: 12,
  },
  successIconWrap: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(16,185,129,0.12)',
    borderWidth: 2,
    borderColor: 'rgba(16,185,129,0.25)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  successTitle: {
    fontSize: 26,
    fontWeight: '800',
    color: Colors.text,
    letterSpacing: -0.5,
  },
  successSub: {
    fontSize: 16,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 24,
  },
  successAmount: {
    color: Colors.success,
    fontWeight: '700',
  },
  successNote: {
    fontSize: 13,
    color: Colors.textMuted,
    textAlign: 'center',
    lineHeight: 20,
    marginTop: 4,
  },
  resetBtn: {
    marginTop: 4,
  },
});
