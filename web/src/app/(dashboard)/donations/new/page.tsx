'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  DollarSign,
  User,
  CreditCard,
  Calendar,
  FileText,
  Search,
  ChevronDown,
  Check,
} from 'lucide-react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/toast';
import { useCreateDonation } from '@/hooks/use-donations';
import { useMembers } from '@/hooks/use-members';
import {
  DONATION_TYPE_LABELS,
  type DonationTypeValue,
  type PaymentMethodType,
  type MemberListItem,
} from '@egliseconnect/types';

// ─── Validation schema ────────────────────────────────────────────────────────

const donationSchema = z.object({
  amount: z
    .string()
    .min(1, 'Le montant est requis')
    .refine((v) => !isNaN(parseFloat(v)) && parseFloat(v) > 0, 'Montant invalide (doit être > 0)'),
  donation_type: z.string().min(1, 'Le type de don est requis'),
  payment_method: z.string().min(1, 'La méthode de paiement est requise'),
  date: z.string().min(1, 'La date est requise'),
  member_id: z.string().optional(),
  campaign_id: z.string().optional(),
  is_anonymous: z.boolean().optional(),
  notes: z.string().optional(),
});

type DonationFormData = z.infer<typeof donationSchema>;

// ─── Payment method options ───────────────────────────────────────────────────

const PAYMENT_METHOD_OPTIONS: { value: PaymentMethodType; label: string }[] = [
  { value: 'cash', label: 'Espèces' },
  { value: 'check', label: 'Chèque' },
  { value: 'card', label: 'Carte' },
  { value: 'bank_transfer', label: 'Virement bancaire' },
  { value: 'online', label: 'En ligne' },
  { value: 'other', label: 'Autre' },
];

// ─── Styled select wrapper ────────────────────────────────────────────────────

function StyledSelect({
  id,
  value,
  onChange,
  children,
  error,
}: {
  id?: string;
  value: string;
  onChange: (v: string) => void;
  children: React.ReactNode;
  error?: boolean;
}) {
  return (
    <div className="relative">
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={[
          'flex h-10 w-full appearance-none rounded-xl bg-white/[0.06] border px-3 py-2 pr-9 text-sm text-white/90',
          'transition-all duration-200',
          'focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/30',
          error
            ? 'border-rose-500/50 focus:ring-rose-500/30'
            : 'border-white/[0.08]',
        ].join(' ')}
      >
        {children}
      </select>
      <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/40" />
    </div>
  );
}

// ─── Member search combobox ───────────────────────────────────────────────────

interface MemberSearchProps {
  value: string;
  onChange: (id: string, name: string) => void;
  disabled?: boolean;
}

function MemberSearch({ value, onChange, disabled }: MemberSearchProps) {
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [open, setOpen] = useState(false);
  const [selectedName, setSelectedName] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);

  // Debounce search query
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQuery(query), 300);
    return () => clearTimeout(t);
  }, [query]);

  const searchParams = debouncedQuery.length >= 2 ? `search=${encodeURIComponent(debouncedQuery)}&page_size=8` : undefined;
  const { data, isLoading } = useMembers(searchParams);

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  function handleSelect(member: MemberListItem) {
    onChange(member.id, member.full_name);
    setSelectedName(member.full_name);
    setQuery('');
    setOpen(false);
  }

  function handleClear() {
    onChange('', '');
    setSelectedName('');
    setQuery('');
  }

  return (
    <div ref={containerRef} className="relative">
      {/* Display field */}
      {value && selectedName ? (
        <div className="flex h-10 w-full items-center justify-between rounded-xl bg-white/[0.06] border border-white/[0.08] px-3 text-sm">
          <div className="flex items-center gap-2 min-w-0">
            <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-purple-500/20">
              <User className="h-3 w-3 text-purple-300" />
            </div>
            <span className="truncate text-white/90">{selectedName}</span>
          </div>
          <button
            type="button"
            onClick={handleClear}
            disabled={disabled}
            className="ml-2 shrink-0 text-white/30 hover:text-white/60 transition-colors"
          >
            ×
          </button>
        </div>
      ) : (
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
          <Input
            type="text"
            placeholder="Rechercher un membre..."
            className="pl-9"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              if (!open) setOpen(true);
            }}
            onFocus={() => setOpen(true)}
            disabled={disabled}
            autoComplete="off"
          />
        </div>
      )}

      {/* Dropdown */}
      {open && !value && (
        <div className="absolute left-0 right-0 top-full z-50 mt-1.5 overflow-hidden rounded-xl bg-[#1a1145]/95 backdrop-blur-xl border border-white/[0.1] shadow-[0_20px_60px_rgba(0,0,0,0.5)]">
          {debouncedQuery.length < 2 ? (
            <p className="px-4 py-3 text-xs text-white/40">
              Saisissez au moins 2 caractères pour chercher...
            </p>
          ) : isLoading ? (
            <p className="px-4 py-3 text-xs text-white/40">Recherche en cours...</p>
          ) : (data?.results ?? []).length === 0 ? (
            <p className="px-4 py-3 text-xs text-white/40">Aucun membre trouvé</p>
          ) : (
            <ul className="max-h-48 overflow-y-auto py-1">
              {(data?.results ?? []).map((member) => (
                <li key={member.id}>
                  <button
                    type="button"
                    className="flex w-full items-center gap-3 px-4 py-2.5 text-sm text-white/80 hover:bg-white/[0.06] transition-colors"
                    onClick={() => handleSelect(member)}
                  >
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-purple-500/20 text-xs font-medium text-purple-300">
                      {member.full_name
                        .split(' ')
                        .map((w: string) => w[0])
                        .join('')
                        .toUpperCase()
                        .slice(0, 2)}
                    </div>
                    <div className="min-w-0 text-left">
                      <p className="truncate font-medium text-white/90">{member.full_name}</p>
                      {!!member.email && (
                        <p className="truncate text-xs text-white/40">{member.email}</p>
                      )}
                    </div>
                    {member.id === value && (
                      <Check className="ml-auto h-4 w-4 shrink-0 text-purple-400" />
                    )}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Section header ───────────────────────────────────────────────────────────

function SectionHeader({
  icon: Icon,
  title,
  description,
}: {
  icon: React.ElementType;
  title: string;
  description?: string;
}) {
  return (
    <div className="flex items-start gap-3 mb-4">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-purple-500/20 ring-1 ring-purple-500/30">
        <Icon className="h-4 w-4 text-purple-300" />
      </div>
      <div>
        <h3 className="text-sm font-semibold text-white/90">{title}</h3>
        {description && <p className="text-xs text-white/40 mt-0.5">{description}</p>}
      </div>
    </div>
  );
}

// ─── Field wrapper ────────────────────────────────────────────────────────────

function Field({
  label,
  required,
  error,
  children,
}: {
  label: string;
  required?: boolean;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium text-white/70">
        {label}
        {required && <span className="ml-0.5 text-rose-400">*</span>}
      </label>
      {children}
      {error && <p className="text-xs text-rose-400">{error}</p>}
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function NewDonationPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { mutate: createDonation, isPending } = useCreateDonation();

  const [memberId, setMemberId] = useState('');

  const {
    register,
    handleSubmit,
    control,
    watch,
    setValue,
    formState: { errors },
  } = useForm<DonationFormData>({
    resolver: zodResolver(donationSchema),
    defaultValues: {
      amount: '',
      donation_type: '',
      payment_method: '',
      date: new Date().toISOString().split('T')[0],
      member_id: '',
      campaign_id: '',
      is_anonymous: false,
      notes: '',
    },
  });

  const isAnonymous = watch('is_anonymous');

  function onSubmit(data: DonationFormData) {
    createDonation(
      {
        amount: data.amount,
        donation_type: data.donation_type as DonationTypeValue,
        payment_method: data.payment_method as PaymentMethodType,
        date: data.date,
        is_anonymous: data.is_anonymous ?? false,
        member_id: !data.is_anonymous && memberId ? memberId : undefined,
        campaign_id: data.campaign_id || undefined,
        notes: data.notes || undefined,
      },
      {
        onSuccess: () => {
          toast({
            type: 'success',
            title: 'Don enregistré',
            description: 'Le don a été créé avec succès.',
          });
          router.push('/donations');
        },
        onError: (err) => {
          toast({
            type: 'error',
            title: 'Erreur d\'enregistrement',
            description: err instanceof Error ? err.message : 'Une erreur est survenue.',
          });
        },
      },
    );
  }

  return (
    <div className="space-y-6">
      {/* ── Page header ───────────────────────────────────────────────────── */}
      <div className="flex items-center gap-4">
        <Link href="/donations">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-5 w-5" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-white/90">Nouveau don</h1>
          <p className="text-sm text-white/40">Enregistrer une nouvelle contribution</p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} noValidate>
        <div className="grid gap-4 lg:grid-cols-3">
          {/* ── Left column (2/3) ────────────────────────────────────────── */}
          <div className="space-y-4 lg:col-span-2">
            {/* Montant et date */}
            <Card>
              <CardHeader className="pb-2">
                <SectionHeader
                  icon={DollarSign}
                  title="Montant et date"
                  description="Informations financières du don"
                />
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  {/* Amount */}
                  <Field label="Montant (CAD)" required error={errors.amount?.message}>
                    <div className="relative">
                      <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm font-medium text-white/40">
                        $
                      </span>
                      <Input
                        type="number"
                        step="0.01"
                        min="0.01"
                        placeholder="0,00"
                        {...register('amount')}
                        className="pl-7"
                        error={!!errors.amount}
                      />
                    </div>
                  </Field>

                  {/* Date */}
                  <Field label="Date du don" required error={errors.date?.message}>
                    <div className="relative">
                      <Calendar className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
                      <Input
                        type="date"
                        {...register('date')}
                        className="pl-9"
                        error={!!errors.date}
                      />
                    </div>
                  </Field>
                </div>
              </CardContent>
            </Card>

            {/* Type et méthode */}
            <Card>
              <CardHeader className="pb-2">
                <SectionHeader
                  icon={CreditCard}
                  title="Type et méthode de paiement"
                  description="Catégorie et mode de règlement"
                />
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  {/* Donation type */}
                  <Field label="Type de don" required error={errors.donation_type?.message}>
                    <Controller
                      name="donation_type"
                      control={control}
                      render={({ field }) => (
                        <StyledSelect
                          value={field.value}
                          onChange={field.onChange}
                          error={!!errors.donation_type}
                        >
                          <option value="" className="bg-[#1a1145]">
                            Sélectionner un type...
                          </option>
                          {Object.entries(DONATION_TYPE_LABELS).map(([value, label]) => (
                            <option key={value} value={value} className="bg-[#1a1145]">
                              {label}
                            </option>
                          ))}
                        </StyledSelect>
                      )}
                    />
                  </Field>

                  {/* Payment method */}
                  <Field
                    label="Méthode de paiement"
                    required
                    error={errors.payment_method?.message}
                  >
                    <Controller
                      name="payment_method"
                      control={control}
                      render={({ field }) => (
                        <StyledSelect
                          value={field.value}
                          onChange={field.onChange}
                          error={!!errors.payment_method}
                        >
                          <option value="" className="bg-[#1a1145]">
                            Sélectionner une méthode...
                          </option>
                          {PAYMENT_METHOD_OPTIONS.map(({ value, label }) => (
                            <option key={value} value={value} className="bg-[#1a1145]">
                              {label}
                            </option>
                          ))}
                        </StyledSelect>
                      )}
                    />
                  </Field>
                </div>

                {/* Campaign (optional) */}
                <Field label="Campagne (optionnel)">
                  <div className="relative">
                    <FileText className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
                    <Input
                      placeholder="Identifiant de la campagne..."
                      {...register('campaign_id')}
                      className="pl-9"
                    />
                  </div>
                  <p className="text-xs text-white/30">
                    Laissez vide si ce don n&apos;est pas lié à une campagne spécifique.
                  </p>
                </Field>
              </CardContent>
            </Card>

            {/* Notes */}
            <Card>
              <CardHeader className="pb-2">
                <SectionHeader
                  icon={FileText}
                  title="Notes"
                  description="Informations complémentaires sur ce don"
                />
              </CardHeader>
              <CardContent>
                <Field label="Notes" error={errors.notes?.message}>
                  <Textarea
                    placeholder="Entrez des notes ou commentaires sur ce don..."
                    rows={4}
                    {...register('notes')}
                  />
                </Field>
              </CardContent>
            </Card>
          </div>

          {/* ── Right column (1/3) ───────────────────────────────────────── */}
          <div className="space-y-4">
            {/* Donor */}
            <Card>
              <CardHeader className="pb-2">
                <SectionHeader
                  icon={User}
                  title="Donateur"
                  description="Membre associé à ce don"
                />
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Anonymous toggle */}
                <label className="flex cursor-pointer items-center justify-between rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-3 transition-colors hover:bg-white/[0.05]">
                  <div>
                    <p className="text-sm font-medium text-white/80">Don anonyme</p>
                    <p className="text-xs text-white/40">L&apos;identité ne sera pas enregistrée</p>
                  </div>
                  <Controller
                    name="is_anonymous"
                    control={control}
                    render={({ field }) => (
                      <button
                        type="button"
                        role="switch"
                        aria-checked={field.value ?? false}
                        onClick={() => {
                          field.onChange(!field.value);
                          if (!field.value) {
                            setMemberId('');
                            setValue('member_id', '');
                          }
                        }}
                        className={[
                          'relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors duration-200',
                          field.value
                            ? 'bg-purple-600'
                            : 'bg-white/[0.12]',
                        ].join(' ')}
                      >
                        <span
                          className={[
                            'inline-block h-4 w-4 rounded-full bg-white shadow-sm transition-transform duration-200',
                            field.value ? 'translate-x-6' : 'translate-x-1',
                          ].join(' ')}
                        />
                      </button>
                    )}
                  />
                </label>

                {/* Member search */}
                {!isAnonymous && (
                  <Field label="Rechercher un membre">
                    <MemberSearch
                      value={memberId}
                      onChange={(id, _name) => {
                        setMemberId(id);
                        setValue('member_id', id);
                      }}
                    />
                    <p className="text-xs text-white/30">
                      Optionnel — laissez vide pour un don sans membre associé.
                    </p>
                  </Field>
                )}

                {isAnonymous && (
                  <div className="flex items-center gap-2 rounded-xl bg-amber-500/10 border border-amber-500/20 px-3 py-2.5">
                    <Badge variant="warning" className="shrink-0">Anonyme</Badge>
                    <p className="text-xs text-amber-400/80">
                      L&apos;identité du donateur ne sera pas enregistrée.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Summary card */}
            <Card className="border-purple-500/20 bg-purple-500/[0.04]">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-white/70">Récapitulatif</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {[
                  { label: 'Montant', value: watch('amount') ? `$${parseFloat(watch('amount') || '0').toFixed(2)}` : '—' },
                  { label: 'Type', value: watch('donation_type') ? DONATION_TYPE_LABELS[watch('donation_type') as DonationTypeValue] : '—' },
                  { label: 'Méthode', value: watch('payment_method') ? (PAYMENT_METHOD_OPTIONS.find((o) => o.value === watch('payment_method'))?.label ?? '—') : '—' },
                  { label: 'Date', value: watch('date') || '—' },
                ].map(({ label, value }) => (
                  <div key={label} className="flex items-center justify-between text-sm">
                    <span className="text-white/40">{label}</span>
                    <span className="font-medium text-white/80">{value}</span>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Actions */}
            <div className="flex flex-col gap-2">
              <Button type="submit" className="w-full" disabled={isPending}>
                {isPending ? (
                  <>
                    <span className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                    Enregistrement...
                  </>
                ) : (
                  <>
                    <DollarSign className="mr-2 h-4 w-4" />
                    Enregistrer le don
                  </>
                )}
              </Button>
              <Link href="/donations" className="w-full">
                <Button type="button" variant="outline" className="w-full" disabled={isPending}>
                  Annuler
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}
