'use client';

import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import {
  Users,
  DollarSign,
  Calendar,
  Heart,
  UserPlus,
  ChevronRight,
  ArrowUpRight,
  ArrowDownRight,
  Activity,
  Clock,
  CheckCircle2,
  AlertCircle,
  HandHelping,
  TrendingUp,
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Avatar } from '@/components/ui/avatar';
import { api } from '@/lib/api';
import { useAuthStore } from '@/stores/auth';
import { formatCurrency } from '@egliseconnect/utils';
import type { DashboardStats } from '@egliseconnect/types';

const ACTIVITY_ICON_MAP: Record<string, { icon: React.ElementType; color: string; bg: string }> = {
  member: { icon: UserPlus, color: 'text-purple-400', bg: 'bg-purple-500/10' },
  donation: { icon: DollarSign, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
  event: { icon: Calendar, color: 'text-blue-400', bg: 'bg-blue-500/10' },
  help: { icon: CheckCircle2, color: 'text-teal-400', bg: 'bg-teal-500/10' },
};

function formatRelativeTime(isoString: string): string {
  const now = Date.now();
  const diff = now - new Date(isoString).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'À l\'instant';
  if (mins < 60) return `Il y a ${mins} min`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `Il y a ${hours} h`;
  const days = Math.floor(hours / 24);
  return `Il y a ${days} j`;
}

const EVENT_TYPE_LABELS: Record<string, string> = {
  worship: 'Culte',
  group: 'Groupe',
  meal: 'Repas',
  special: 'Spécial',
  meeting: 'Réunion',
  training: 'Formation',
  outreach: 'Évangélisation',
  other: 'Autre',
};

const EVENT_TYPE_BADGE_VARIANT: Record<
  string,
  'default' | 'secondary' | 'success' | 'warning' | 'outline' | 'destructive'
> = {
  worship: 'default',
  group: 'secondary',
  meal: 'success',
  special: 'warning',
  meeting: 'outline',
};

// ─── Stat Card ───────────────────────────────────────────────────────────────

interface StatCardProps {
  title: string;
  value: string | number | undefined;
  subtitle: string;
  icon: React.ElementType;
  accentFrom: string;
  accentTo: string;
  trend?: { value: number; positive: boolean } | null;
  loading?: boolean;
}

function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  accentFrom,
  accentTo,
  trend,
  loading,
}: StatCardProps) {
  return (
    <Card className="relative overflow-hidden group hover:border-white/[0.14] transition-all duration-300 hover:shadow-[0_12px_40px_rgba(0,0,0,0.3)]">
      {/* Gradient accent bar at top */}
      <div
        className={`absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r ${accentFrom} ${accentTo} opacity-80`}
      />

      {/* Subtle glow on hover */}
      <div
        className={`absolute inset-0 bg-gradient-to-br ${accentFrom}/5 ${accentTo}/0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none rounded-2xl`}
      />

      <CardContent className="p-6 relative">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white/50 truncate">{title}</p>

            {loading ? (
              <>
                <Skeleton className="h-8 w-24 mt-2 mb-1" />
                <Skeleton className="h-4 w-32 mt-1" />
              </>
            ) : (
              <>
                <p className="text-3xl font-bold text-white mt-1 tracking-tight">
                  {value ?? '—'}
                </p>
                <p className="text-xs text-white/40 mt-1">{subtitle}</p>
              </>
            )}
          </div>

          <div
            className={`flex-shrink-0 p-3 rounded-xl bg-gradient-to-br ${accentFrom}/20 ${accentTo}/10 ml-4`}
          >
            <Icon className={`h-5 w-5 ${accentFrom.replace('from-', 'text-')}`} />
          </div>
        </div>

        {trend && !loading && (
          <div className="mt-4 flex items-center gap-1.5">
            {trend.positive ? (
              <ArrowUpRight className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
            ) : (
              <ArrowDownRight className="h-3.5 w-3.5 text-rose-400 shrink-0" />
            )}
            <span
              className={`text-xs font-medium ${trend.positive ? 'text-emerald-400' : 'text-rose-400'}`}
            >
              {trend.value}%
            </span>
            <span className="text-xs text-white/30">vs mois dernier</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ─── Quick Action Button ──────────────────────────────────────────────────────

interface QuickActionProps {
  label: string;
  icon: React.ElementType;
  href: string;
  accentClass: string;
}

function QuickAction({ label, icon: Icon, href, accentClass }: QuickActionProps) {
  const router = useRouter();
  return (
    <button
      onClick={() => router.push(href)}
      className={`flex items-center gap-2.5 px-4 py-2.5 rounded-xl border border-white/[0.08] bg-white/[0.04] hover:bg-white/[0.08] text-white/70 hover:text-white/90 text-sm font-medium transition-all duration-200 hover:border-white/[0.14] hover:shadow-[0_4px_20px_rgba(0,0,0,0.2)] group`}
    >
      <div className={`p-1.5 rounded-lg ${accentClass} transition-transform duration-200 group-hover:scale-110`}>
        <Icon className="h-3.5 w-3.5" />
      </div>
      {label}
    </button>
  );
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────

export default function DashboardPage() {
  const router = useRouter();
  const member = useAuthStore((s) => s.member);

  const { data: stats, isLoading } = useQuery<DashboardStats>({
    queryKey: ['dashboard', 'stats'],
    queryFn: () => api.dashboard.stats() as Promise<DashboardStats>,
    staleTime: 60_000,
  });

  // Greeting based on time of day
  const hour = new Date().getHours();
  const greeting =
    hour < 12 ? 'Bonjour' : hour < 18 ? 'Bon après-midi' : 'Bonsoir';

  const firstName = member?.first_name;

  // Today's date in French
  const todayLabel = new Intl.DateTimeFormat('fr-CA', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(new Date());

  const capitalizedDate = todayLabel.charAt(0).toUpperCase() + todayLabel.slice(1);

  return (
    <div className="space-y-8 pb-8">

      {/* ── Welcome Header ─────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">
            {greeting}
            {firstName && (
              <span className="bg-gradient-to-r from-purple-400 to-violet-300 bg-clip-text text-transparent">
                {' '}{firstName}
              </span>
            )}{' '}
            <span className="wave" aria-label="bonjour">👋</span>
          </h1>
          <p className="mt-1 text-white/50 text-sm">{capitalizedDate}</p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {member && (
            <div className="flex items-center gap-2.5 px-3 py-2 rounded-xl bg-white/[0.05] border border-white/[0.08]">
              <Avatar
                src={member.photo}
                fallback={member.full_name}
                size="sm"
              />
              <div className="hidden sm:block">
                <p className="text-sm font-medium text-white/80 leading-none">{member.full_name}</p>
                <p className="text-xs text-white/40 mt-0.5 capitalize">{member.role}</p>
              </div>
            </div>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => router.push('/reports')}
          >
            <TrendingUp className="h-4 w-4 mr-1.5" />
            Rapports
          </Button>
        </div>
      </div>

      {/* ── Stat Cards ─────────────────────────────────────────────────────── */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Membres actifs"
          value={stats?.members.active}
          subtitle={`${stats?.members.new_this_month ?? 0} nouveaux ce mois`}
          icon={Users}
          accentFrom="from-purple-500"
          accentTo="to-violet-400"
          trend={
            stats?.members.growth_rate != null
              ? { value: stats.members.growth_rate, positive: stats.members.growth_rate >= 0 }
              : null
          }
          loading={isLoading}
        />
        <StatCard
          title="Dons ce mois"
          value={
            stats?.donations.total_this_month != null
              ? formatCurrency(stats.donations.total_this_month)
              : undefined
          }
          subtitle={`${stats?.donations.count_this_month ?? 0} transactions`}
          icon={DollarSign}
          accentFrom="from-emerald-500"
          accentTo="to-teal-400"
          loading={isLoading}
        />
        <StatCard
          title="Événements à venir"
          value={stats?.events.upcoming_count}
          subtitle={`${stats?.events.this_month_count ?? 0} ce mois`}
          icon={Calendar}
          accentFrom="from-blue-500"
          accentTo="to-cyan-400"
          loading={isLoading}
        />
        <StatCard
          title="Bénévoles actifs"
          value={stats?.volunteers.active_count}
          subtitle={`${stats?.volunteers.hours_this_month ?? 0} h ce mois`}
          icon={Heart}
          accentFrom="from-rose-500"
          accentTo="to-pink-400"
          loading={isLoading}
        />
      </div>

      {/* ── Quick Actions ───────────────────────────────────────────────────── */}
      <div>
        <p className="text-xs font-semibold uppercase tracking-wider text-white/30 mb-3">
          Actions rapides
        </p>
        <div className="flex flex-wrap gap-2">
          <QuickAction
            label="Nouveau membre"
            icon={UserPlus}
            href="/members/new"
            accentClass="bg-purple-500/20 text-purple-400"
          />
          <QuickAction
            label="Nouveau don"
            icon={DollarSign}
            href="/donations/new"
            accentClass="bg-emerald-500/20 text-emerald-400"
          />
          <QuickAction
            label="Nouvel événement"
            icon={Calendar}
            href="/events/new"
            accentClass="bg-blue-500/20 text-blue-400"
          />
          <QuickAction
            label="Demande d'aide"
            icon={HandHelping}
            href="/help-requests"
            accentClass="bg-rose-500/20 text-rose-400"
          />
          <QuickAction
            label="Présence"
            icon={Activity}
            href="/attendance"
            accentClass="bg-amber-500/20 text-amber-400"
          />
        </div>
      </div>

      {/* ── Two-column section ──────────────────────────────────────────────── */}
      <div className="grid gap-6 lg:grid-cols-2">

        {/* Activité récente */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Activité récente</CardTitle>
                <CardDescription className="mt-0.5">Dernières actions dans le système</CardDescription>
              </div>
              <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" title="En direct" />
            </div>
          </CardHeader>
          <CardContent className="space-y-1 pt-0">
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex items-center gap-3 px-3 py-2.5">
                  <Skeleton className="h-8 w-8 rounded-lg" />
                  <div className="flex-1">
                    <Skeleton className="h-4 w-32 mb-1" />
                    <Skeleton className="h-3 w-24" />
                  </div>
                </div>
              ))
            ) : (stats?.recent_activities ?? []).length === 0 ? (
              <p className="text-sm text-white/40 text-center py-6">Aucune activité récente</p>
            ) : (
              (stats?.recent_activities ?? []).map((activity) => {
                const mapping = ACTIVITY_ICON_MAP[activity.type] ?? ACTIVITY_ICON_MAP.event;
                const Icon = mapping.icon;
                return (
                  <div
                    key={`${activity.type}-${activity.id}`}
                    className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-white/[0.04] transition-colors duration-150 group cursor-default"
                  >
                    <div className={`flex-shrink-0 p-2 rounded-lg ${mapping.bg}`}>
                      <Icon className={`h-4 w-4 ${mapping.color}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-white/70 leading-snug">
                        {activity.description}
                      </p>
                      <p className="text-xs font-medium text-white/90 truncate">
                        {activity.name}
                      </p>
                    </div>
                    <div className="flex-shrink-0 flex items-center gap-1 text-white/30">
                      <Clock className="h-3 w-3" />
                      <span className="text-xs whitespace-nowrap">{formatRelativeTime(activity.time)}</span>
                    </div>
                  </div>
                );
              })
            )}
          </CardContent>
        </Card>

        {/* Événements à venir */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Événements à venir</CardTitle>
                <CardDescription className="mt-0.5">Prochains événements</CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push('/events')}
                className="text-purple-400 hover:text-purple-300 -mr-2 text-xs"
              >
                Tout voir
                <ChevronRight className="h-3.5 w-3.5 ml-0.5" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-1 pt-0">
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex items-center gap-3 px-3 py-2.5">
                  <Skeleton className="h-10 w-10 rounded-lg" />
                  <div className="flex-1">
                    <Skeleton className="h-4 w-40 mb-1" />
                    <Skeleton className="h-3 w-28" />
                  </div>
                </div>
              ))
            ) : (stats?.upcoming_events ?? []).length === 0 ? (
              <p className="text-sm text-white/40 text-center py-6">Aucun événement à venir</p>
            ) : (
              (stats?.upcoming_events ?? []).map((event) => (
                <div
                  key={event.id}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-white/[0.04] transition-colors duration-150 cursor-pointer group"
                  onClick={() => router.push(`/events/${event.id}`)}
                >
                  {/* Date block */}
                  <div className="flex-shrink-0 w-10 text-center">
                    <p className="text-xs text-white/40 leading-none uppercase">
                      {new Intl.DateTimeFormat('fr-CA', { month: 'short' }).format(new Date(event.date))}
                    </p>
                    <p className="text-lg font-bold text-white/90 leading-tight">
                      {new Date(event.date).getDate()}
                    </p>
                  </div>

                  {/* Divider */}
                  <div className="flex-shrink-0 w-px h-8 bg-white/[0.08]" />

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white/85 truncate group-hover:text-white transition-colors">
                      {event.title}
                    </p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <Clock className="h-3 w-3 text-white/30 shrink-0" />
                      <span className="text-xs text-white/40">
                        {new Intl.DateTimeFormat('fr-CA', { hour: '2-digit', minute: '2-digit' }).format(new Date(event.date))}
                      </span>
                      <span className="text-white/20 text-xs">·</span>
                      <span className="text-xs text-white/40">{event.attendees} inscrits</span>
                    </div>
                  </div>

                  <Badge
                    variant={EVENT_TYPE_BADGE_VARIANT[event.type] ?? 'secondary'}
                    className="flex-shrink-0 hidden sm:inline-flex"
                  >
                    {EVENT_TYPE_LABELS[event.type] ?? event.type}
                  </Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      {/* ── Giving Overview + Help Stats ────────────────────────────────────── */}
      <div className="grid gap-6 lg:grid-cols-3">

        {/* Giving overview — spans 2 columns */}
        <Card className="lg:col-span-2">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Aperçu des dons</CardTitle>
                <CardDescription className="mt-0.5">Tendance des 6 derniers mois</CardDescription>
              </div>
              {stats?.donations.total_this_year && (
                <div className="text-right">
                  <p className="text-xs text-white/40">Total cette année</p>
                  <p className="text-lg font-bold text-white/90">
                    {formatCurrency(stats.donations.total_this_year)}
                  </p>
                </div>
              )}
              {isLoading && <Skeleton className="h-10 w-28" />}
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            {/* CSS bar chart */}
            <div className="flex items-end gap-3 h-36">
              {isLoading ? (
                Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="flex-1 flex flex-col items-center gap-2">
                    <div className="w-full flex items-end" style={{ height: '88px' }}>
                      <Skeleton className={`w-full rounded-t-lg ${i % 2 === 0 ? 'h-12' : 'h-16'}`} />
                    </div>
                    <Skeleton className="h-3 w-6" />
                  </div>
                ))
              ) : (stats?.giving_trends ?? []).length === 0 ? (
                <p className="text-sm text-white/40 text-center w-full py-8">Aucune donnée disponible</p>
              ) : (
                (stats?.giving_trends ?? []).map((item, idx) => {
                  const trends = stats?.giving_trends ?? [];
                  const isLast = idx === trends.length - 1;
                  return (
                    <div key={item.month} className="flex-1 flex flex-col items-center gap-2 group">
                      {/* Value tooltip on hover */}
                      <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-150">
                        <span className="text-[10px] font-medium text-white/70 whitespace-nowrap">
                          {formatCurrency(item.amount)}
                        </span>
                      </div>

                      {/* Bar */}
                      <div className="w-full relative flex items-end" style={{ height: '88px' }}>
                        <div
                          className={`w-full rounded-t-lg transition-all duration-500 ${
                            isLast
                              ? 'bg-gradient-to-t from-purple-600 to-violet-400 shadow-[0_0_16px_rgba(124,58,237,0.4)]'
                              : 'bg-white/[0.08] group-hover:bg-white/[0.14]'
                          }`}
                          style={{ height: `${item.pct}%` }}
                        />
                      </div>

                      {/* Month label */}
                      <span className={`text-xs font-medium ${isLast ? 'text-purple-400' : 'text-white/40'}`}>
                        {item.month}
                      </span>
                    </div>
                  );
                })
              )}
            </div>

            {/* Footer stats row */}
            <div className="mt-5 pt-4 border-t border-white/[0.06] grid grid-cols-3 gap-4">
              <div>
                <p className="text-xs text-white/40">Ce mois-ci</p>
                {isLoading ? (
                  <Skeleton className="h-5 w-20 mt-1" />
                ) : (
                  <p className="text-sm font-semibold text-white/90 mt-0.5">
                    {stats?.donations.total_this_month
                      ? formatCurrency(stats.donations.total_this_month)
                      : '—'}
                  </p>
                )}
              </div>
              <div>
                <p className="text-xs text-white/40">Don moyen</p>
                {isLoading ? (
                  <Skeleton className="h-5 w-20 mt-1" />
                ) : (
                  <p className="text-sm font-semibold text-white/90 mt-0.5">
                    {stats?.donations.average
                      ? formatCurrency(stats.donations.average)
                      : '—'}
                  </p>
                )}
              </div>
              <div>
                <p className="text-xs text-white/40">Transactions</p>
                {isLoading ? (
                  <Skeleton className="h-5 w-16 mt-1" />
                ) : (
                  <p className="text-sm font-semibold text-white/90 mt-0.5">
                    {stats?.donations.count_this_month ?? '—'}
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Status overview */}
        <Card>
          <CardHeader className="pb-4">
            <CardTitle>Aperçu du statut</CardTitle>
            <CardDescription className="mt-0.5">Indicateurs clés</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 pt-0">

            {/* Attendance */}
            <div className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-amber-400" />
                  <span className="text-sm text-white/70">Présence moy.</span>
                </div>
                {isLoading ? (
                  <Skeleton className="h-5 w-12" />
                ) : (
                  <span className="text-sm font-bold text-white/90">
                    {stats?.attendance.average_rate != null
                      ? `${stats.attendance.average_rate}%`
                      : '—'}
                  </span>
                )}
              </div>
              {!isLoading && stats?.attendance.average_rate != null && (
                <div className="h-1.5 w-full rounded-full bg-white/[0.06] overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-amber-500 to-yellow-400 transition-all duration-700"
                    style={{ width: `${Math.min(stats.attendance.average_rate, 100)}%` }}
                  />
                </div>
              )}
              {!isLoading && (
                <p className="text-xs text-white/40 mt-1.5">
                  {stats?.attendance.last_sunday_count ?? 0} présents dimanche dernier
                </p>
              )}
            </div>

            {/* Help requests */}
            <div className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]">
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className="h-4 w-4 text-rose-400" />
                <span className="text-sm text-white/70">Demandes d'aide</span>
              </div>
              {isLoading ? (
                <Skeleton className="h-8 w-full" />
              ) : (
                <div className="flex items-baseline gap-1.5">
                  <span className="text-2xl font-bold text-white/90">
                    {stats?.help_requests.open_count ?? 0}
                  </span>
                  <span className="text-xs text-white/40">en cours</span>
                </div>
              )}
              {!isLoading && (
                <p className="text-xs text-white/40 mt-1">
                  {stats?.help_requests.resolved_this_month ?? 0} résolues ce mois
                </p>
              )}
            </div>

            {/* Volunteers */}
            <div className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]">
              <div className="flex items-center gap-2 mb-2">
                <Heart className="h-4 w-4 text-rose-400" />
                <span className="text-sm text-white/70">Bénévoles</span>
              </div>
              {isLoading ? (
                <Skeleton className="h-8 w-full" />
              ) : (
                <div className="flex items-baseline gap-1.5">
                  <span className="text-2xl font-bold text-white/90">
                    {stats?.volunteers.active_count ?? 0}
                  </span>
                  <span className="text-xs text-white/40">actifs</span>
                </div>
              )}
              {!isLoading && (
                <p className="text-xs text-white/40 mt-1">
                  {stats?.volunteers.hours_this_month ?? 0} h de bénévolat ce mois
                </p>
              )}
            </div>

            <Button
              variant="outline"
              className="w-full mt-1 text-sm"
              onClick={() => router.push('/reports')}
            >
              <TrendingUp className="h-4 w-4 mr-2" />
              Voir tous les rapports
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
