'use client';

import { use, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/components/ui/toast';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

// ─── Types ───────────────────────────────────────────────────────────────────

interface VolunteerProfile {
  id: string;
  member: { id: string; full_name: string };
  position: { id: string; title: string } | null;
  status: string;
  is_active: boolean;
  availability: string;
  notes: string;
  total_hours: number;
}

// ─── Field wrapper ────────────────────────────────────────────────────────────

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label className="text-sm font-medium text-white/80">{label}</label>
      {children}
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function EditVolunteerPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: volunteer, isLoading } = useQuery<VolunteerProfile>({
    queryKey: ['volunteers', id],
    queryFn: () => api.get(`/api/v2/volunteers/profiles/${id}/`) as Promise<VolunteerProfile>,
    enabled: !!id,
  });

  const { mutate: updateVolunteer, isPending } = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.patch(`/api/v2/volunteers/profiles/${id}/`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['volunteers'] });
      queryClient.invalidateQueries({ queryKey: ['volunteers', id] });
    },
  });

  const [form, setForm] = useState({
    availability: '',
    notes: '',
    is_active: true,
  });

  useEffect(() => {
    if (volunteer) {
      setForm({
        availability: volunteer.availability ?? '',
        notes: volunteer.notes ?? '',
        is_active: volunteer.is_active ?? true,
      });
    }
  }, [volunteer]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    updateVolunteer(form, {
      onSuccess: () => {
        toast({
          type: 'success',
          title: 'Bénévole mis à jour',
          description: 'Les modifications ont été enregistrées.',
        });
        router.push(`/volunteers/${id}`);
      },
      onError: () => {
        toast({
          type: 'error',
          title: 'Erreur',
          description: 'Impossible de mettre à jour le bénévole.',
        });
      },
    });
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10 rounded-xl" />
          <Skeleton className="h-7 w-48" />
        </div>
        <Skeleton className="h-64 rounded-2xl" />
      </div>
    );
  }

  if (!volunteer) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <p className="text-white/50 text-sm">Bénévole introuvable</p>
        <Link href="/volunteers" className="text-purple-400 hover:text-purple-300 text-sm mt-3 inline-block">
          Retour aux bénévoles
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href={`/volunteers/${id}`}>
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-5 w-5" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-white">Modifier le bénévole</h1>
          <p className="text-sm text-white/50">{volunteer.member.full_name}</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Informations</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Field label="Disponibilité">
              <Select
                value={form.availability}
                onChange={(e) => setForm((f) => ({ ...f, availability: e.target.value }))}
              >
                <option value="" className="bg-[#1a1145]">Sélectionner...</option>
                <option value="full_time" className="bg-[#1a1145]">Temps plein</option>
                <option value="part_time" className="bg-[#1a1145]">Temps partiel</option>
                <option value="weekends" className="bg-[#1a1145]">Fins de semaine</option>
                <option value="evenings" className="bg-[#1a1145]">Soirées</option>
                <option value="on_call" className="bg-[#1a1145]">Sur appel</option>
              </Select>
            </Field>

            <Field label="Notes">
              <textarea
                value={form.notes}
                onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
                placeholder="Notes sur ce bénévole..."
                rows={4}
                className="flex w-full rounded-xl bg-white/[0.06] border border-white/[0.08] px-3 py-2 text-sm text-white/90 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/30 transition-all duration-200 placeholder:text-white/30 resize-none"
              />
            </Field>

            <div
              className="flex items-center justify-between rounded-xl bg-white/[0.03] border border-white/[0.06] px-4 py-3 cursor-pointer hover:bg-white/[0.05] transition-colors"
              onClick={() => setForm((f) => ({ ...f, is_active: !f.is_active }))}
            >
              <div>
                <p className="text-sm font-medium text-white/80">Actif</p>
                <p className="text-xs text-white/40">Le bénévole est disponible pour des missions</p>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={form.is_active}
                onClick={(e) => { e.stopPropagation(); setForm((f) => ({ ...f, is_active: !f.is_active })); }}
                className={`relative h-6 w-11 rounded-full transition-colors duration-200 shrink-0 ${
                  form.is_active ? 'bg-purple-600' : 'bg-white/10'
                }`}
              >
                <span
                  className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform duration-200 ${
                    form.is_active ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>
          </CardContent>
        </Card>

        <div className="flex items-center gap-3">
          <Button type="submit" disabled={isPending} className="min-w-[180px]">
            {isPending ? (
              <span className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Enregistrement...
              </span>
            ) : (
              'Enregistrer les modifications'
            )}
          </Button>
          <Link href={`/volunteers/${id}`}>
            <Button type="button" variant="outline" disabled={isPending}>
              Annuler
            </Button>
          </Link>
        </div>
      </form>
    </div>
  );
}
