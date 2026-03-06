'use client';

import { use, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Calendar, MapPin, Users, Video, Type, AlignLeft, RefreshCw } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/components/ui/toast';
import { useEvent, useUpdateEvent } from '@/hooks/use-events';
import type { Event } from '@egliseconnect/types';

// ─── Schema ───────────────────────────────────────────────────────────────────

const eventSchema = z.object({
  title: z.string().min(1, 'Le titre est requis'),
  description: z.string().optional(),
  event_type: z.string().min(1, 'Le type est requis'),
  start_date: z.string().min(1, 'La date de début est requise'),
  end_date: z.string().optional(),
  location: z.string().optional(),
  max_capacity: z.string().optional(),
  virtual_link: z.string().url('URL invalide').optional().or(z.literal('')),
  is_recurring: z.boolean().optional(),
});

type EventFormData = z.infer<typeof eventSchema>;

// ─── Event type options ───────────────────────────────────────────────────────

const EVENT_TYPE_OPTIONS = [
  { value: 'worship', label: 'Culte' },
  { value: 'group', label: 'Groupe' },
  { value: 'meal', label: 'Repas communautaire' },
  { value: 'special', label: 'Événement spécial' },
  { value: 'meeting', label: 'Réunion' },
  { value: 'training', label: 'Formation' },
  { value: 'outreach', label: 'Évangélisation' },
  { value: 'other', label: 'Autre' },
];

// ─── Helpers ─────────────────────────────────────────────────────────────────

/** Convert an ISO datetime string to the format required by datetime-local inputs: YYYY-MM-DDTHH:mm */
function toDatetimeLocal(dateStr: string | null | undefined): string {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  } catch {
    return '';
  }
}

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
      <Skeleton className="h-40 rounded-2xl" />
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function EditEventPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const { toast } = useToast();

  const { data: eventRaw, isLoading } = useEvent(id);
  const event = eventRaw as Event | undefined;

  const { mutate: updateEvent, isPending } = useUpdateEvent(id);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<EventFormData>({
    resolver: zodResolver(eventSchema),
    defaultValues: {
      event_type: '',
      is_recurring: false,
    },
  });

  const isRecurring = watch('is_recurring');

  // Pre-fill the form once the event data loads
  useEffect(() => {
    if (!event) return;
    reset({
      title: event.title ?? '',
      description: event.description ?? '',
      event_type: event.event_type ?? '',
      start_date: toDatetimeLocal(event.start_date),
      end_date: toDatetimeLocal(event.end_date),
      location: event.location ?? '',
      max_capacity: event.max_capacity ? String(event.max_capacity) : '',
      virtual_link: event.virtual_link ?? '',
      is_recurring: event.is_recurring ?? false,
    });
  }, [event, reset]);

  function onSubmit(data: EventFormData) {
    const payload: Record<string, unknown> = {
      title: data.title,
      event_type: data.event_type,
      start_date: data.start_date,
      description: data.description ?? '',
      location: data.location ?? '',
      is_recurring: data.is_recurring ?? false,
    };

    if (data.end_date) {
      payload.end_date = data.end_date;
    } else {
      payload.end_date = null;
    }

    if (data.max_capacity) {
      payload.max_capacity = parseInt(data.max_capacity, 10);
    } else {
      payload.max_capacity = null;
    }

    if (data.virtual_link) {
      payload.virtual_link = data.virtual_link;
      payload.is_virtual = true;
    } else {
      payload.virtual_link = '';
      payload.is_virtual = false;
    }

    updateEvent(payload, {
      onSuccess: () => {
        toast({
          type: 'success',
          title: 'Événement mis à jour',
          description: `"${data.title}" a été modifié avec succès.`,
        });
        router.push(`/events/${id}`);
      },
      onError: () => {
        toast({
          type: 'error',
          title: 'Erreur lors de la mise à jour',
          description: 'Veuillez vérifier les informations et réessayer.',
        });
      },
    });
  }

  if (isLoading) return <EditFormSkeleton />;

  if (!event) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="rounded-2xl bg-white/[0.04] border border-white/[0.06] p-8 text-center">
          <p className="text-white/50 text-sm">Événement introuvable</p>
          <Link href="/events" className="text-purple-400 hover:text-purple-300 text-sm mt-3 inline-block transition-colors">
            Retour aux événements
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex items-center gap-4">
        <Link href={`/events/${id}`}>
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-5 w-5" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-white">Modifier l&apos;événement</h1>
          <p className="text-sm text-white/50 truncate max-w-sm">{event.title}</p>
        </div>
      </div>

      {/* ── Form ── */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Informations principales */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Informations principales</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Field label="Titre" required error={errors.title?.message} icon={Type}>
              <Input
                {...register('title')}
                placeholder="Ex: Culte du dimanche matin"
                error={!!errors.title}
              />
            </Field>

            <Field label="Description" error={errors.description?.message} icon={AlignLeft}>
              <Textarea
                {...register('description')}
                placeholder="Décrivez l'événement, son programme, ce qu'il faut apporter..."
                rows={4}
              />
            </Field>

            <Field label="Type d'événement" required error={errors.event_type?.message}>
              <Select {...register('event_type')} error={!!errors.event_type}>
                <option value="" className="bg-[#1a1145]">Sélectionner un type...</option>
                {EVENT_TYPE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value} className="bg-[#1a1145]">
                    {opt.label}
                  </option>
                ))}
              </Select>
            </Field>
          </CardContent>
        </Card>

        {/* Date et lieu */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Date et lieu</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Date de début" required error={errors.start_date?.message} icon={Calendar}>
                <Input
                  type="datetime-local"
                  {...register('start_date')}
                  error={!!errors.start_date}
                />
              </Field>

              <Field label="Date de fin" error={errors.end_date?.message} icon={Calendar}>
                <Input
                  type="datetime-local"
                  {...register('end_date')}
                />
              </Field>
            </div>

            <Field label="Lieu" error={errors.location?.message} icon={MapPin}>
              <Input
                {...register('location')}
                placeholder="Ex: Salle principale, 123 rue de l'Église"
              />
            </Field>
          </CardContent>
        </Card>

        {/* Capacité et options */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Capacité et options</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field
                label="Capacité maximale"
                error={errors.max_capacity?.message}
                icon={Users}
              >
                <Input
                  type="number"
                  min="1"
                  {...register('max_capacity')}
                  placeholder="Laisser vide pour illimité"
                />
              </Field>

              <Field
                label="Lien de réunion virtuelle"
                error={errors.virtual_link?.message}
                icon={Video}
              >
                <Input
                  type="url"
                  {...register('virtual_link')}
                  placeholder="https://zoom.us/j/..."
                />
              </Field>
            </div>

            {/* Is recurring toggle */}
            <div
              className="flex items-center justify-between rounded-xl bg-white/[0.03] border border-white/[0.06] px-4 py-3 cursor-pointer hover:bg-white/[0.05] transition-colors"
              onClick={() => setValue('is_recurring', !isRecurring)}
            >
              <div className="flex items-center gap-3">
                <RefreshCw className="h-4 w-4 text-white/40" />
                <div>
                  <p className="text-sm font-medium text-white/80">Événement récurrent</p>
                  <p className="text-xs text-white/40">Cet événement se répète régulièrement</p>
                </div>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={isRecurring}
                onClick={(e) => { e.stopPropagation(); setValue('is_recurring', !isRecurring); }}
                className={[
                  'relative h-6 w-11 rounded-full transition-colors duration-200 shrink-0',
                  isRecurring ? 'bg-purple-600' : 'bg-white/10',
                ].join(' ')}
              >
                <span
                  className={[
                    'absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform duration-200',
                    isRecurring ? 'translate-x-5' : 'translate-x-0',
                  ].join(' ')}
                />
              </button>
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
          <Link href={`/events/${id}`}>
            <Button type="button" variant="outline" disabled={isPending}>
              Annuler
            </Button>
          </Link>
        </div>
      </form>
    </div>
  );
}
