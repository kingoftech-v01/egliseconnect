'use client';

import { use, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, User, Phone, Mail, MapPin, Calendar } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/components/ui/toast';
import { useMember, useUpdateMember } from '@/hooks/use-members';
import { ROLE_LABELS, MEMBERSHIP_STATUS_LABELS } from '@egliseconnect/types';
import type { Member } from '@egliseconnect/types';

// ─── Schema ───────────────────────────────────────────────────────────────────

const memberSchema = z.object({
  first_name: z.string().min(1, 'Le prénom est requis'),
  last_name: z.string().min(1, 'Le nom est requis'),
  email: z.string().email('Courriel invalide'),
  phone: z.string().optional(),
  phone_secondary: z.string().optional(),
  birth_date: z.string().optional(),
  address: z.string().optional(),
  city: z.string().optional(),
  province: z.string().optional(),
  postal_code: z.string().optional(),
  family_status: z.string().optional(),
  role: z.string().optional(),
  membership_status: z.string().optional(),
});

type MemberFormData = z.infer<typeof memberSchema>;

// ─── Field wrapper ────────────────────────────────────────────────────────────

function Field({
  label,
  required,
  error,
  icon: Icon,
  children,
}: {
  label: string;
  required?: boolean;
  error?: string;
  icon?: React.ElementType;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label className="flex items-center gap-1.5 text-sm font-medium text-white/80">
        {Icon && <Icon className="h-3.5 w-3.5 text-white/40" />}
        {label}
        {required && <span className="text-rose-400">*</span>}
      </label>
      {children}
      {error && <p className="text-xs text-rose-400">{error}</p>}
    </div>
  );
}

// ─── Skeleton ────────────────────────────────────────────────────────────────

function EditFormSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Skeleton className="h-10 w-10 rounded-xl" />
        <div className="space-y-2">
          <Skeleton className="h-7 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
      </div>
      <Skeleton className="h-64 rounded-2xl" />
      <Skeleton className="h-48 rounded-2xl" />
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function EditMemberPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const { toast } = useToast();

  const { data: memberRaw, isLoading } = useMember(id);
  const member = memberRaw as Member | undefined;

  const { mutate: updateMember, isPending } = useUpdateMember(id);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<MemberFormData>({
    resolver: zodResolver(memberSchema),
  });

  useEffect(() => {
    if (!member) return;
    reset({
      first_name: member.first_name ?? '',
      last_name: member.last_name ?? '',
      email: member.email ?? '',
      phone: member.phone ?? '',
      phone_secondary: member.phone_secondary ?? '',
      birth_date: member.birth_date ?? '',
      address: member.address ?? '',
      city: member.city ?? '',
      province: member.province ?? '',
      postal_code: member.postal_code ?? '',
      family_status: member.family_status ?? '',
      role: member.role ?? '',
      membership_status: member.membership_status ?? '',
    });
  }, [member, reset]);

  function onSubmit(data: MemberFormData) {
    updateMember(data, {
      onSuccess: () => {
        toast({
          type: 'success',
          title: 'Membre mis à jour',
          description: `${data.first_name} ${data.last_name} a été modifié avec succès.`,
        });
        router.push(`/members/${id}`);
      },
      onError: () => {
        toast({
          type: 'error',
          title: 'Erreur',
          description: 'Veuillez vérifier les informations et réessayer.',
        });
      },
    });
  }

  if (isLoading) return <EditFormSkeleton />;

  if (!member) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="rounded-2xl bg-white/[0.04] border border-white/[0.06] p-8 text-center">
          <p className="text-white/50 text-sm">Membre introuvable</p>
          <Link href="/members" className="text-purple-400 hover:text-purple-300 text-sm mt-3 inline-block transition-colors">
            Retour aux membres
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex items-center gap-4">
        <Link href={`/members/${id}`}>
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-5 w-5" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-white">Modifier le membre</h1>
          <p className="text-sm text-white/50 truncate max-w-sm">{member.full_name}</p>
        </div>
      </div>

      {/* ── Form ── */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Informations personnelles */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Informations personnelles</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Prénom" required error={errors.first_name?.message} icon={User}>
                <Input {...register('first_name')} placeholder="Prénom" error={!!errors.first_name} />
              </Field>
              <Field label="Nom de famille" required error={errors.last_name?.message} icon={User}>
                <Input {...register('last_name')} placeholder="Nom de famille" error={!!errors.last_name} />
              </Field>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Courriel" required error={errors.email?.message} icon={Mail}>
                <Input type="email" {...register('email')} placeholder="courriel@exemple.ca" error={!!errors.email} />
              </Field>
              <Field label="Téléphone" error={errors.phone?.message} icon={Phone}>
                <Input {...register('phone')} placeholder="+1 (514) 555-0000" />
              </Field>
            </div>
            <Field label="Date de naissance" error={errors.birth_date?.message} icon={Calendar}>
              <Input type="date" {...register('birth_date')} className="max-w-xs" />
            </Field>
          </CardContent>
        </Card>

        {/* Adresse */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Adresse</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Field label="Adresse" error={errors.address?.message} icon={MapPin}>
              <Input {...register('address')} placeholder="123 rue Principale" />
            </Field>
            <div className="grid gap-4 sm:grid-cols-3">
              <Field label="Ville" error={errors.city?.message}>
                <Input {...register('city')} placeholder="Montréal" />
              </Field>
              <Field label="Province" error={errors.province?.message}>
                <Input {...register('province')} placeholder="QC" />
              </Field>
              <Field label="Code postal" error={errors.postal_code?.message}>
                <Input {...register('postal_code')} placeholder="H1A 1A1" />
              </Field>
            </div>
          </CardContent>
        </Card>

        {/* Rôle et statut */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Rôle et statut</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Rôle">
                <Select {...register('role')}>
                  {Object.entries(ROLE_LABELS).map(([value, label]) => (
                    <option key={value} value={value} className="bg-[#1a1145]">{label}</option>
                  ))}
                </Select>
              </Field>
              <Field label="Statut">
                <Select {...register('membership_status')}>
                  {Object.entries(MEMBERSHIP_STATUS_LABELS).map(([value, label]) => (
                    <option key={value} value={value} className="bg-[#1a1145]">{label}</option>
                  ))}
                </Select>
              </Field>
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <Button type="submit" disabled={isPending} className="min-w-[180px]">
            {isPending ? (
              <span className="flex items-center gap-2">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Enregistrement...
              </span>
            ) : (
              'Enregistrer les modifications'
            )}
          </Button>
          <Link href={`/members/${id}`}>
            <Button type="button" variant="outline" disabled={isPending}>
              Annuler
            </Button>
          </Link>
        </div>
      </form>
    </div>
  );
}
