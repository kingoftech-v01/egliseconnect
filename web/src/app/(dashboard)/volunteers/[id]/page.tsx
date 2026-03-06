'use client';

import { use } from 'react';
import Link from 'next/link';
import {
  ChevronLeft,
  Users,
  Briefcase,
  Calendar,
  Clock,
  Info,
  AlertTriangle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { DataTable, type Column } from '@/components/ui/data-table';
import { usePosition, useSchedules, type Schedule } from '@/hooks/use-volunteers';

// ─── Constants ────────────────────────────────────────────────────────────────

const POSITION_TYPE_LABELS: Record<string, string> = {
  worship: 'Louange',
  technical: 'Technique',
  children: 'Enfants',
  welcome: 'Accueil',
  prayer: 'Prière',
  administration: 'Administration',
  other: 'Autre',
};

const SCHEDULE_STATUS_LABELS: Record<string, string> = {
  pending: 'En attente',
  confirmed: 'Confirmé',
  absent: 'Absent',
  replaced: 'Remplacé',
};

const SCHEDULE_STATUS_VARIANT: Record<
  string,
  'default' | 'success' | 'warning' | 'destructive' | 'secondary'
> = {
  pending: 'warning',
  confirmed: 'success',
  absent: 'destructive',
  replaced: 'secondary',
};

// ─── Sub-components ───────────────────────────────────────────────────────────

function InfoRow({
  icon: Icon,
  label,
  children,
}: {
  icon: React.ElementType;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-3">
      <div className="p-2 rounded-lg bg-white/[0.04] border border-white/[0.06] text-white/40 mt-0.5 shrink-0">
        <Icon className="h-3.5 w-3.5" />
      </div>
      <div>
        <p className="text-xs text-white/40 uppercase tracking-wider">{label}</p>
        <div className="mt-0.5 text-sm text-white/80">{children}</div>
      </div>
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <div className="h-10 w-10 bg-white/[0.05] rounded-xl animate-pulse" />
        <div className="space-y-2">
          <div className="h-6 w-48 bg-white/[0.05] rounded-lg animate-pulse" />
          <div className="h-4 w-32 bg-white/[0.04] rounded-lg animate-pulse" />
        </div>
      </div>
      <div className="grid gap-6 md:grid-cols-3">
        <div className="md:col-span-1 h-64 bg-white/[0.05] rounded-2xl animate-pulse" />
        <div className="md:col-span-2 h-64 bg-white/[0.05] rounded-2xl animate-pulse" />
      </div>
    </div>
  );
}

// ─── History table columns ────────────────────────────────────────────────────

const historyColumns: Column<Schedule & Record<string, unknown>>[] = [
  {
    key: 'member_name',
    header: 'Bénévole',
    render: (item) => (
      <p className="font-medium text-white/90">{item.member_name || '—'}</p>
    ),
  },
  {
    key: 'scheduled_date',
    header: 'Date',
    render: (item) =>
      item.scheduled_date
        ? new Date(item.scheduled_date).toLocaleDateString('fr-CA', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          })
        : '—',
  },
  {
    key: 'status',
    header: 'Statut',
    render: (item) => (
      <Badge variant={SCHEDULE_STATUS_VARIANT[item.status] || 'secondary'}>
        {SCHEDULE_STATUS_LABELS[item.status] || item.status}
      </Badge>
    ),
  },
  {
    key: 'notes',
    header: 'Notes',
    render: (item) => (
      <p className="text-white/50 text-xs max-w-xs truncate">{item.notes || '—'}</p>
    ),
  },
];

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function PositionDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: position, isLoading, isError } = usePosition(id);

  const scheduleParams = new URLSearchParams();
  scheduleParams.set('position', id);
  scheduleParams.set('page_size', '50');
  const { data: schedulesData, isLoading: schedulesLoading } = useSchedules(
    scheduleParams.toString(),
  );

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Link href="/volunteers">
            <Button variant="ghost" size="icon">
              <ChevronLeft className="h-5 w-5" />
            </Button>
          </Link>
          <div className="h-4 w-24 bg-white/[0.05] rounded animate-pulse" />
        </div>
        <SkeletonCard />
      </div>
    );
  }

  // Error / not found state
  if (isError || !position) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Link href="/volunteers">
            <Button variant="ghost" size="icon">
              <ChevronLeft className="h-5 w-5" />
            </Button>
          </Link>
          <p className="text-white/40 text-sm">Bénévoles</p>
        </div>
        <div className="rounded-2xl bg-white/[0.05] backdrop-blur-xl border border-white/[0.08] p-12 text-center">
          <div className="flex justify-center mb-4">
            <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20">
              <AlertTriangle className="h-8 w-8 text-amber-400" />
            </div>
          </div>
          <p className="text-white/70 font-medium">Poste introuvable</p>
          <p className="text-white/40 text-sm mt-1">
            Ce poste n&apos;existe pas ou a été supprimé.
          </p>
          <Link href="/volunteers" className="inline-block mt-4">
            <Button variant="outline">Retour à la liste</Button>
          </Link>
        </div>
      </div>
    );
  }

  // Compute stats from schedules
  const confirmed = schedulesData?.results.filter((s) => s.status === 'confirmed').length ?? 0;
  const pending = schedulesData?.results.filter((s) => s.status === 'pending').length ?? 0;
  const uniqueVolunteers = new Set(
    schedulesData?.results.map((s) => s.member).filter(Boolean) ?? [],
  ).size;

  const capacityPercent =
    position.max_volunteers > 0
      ? Math.min(
          100,
          Math.round(((position.active_volunteer_count ?? 0) / position.max_volunteers) * 100),
        )
      : 0;

  const isUnderstaffed =
    typeof position.active_volunteer_count === 'number' &&
    position.active_volunteer_count < position.min_volunteers;

  return (
    <div className="space-y-6">
      {/* Back + title */}
      <div className="flex items-center gap-3">
        <Link href="/volunteers">
          <Button variant="ghost" size="icon" className="shrink-0">
            <ChevronLeft className="h-5 w-5" />
          </Button>
        </Link>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl font-bold text-white truncate">{position.name}</h1>
            <Badge variant={position.is_active ? 'success' : 'secondary'}>
              {position.is_active ? 'Actif' : 'Inactif'}
            </Badge>
            {isUnderstaffed && (
              <Badge variant="destructive">Effectif insuffisant</Badge>
            )}
          </div>
          <p className="text-white/40 text-sm mt-0.5">
            {POSITION_TYPE_LABELS[position.position_type] || position.position_type}
          </p>
        </div>
      </div>

      {/* Top grid: info + capacity */}
      <div className="grid gap-6 md:grid-cols-3">
        {/* Position info */}
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Briefcase className="h-4 w-4 text-purple-400" />
              Informations
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <InfoRow icon={Info} label="Type">
              {POSITION_TYPE_LABELS[position.position_type] || position.position_type}
            </InfoRow>
            <InfoRow icon={Users} label="Capacité">
              {position.min_volunteers} – {position.max_volunteers} bénévoles
            </InfoRow>
            <InfoRow icon={Users} label="Bénévoles actifs">
              <span
                className={
                  isUnderstaffed ? 'text-rose-400 font-semibold' : 'text-emerald-400 font-semibold'
                }
              >
                {position.active_volunteer_count ?? '—'}
              </span>
              {isUnderstaffed && (
                <span className="text-white/40 text-xs ml-2">
                  (min. {position.min_volunteers} requis)
                </span>
              )}
            </InfoRow>

            {!!position.description && (
              <div className="pt-2 border-t border-white/[0.06]">
                <p className="text-xs text-white/40 uppercase tracking-wider mb-1.5">Description</p>
                <p className="text-sm text-white/60 leading-relaxed">{position.description}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Volunteer capacity bar + schedule stats */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Users className="h-4 w-4 text-purple-400" />
              Occupation du poste
            </CardTitle>
            <CardDescription>
              Suivi de l&apos;affectation des bénévoles à ce poste
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Capacity bar */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-white/50">Taux d&apos;occupation</span>
                <span className="text-white font-medium tabular-nums">{capacityPercent}%</span>
              </div>
              <div className="h-2.5 rounded-full bg-white/[0.06] overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${capacityPercent}%`,
                    background:
                      capacityPercent >= 100
                        ? 'rgb(52 211 153)'
                        : capacityPercent >= 60
                        ? 'rgb(124 58 237)'
                        : 'rgb(251 191 36)',
                  }}
                />
              </div>
              <div className="flex justify-between text-xs text-white/30">
                <span>0</span>
                <span>Min: {position.min_volunteers}</span>
                <span>Max: {position.max_volunteers}</span>
              </div>
            </div>

            {/* Quick stats grid */}
            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-xl bg-white/[0.04] border border-white/[0.06] p-3 text-center">
                <p className="text-2xl font-bold text-white tabular-nums">{uniqueVolunteers}</p>
                <p className="text-xs text-white/40 mt-0.5">Bénévoles distincts</p>
              </div>
              <div className="rounded-xl bg-white/[0.04] border border-white/[0.06] p-3 text-center">
                <p className="text-2xl font-bold text-emerald-400 tabular-nums">{confirmed}</p>
                <p className="text-xs text-white/40 mt-0.5">Confirmés</p>
              </div>
              <div className="rounded-xl bg-white/[0.04] border border-white/[0.06] p-3 text-center">
                <p className="text-2xl font-bold text-amber-400 tabular-nums">{pending}</p>
                <p className="text-xs text-white/40 mt-0.5">En attente</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Schedule history */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Calendar className="h-4 w-4 text-purple-400" />
            Historique des planifications
          </CardTitle>
          <CardDescription>
            Toutes les affectations passées et à venir pour ce poste
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0 pt-2">
          {schedulesLoading ? (
            <div className="p-6 space-y-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-10 bg-white/[0.04] rounded-xl animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="px-6 pb-6">
              <DataTable
                columns={historyColumns}
                data={
                  (schedulesData?.results ?? []) as (Schedule & Record<string, unknown>)[]
                }
                loading={false}
                emptyMessage="Aucune planification pour ce poste"
              />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Footer hint */}
      <div className="flex items-center gap-2 text-white/30 text-xs">
        <Clock className="h-3.5 w-3.5" />
        <span>
          Affichage des {schedulesData?.results.length ?? 0} planifications les plus récentes.
        </span>
      </div>
    </div>
  );
}
