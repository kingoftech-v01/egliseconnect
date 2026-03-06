'use client';

import { useState, useMemo } from 'react';
import {
  BarChart3,
  TrendingUp,
  Users,
  DollarSign,
  Calendar,
  Clock,
  Download,
  Plus,
  Save,
  Heart,
  UserCheck,
  Activity,
  Share2,
  FileText,
  ChevronRight,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { DataTable, type Column } from '@/components/ui/data-table';
import { InfiniteScrollTable } from '@/components/ui/infinite-scroll-table';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogContent,
  DialogFooter,
  DialogClose,
} from '@/components/ui/dialog';
import { useToast } from '@/components/ui/toast';
import {
  useReportsDashboard,
  useAttendanceReport,
  useDonationReport,
  useVolunteerReport,
  useInfiniteSavedReports,
  useCreateSavedReport,
} from '@/hooks/use-reports';

// ─── Types ──────────────────────────────────────────────────────────────────

interface SavedReport extends Record<string, unknown> {
  id: string;
  name: string;
  type: string;
  created_at: string;
  is_shared: boolean;
  description?: string;
}

// ─── Mini Bar Chart (CSS-based) ──────────────────────────────────────────────

interface BarChartProps {
  data: { label: string; value: number }[];
  maxValue?: number;
  className?: string;
}

function MiniBarChart({ data, maxValue, className }: BarChartProps) {
  const max = maxValue ?? Math.max(...data.map((d) => d.value), 1);
  return (
    <div className={`flex items-end gap-1 h-16 ${className ?? ''}`}>
      {data.map((bar, i) => {
        const pct = Math.max(4, Math.round((bar.value / max) * 100));
        return (
          <div key={i} className="flex-1 flex flex-col items-center gap-1 group">
            <div
              className="w-full rounded-t bg-gradient-to-t from-purple-600 to-purple-400 transition-all duration-300 group-hover:from-purple-500 group-hover:to-purple-300"
              style={{ height: `${pct}%` }}
              title={`${bar.label}: ${bar.value}`}
            />
            <span className="text-[9px] text-white/30 truncate w-full text-center">
              {bar.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}

// ─── Stat Card ───────────────────────────────────────────────────────────────

interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  icon: React.ElementType;
  trend?: number;
  loading?: boolean;
}

function StatCard({ label, value, sub, icon: Icon, trend, loading }: StatCardProps) {
  if (loading) {
    return (
      <Card>
        <CardContent className="p-5">
          <Skeleton className="h-4 w-24 mb-3" />
          <Skeleton className="h-8 w-32 mb-2" />
          <Skeleton className="h-3 w-20" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-purple-600/5 to-transparent pointer-events-none" />
      <CardContent className="p-5">
        <div className="flex items-start justify-between mb-3">
          <p className="text-sm text-white/50">{label}</p>
          <div className="p-2 rounded-xl bg-purple-600/10 border border-purple-500/20">
            <Icon className="h-4 w-4 text-purple-400" />
          </div>
        </div>
        <p className="text-2xl font-bold text-white">{value}</p>
        {(sub || trend !== undefined) && (
          <div className="flex items-center gap-2 mt-1">
            {trend !== undefined && (
              <span
                className={`text-xs font-medium flex items-center gap-0.5 ${
                  trend >= 0 ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                <TrendingUp className={`h-3 w-3 ${trend < 0 ? 'rotate-180' : ''}`} />
                {Math.abs(trend)}%
              </span>
            )}
            {sub && <p className="text-xs text-white/40">{sub}</p>}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ─── Months labels ───────────────────────────────────────────────────────────

const MOIS_COURTS = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc'];

// ─── Mock / fallback chart data helpers ──────────────────────────────────────

function buildMonthlyBars(rawData: unknown, field = 'total') {
  if (Array.isArray(rawData)) {
    return rawData.slice(-6).map((d: Record<string, unknown>, i) => ({
      label: MOIS_COURTS[i] ?? String(i + 1),
      value: Number(d[field] ?? 0),
    }));
  }
  return [];
}

// ─── Vue d'ensemble Tab ───────────────────────────────────────────────────────

function OverviewTab() {
  const { data: membersData, isLoading: membersLoading } = useReportsDashboard('members');
  const { data: donationsData, isLoading: donationsLoading } = useReportsDashboard('donations');
  const { data: eventsData, isLoading: eventsLoading } = useReportsDashboard('events');
  const { data: volunteersData, isLoading: volunteersLoading } = useReportsDashboard('volunteers');

  const sections = [
    {
      title: 'Croissance des membres',
      description: 'Évolution du nombre de membres actifs',
      icon: Users,
      color: 'from-blue-600/20 to-blue-600/5',
      iconColor: 'text-blue-400',
      borderColor: 'border-blue-500/20',
      loading: membersLoading,
      data: buildMonthlyBars(membersData),
      link: '#membres',
    },
    {
      title: 'Tendances des dons',
      description: 'Évolution mensuelle des contributions',
      icon: DollarSign,
      color: 'from-emerald-600/20 to-emerald-600/5',
      iconColor: 'text-emerald-400',
      borderColor: 'border-emerald-500/20',
      loading: donationsLoading,
      data: buildMonthlyBars(donationsData, 'amount'),
      link: '#dons',
    },
    {
      title: "Taux de présence",
      description: 'Présence moyenne aux services',
      icon: Calendar,
      color: 'from-purple-600/20 to-purple-600/5',
      iconColor: 'text-purple-400',
      borderColor: 'border-purple-500/20',
      loading: eventsLoading,
      data: buildMonthlyBars(eventsData, 'attendance'),
      link: '#presence',
    },
    {
      title: 'Participation bénévole',
      description: 'Heures de bénévolat par mois',
      icon: Heart,
      color: 'from-rose-600/20 to-rose-600/5',
      iconColor: 'text-rose-400',
      borderColor: 'border-rose-500/20',
      loading: volunteersLoading,
      data: buildMonthlyBars(volunteersData, 'hours'),
      link: '#benevoles',
    },
  ];

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2">
        {sections.map((section) => (
          <Card key={section.title} className="relative overflow-hidden group">
            <div
              className={`absolute inset-0 bg-gradient-to-br ${section.color} pointer-events-none`}
            />
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-xl bg-white/[0.06] border ${section.borderColor}`}>
                    <section.icon className={`h-4 w-4 ${section.iconColor}`} />
                  </div>
                  <div>
                    <CardTitle className="text-sm">{section.title}</CardTitle>
                    <CardDescription className="text-xs mt-0.5">
                      {section.description}
                    </CardDescription>
                  </div>
                </div>
                <button className="text-white/30 hover:text-white/60 transition-colors">
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </CardHeader>
            <CardContent className="pb-5">
              {section.loading ? (
                <div className="h-16 flex items-end gap-1">
                  {[...Array(6)].map((_, i) => (
                    <div
                      key={i}
                      className="flex-1 rounded-t animate-pulse bg-white/[0.04]"
                      style={{ height: `${30 + i * 10}%` }}
                    />
                  ))}
                </div>
              ) : (
                <MiniBarChart data={section.data} />
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick links */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Accès rapide aux rapports</CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { label: 'Rapport membres', icon: Users, desc: 'Statistiques détaillées' },
              { label: 'Rapport dons', icon: DollarSign, desc: 'Analyse financière' },
              { label: 'Rapport présence', icon: Calendar, desc: 'Taux par service' },
              { label: 'Rapport bénévoles', icon: Heart, desc: 'Heures et postes' },
            ].map((link) => (
              <button
                key={link.label}
                className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.07] hover:border-purple-500/20 transition-all text-left group"
              >
                <div className="p-2 rounded-lg bg-purple-600/10 group-hover:bg-purple-600/20 transition-colors">
                  <link.icon className="h-4 w-4 text-purple-400" />
                </div>
                <div>
                  <p className="text-sm font-medium text-white/80">{link.label}</p>
                  <p className="text-xs text-white/40">{link.desc}</p>
                </div>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ─── Membres Tab ──────────────────────────────────────────────────────────────

function MembresTab() {
  const { data, isLoading } = useReportsDashboard('members');

  const rawStats = data as Record<string, unknown> | undefined;

  const stats = {
    total: Number(rawStats?.total_members ?? 0),
    active: Number(rawStats?.active_members ?? 0),
    inactive: Number(rawStats?.inactive_members ?? 0),
    growth_rate: Number(rawStats?.growth_rate ?? 0),
    new_this_month: Number(rawStats?.new_this_month ?? 0),
  };

  const registrationData = useMemo(() => {
    if (Array.isArray(rawStats?.by_month)) {
      return (rawStats.by_month as Record<string, unknown>[]).map((m, i) => ({
        label: MOIS_COURTS[i] ?? String(i + 1),
        value: Number(m.count ?? 0),
      }));
    }
    return [];
  }, [rawStats]);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-3">
          {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-28" />)}
        </div>
        <Skeleton className="h-48" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats row */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="p-5 text-center">
            <div className="inline-flex p-3 rounded-full bg-blue-500/10 mb-3">
              <Users className="h-6 w-6 text-blue-400" />
            </div>
            <p className="text-3xl font-bold text-white">{stats.total}</p>
            <p className="text-sm text-white/50 mt-1">Total membres</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5 text-center">
            <div className="inline-flex p-3 rounded-full bg-emerald-500/10 mb-3">
              <UserCheck className="h-6 w-6 text-emerald-400" />
            </div>
            <p className="text-3xl font-bold text-white">{stats.active}</p>
            <p className="text-sm text-white/50 mt-1">Membres actifs</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5 text-center">
            <div className="inline-flex p-3 rounded-full bg-white/[0.06] mb-3">
              <Activity className="h-6 w-6 text-white/40" />
            </div>
            <p className="text-3xl font-bold text-white">{stats.inactive}</p>
            <p className="text-sm text-white/50 mt-1">Membres inactifs</p>
          </CardContent>
        </Card>
      </div>

      {/* Growth + chart */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Croissance</CardTitle>
          </CardHeader>
          <CardContent className="pt-0 space-y-4">
            <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]">
              <div>
                <p className="text-xs text-white/40">Taux de croissance</p>
                <p className="text-lg font-bold text-emerald-400">+{stats.growth_rate}%</p>
              </div>
              <TrendingUp className="h-5 w-5 text-emerald-400" />
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]">
              <div>
                <p className="text-xs text-white/40">Nouveaux ce mois</p>
                <p className="text-lg font-bold text-white">{stats.new_this_month}</p>
              </div>
              <Plus className="h-5 w-5 text-purple-400" />
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]">
              <div>
                <p className="text-xs text-white/40">Taux d'activité</p>
                <p className="text-lg font-bold text-white">
                  {stats.total > 0 ? Math.round((stats.active / stats.total) * 100) : 0}%
                </p>
              </div>
              <Activity className="h-5 w-5 text-blue-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-sm">Inscriptions par mois</CardTitle>
            <CardDescription>Nombre de nouveaux membres enregistrés</CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <MiniBarChart data={registrationData} className="h-32" />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// ─── Dons Tab ─────────────────────────────────────────────────────────────────

function DonsTab() {
  const currentYear = new Date().getFullYear();
  const [year, setYear] = useState(currentYear);

  const params = new URLSearchParams();
  params.set('year', String(year));

  const { data, isLoading } = useDonationReport(params.toString());

  const rawStats = data as Record<string, unknown> | undefined;

  const stats = {
    total: Number(rawStats?.total_amount ?? 0),
    average: Number(rawStats?.average_donation ?? 0),
    count: Number(rawStats?.total_donations ?? 0),
    top_donor: (rawStats?.top_donor as string) ?? '—',
  };

  const monthlyData = useMemo(() => {
    if (Array.isArray(rawStats?.monthly)) {
      return (rawStats.monthly as Record<string, unknown>[]).map((m, i) => ({
        label: MOIS_COURTS[i] ?? String(i + 1),
        value: Number(m.amount ?? 0),
      }));
    }
    return [];
  }, [rawStats]);

  const byType = useMemo(() => {
    if (Array.isArray(rawStats?.by_type)) {
      return rawStats.by_type as { type: string; amount: number; percentage: number }[];
    }
    return [];
  }, [rawStats]);

  const formatAmount = (v: number) =>
    new Intl.NumberFormat('fr-CA', { style: 'currency', currency: 'CAD' }).format(v);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-12 w-32" />
        <div className="grid gap-4 sm:grid-cols-3">
          {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-28" />)}
        </div>
        <Skeleton className="h-48" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Year selector */}
      <div className="flex items-center gap-3">
        <label className="text-sm text-white/50">Année :</label>
        <Select
          value={String(year)}
          onChange={(e) => setYear(Number(e.target.value))}
          className="w-28"
        >
          {[currentYear, currentYear - 1, currentYear - 2, currentYear - 3].map((y) => (
            <option key={y} value={y} className="bg-[#1a1145]">
              {y}
            </option>
          ))}
        </Select>
      </div>

      {/* Key metrics */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs text-white/40">Total des dons</p>
              <DollarSign className="h-4 w-4 text-emerald-400" />
            </div>
            <p className="text-2xl font-bold text-white">{formatAmount(stats.total)}</p>
            <p className="text-xs text-white/40 mt-1">{stats.count} transactions</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs text-white/40">Don moyen</p>
              <TrendingUp className="h-4 w-4 text-purple-400" />
            </div>
            <p className="text-2xl font-bold text-white">{formatAmount(stats.average)}</p>
            <p className="text-xs text-white/40 mt-1">Par transaction</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs text-white/40">Donateur principal</p>
              <Users className="h-4 w-4 text-blue-400" />
            </div>
            <p className="text-lg font-bold text-white truncate">{stats.top_donor}</p>
            <p className="text-xs text-white/40 mt-1">Contribution maximale</p>
          </CardContent>
        </Card>
      </div>

      {/* Monthly chart + by type */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-sm">Dons mensuels — {year}</CardTitle>
            <CardDescription>Montant total collecté par mois</CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <MiniBarChart data={monthlyData} className="h-32" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Par type de don</CardTitle>
          </CardHeader>
          <CardContent className="pt-0 space-y-3">
            {byType.length === 0 ? (
              <p className="text-xs text-white/30 text-center py-4">Aucune donnée disponible</p>
            ) : byType.map((item) => (
              <div key={item.type}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-white/60">{item.type}</span>
                  <span className="text-xs text-white/40">{item.percentage}%</span>
                </div>
                <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-purple-600 to-purple-400 transition-all duration-500"
                    style={{ width: `${item.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// ─── Présence Tab ─────────────────────────────────────────────────────────────

function PresenceTab() {
  const { data, isLoading } = useAttendanceReport();

  const rawStats = data as Record<string, unknown> | undefined;

  const sessions = useMemo(() => {
    if (Array.isArray(rawStats?.sessions)) {
      return rawStats.sessions as {
        date: string;
        service_type: string;
        count: number;
        capacity: number;
      }[];
    }
    return [];
  }, [rawStats]);

  const byServiceType = useMemo(() => {
    if (Array.isArray(rawStats?.by_service_type)) {
      return rawStats.by_service_type as { type: string; average: number; sessions: number }[];
    }
    return [];
  }, [rawStats]);

  const trendData = useMemo(() => {
    if (Array.isArray(rawStats?.trends)) {
      return (rawStats.trends as Record<string, unknown>[]).slice(-6).map((t, i) => ({
        label: MOIS_COURTS[i] ?? String(i + 1),
        value: Number(t.average ?? t.count ?? 0),
      }));
    }
    return [];
  }, [rawStats]);

  const sessionColumns: Column<(typeof sessions)[0] & Record<string, unknown>>[] = [
    {
      key: 'date',
      header: 'Date',
      render: (item) =>
        new Date(item.date as string).toLocaleDateString('fr-CA', {
          weekday: 'long',
          year: 'numeric',
          month: 'long',
          day: 'numeric',
        }),
    },
    {
      key: 'service_type',
      header: 'Type de service',
      render: (item) => (
        <Badge variant="secondary">{item.service_type as string}</Badge>
      ),
    },
    {
      key: 'count',
      header: 'Présents',
      render: (item) => (
        <span className="font-medium text-white">{item.count as number}</span>
      ),
    },
    {
      key: 'capacity',
      header: 'Taux',
      render: (item) => {
        const pct = Math.round(((item.count as number) / (item.capacity as number)) * 100);
        const color = pct >= 80 ? 'text-emerald-400' : pct >= 60 ? 'text-amber-400' : 'text-white/60';
        return <span className={`font-medium ${color}`}>{pct}%</span>;
      },
    },
  ];

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 lg:grid-cols-3">
        {/* Trend chart */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-sm">Tendance de présence</CardTitle>
            <CardDescription>Moyenne mensuelle des derniers 6 mois</CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <MiniBarChart data={trendData} className="h-32" />
          </CardContent>
        </Card>

        {/* By service type */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Par type de service</CardTitle>
          </CardHeader>
          <CardContent className="pt-0 space-y-3">
            {byServiceType.length === 0 ? (
              <p className="text-xs text-white/30 text-center py-4">Aucune donnée disponible</p>
            ) : byServiceType.map((item) => (
              <div
                key={item.type}
                className="flex items-center justify-between p-2 rounded-lg bg-white/[0.03] border border-white/[0.04]"
              >
                <div>
                  <p className="text-xs font-medium text-white/80">{item.type}</p>
                  <p className="text-xs text-white/40">{item.sessions} sessions</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-white">{item.average}</p>
                  <p className="text-xs text-white/40">moy.</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Recent sessions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Sessions récentes</CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          <DataTable
            columns={sessionColumns}
            data={sessions as ((typeof sessions)[0] & Record<string, unknown>)[]}
            emptyMessage="Aucune session enregistrée"
          />
        </CardContent>
      </Card>
    </div>
  );
}

// ─── Bénévoles Tab ────────────────────────────────────────────────────────────

function BenevolesTab() {
  const { data, isLoading } = useVolunteerReport();

  const rawStats = data as Record<string, unknown> | undefined;

  const stats = {
    total: Number(rawStats?.total_volunteers ?? 0),
    active: Number(rawStats?.active_volunteers ?? 0),
    hours_month: Number(rawStats?.hours_this_month ?? 0),
    hours_year: Number(rawStats?.hours_this_year ?? 0),
  };

  const byPosition = useMemo(() => {
    if (Array.isArray(rawStats?.by_position)) {
      return rawStats.by_position as { position: string; hours: number; volunteers: number }[];
    }
    return [];
  }, [rawStats]);

  const topVolunteers = useMemo(() => {
    if (Array.isArray(rawStats?.top_volunteers)) {
      return rawStats.top_volunteers as { name: string; hours: number; position: string }[];
    }
    return [];
  }, [rawStats]);

  const maxHours = Math.max(...byPosition.map((p) => p.hours), 1);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-4">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-24" />)}
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats row */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: 'Total bénévoles', value: stats.total, icon: Users, color: 'text-blue-400' },
          { label: 'Bénévoles actifs', value: stats.active, icon: UserCheck, color: 'text-emerald-400' },
          { label: 'Heures ce mois', value: stats.hours_month, icon: Clock, color: 'text-purple-400' },
          { label: 'Heures cette année', value: stats.hours_year, icon: BarChart3, color: 'text-amber-400' },
        ].map((s) => (
          <Card key={s.label}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs text-white/40">{s.label}</p>
                <s.icon className={`h-4 w-4 ${s.color}`} />
              </div>
              <p className="text-2xl font-bold text-white">{s.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* Hours by position */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Heures par poste</CardTitle>
          </CardHeader>
          <CardContent className="pt-0 space-y-3">
            {byPosition.length === 0 ? (
              <p className="text-xs text-white/30 text-center py-4">Aucune donnée disponible</p>
            ) : byPosition.map((item) => (
              <div key={item.position}>
                <div className="flex items-center justify-between mb-1">
                  <div>
                    <span className="text-xs text-white/70">{item.position}</span>
                    <span className="text-xs text-white/30 ml-2">{item.volunteers} bénévoles</span>
                  </div>
                  <span className="text-xs font-medium text-white">{item.hours}h</span>
                </div>
                <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-purple-600 to-purple-400 transition-all duration-500"
                    style={{ width: `${(item.hours / maxHours) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Top volunteers */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Meilleurs bénévoles</CardTitle>
          </CardHeader>
          <CardContent className="pt-0 space-y-2">
            {topVolunteers.length === 0 ? (
              <p className="text-xs text-white/30 text-center py-4">Aucune donnée disponible</p>
            ) : topVolunteers.map((v, i) => (
              <div
                key={v.name}
                className="flex items-center gap-3 p-2.5 rounded-xl bg-white/[0.03] border border-white/[0.04]"
              >
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                    i === 0
                      ? 'bg-amber-500/20 text-amber-400'
                      : i === 1
                        ? 'bg-slate-400/20 text-slate-400'
                        : i === 2
                          ? 'bg-orange-700/20 text-orange-600'
                          : 'bg-white/[0.06] text-white/40'
                  }`}
                >
                  {i + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white/80 truncate">{v.name}</p>
                  <p className="text-xs text-white/40">{v.position}</p>
                </div>
                <div className="flex items-center gap-1 text-purple-400">
                  <Clock className="h-3 w-3" />
                  <span className="text-xs font-medium">{v.hours}h</span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// ─── Rapports sauvegardés Tab ─────────────────────────────────────────────────

const REPORT_TYPE_LABELS: Record<string, string> = {
  members: 'Membres',
  donations: 'Dons',
  attendance: 'Présence',
  volunteers: 'Bénévoles',
  events: 'Événements',
  overview: 'Vue d\'ensemble',
};

function RapportsSauvegardésTab() {
  const { toast } = useToast();
  const [createOpen, setCreateOpen] = useState(false);
  const [newReport, setNewReport] = useState({ name: '', type: 'members', description: '' });

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteSavedReports();

  const reports = (data?.pages.flatMap((p) => p.results) ?? []) as SavedReport[];
  const totalCount = data?.pages[0]?.count;
  const createReport = useCreateSavedReport();

  const columns: Column<SavedReport & Record<string, unknown>>[] = [
    {
      key: 'name',
      header: 'Nom du rapport',
      render: (item) => (
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-purple-400 shrink-0" />
          <div>
            <p className="font-medium text-white/90">{item.name as string}</p>
            {!!item.description && (
              <p className="text-xs text-white/40 truncate max-w-xs">
                {item.description as string}
              </p>
            )}
          </div>
        </div>
      ),
    },
    {
      key: 'type',
      header: 'Type',
      render: (item) => (
        <Badge variant="outline">
          {REPORT_TYPE_LABELS[item.type as string] ?? (item.type as string)}
        </Badge>
      ),
    },
    {
      key: 'created_at',
      header: 'Créé le',
      render: (item) =>
        new Date(item.created_at as string).toLocaleDateString('fr-CA', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
        }),
    },
    {
      key: 'is_shared',
      header: 'Partagé',
      render: (item) =>
        (item.is_shared as boolean) ? (
          <Badge variant="success">
            <Share2 className="h-3 w-3 mr-1" />
            Partagé
          </Badge>
        ) : (
          <Badge variant="secondary">Privé</Badge>
        ),
    },
    {
      key: 'actions',
      header: '',
      render: () => (
        <button
          className="p-1.5 rounded-lg text-white/30 hover:text-white/60 hover:bg-white/[0.06] transition-colors"
          title="Télécharger"
          onClick={(e) => {
            e.stopPropagation();
            toast({ type: 'info', title: 'Téléchargement', description: 'Préparation du fichier…' });
          }}
        >
          <Download className="h-4 w-4" />
        </button>
      ),
    },
  ];

  const handleCreate = () => {
    if (!newReport.name.trim()) {
      toast({ type: 'error', title: 'Nom requis', description: 'Veuillez entrer un nom pour le rapport.' });
      return;
    }
    createReport.mutate(
      { name: newReport.name, type: newReport.type, description: newReport.description },
      {
        onSuccess: () => {
          toast({ type: 'success', title: 'Rapport créé', description: `"${newReport.name}" a été sauvegardé avec succès.` });
          setNewReport({ name: '', type: 'members', description: '' });
          setCreateOpen(false);
        },
        onError: () => {
          toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer le rapport.' });
        },
      },
    );
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-medium text-white/70">Rapports sauvegardés</h3>
          <p className="text-xs text-white/40 mt-0.5">{reports.length} rapport(s) disponible(s)</p>
        </div>
        <Button onClick={() => setCreateOpen(true)} size="sm">
          <Plus className="h-4 w-4 mr-1.5" />
          Nouveau rapport
        </Button>
      </div>

      <InfiniteScrollTable
        columns={columns}
        data={reports as (SavedReport & Record<string, unknown>)[]}
        totalCount={totalCount}
        isLoading={isLoading}
        fetchNextPage={fetchNextPage}
        hasNextPage={hasNextPage}
        isFetchingNextPage={isFetchingNextPage}
        error={error}
        emptyMessage="Aucun rapport sauvegardé"
      />

      {/* Create dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)}>
        <DialogClose onClose={() => setCreateOpen(false)} />
        <DialogHeader>
          <DialogTitle>Créer un rapport</DialogTitle>
          <DialogDescription>
            Configurez et sauvegardez un nouveau rapport personnalisé.
          </DialogDescription>
        </DialogHeader>
        <DialogContent>
          <div className="space-y-4">
            <div>
              <label className="text-xs text-white/50 mb-1.5 block">Nom du rapport *</label>
              <Input
                placeholder="Ex: Rapport membres T1 2026"
                value={newReport.name}
                onChange={(e) => setNewReport((p) => ({ ...p, name: e.target.value }))}
              />
            </div>
            <div>
              <label className="text-xs text-white/50 mb-1.5 block">Type de rapport</label>
              <Select
                value={newReport.type}
                onChange={(e) => setNewReport((p) => ({ ...p, type: e.target.value }))}
              >
                {Object.entries(REPORT_TYPE_LABELS).map(([value, label]) => (
                  <option key={value} value={value} className="bg-[#1a1145]">
                    {label}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <label className="text-xs text-white/50 mb-1.5 block">Description (optionnel)</label>
              <Input
                placeholder="Brève description du rapport…"
                value={newReport.description}
                onChange={(e) => setNewReport((p) => ({ ...p, description: e.target.value }))}
              />
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setCreateOpen(false)}>
            Annuler
          </Button>
          <Button onClick={handleCreate} disabled={createReport.isPending}>
            <Save className="h-4 w-4 mr-1.5" />
            {createReport.isPending ? 'Sauvegarde...' : 'Sauvegarder'}
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function ReportsPage() {
  const { toast } = useToast();

  // Top-level dashboard stats
  const { data: membersData, isLoading: membersLoading } = useReportsDashboard('members');
  const { data: donationsData, isLoading: donationsLoading } = useReportsDashboard('donations');
  const { data: eventsData, isLoading: eventsLoading } = useReportsDashboard('events');
  const { data: volunteersData, isLoading: volunteersLoading } = useReportsDashboard('volunteers');

  const anyLoading = membersLoading || donationsLoading || eventsLoading || volunteersLoading;

  const topStats = useMemo(() => {
    const m = membersData as Record<string, unknown> | undefined;
    const d = donationsData as Record<string, unknown> | undefined;
    const e = eventsData as Record<string, unknown> | undefined;
    const v = volunteersData as Record<string, unknown> | undefined;

    const totalMembers = Number(m?.total_members ?? 0);
    const monthlyGiving = Number(d?.monthly_total ?? 0);
    const avgAttendance = Number(e?.average_attendance ?? 0);
    const volunteerHours = Number(v?.hours_this_month ?? 0);

    return { totalMembers, monthlyGiving, avgAttendance, volunteerHours };
  }, [membersData, donationsData, eventsData, volunteersData]);

  const formatCAD = (v: number) =>
    new Intl.NumberFormat('fr-CA', { style: 'currency', currency: 'CAD', maximumFractionDigits: 0 }).format(v);

  const handleExport = () => {
    toast({
      type: 'info',
      title: 'Export en cours',
      description: 'Votre rapport sera prêt dans quelques instants.',
    });
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Rapports</h1>
          <p className="text-white/50 text-sm mt-0.5">
            Analyses et statistiques de votre église
          </p>
        </div>
        <Button variant="outline" onClick={handleExport}>
          <Download className="h-4 w-4 mr-2" />
          Exporter
        </Button>
      </div>

      {/* Top stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total membres"
          value={topStats.totalMembers || '—'}
          icon={Users}
          trend={4}
          sub="vs mois dernier"
          loading={anyLoading}
        />
        <StatCard
          label="Dons du mois"
          value={topStats.monthlyGiving ? formatCAD(topStats.monthlyGiving) : '—'}
          icon={DollarSign}
          trend={7}
          sub="vs mois dernier"
          loading={anyLoading}
        />
        <StatCard
          label="Présence moyenne"
          value={topStats.avgAttendance || '—'}
          icon={Calendar}
          trend={-2}
          sub="vs mois dernier"
          loading={anyLoading}
        />
        <StatCard
          label="Heures bénévoles"
          value={topStats.volunteerHours || '—'}
          icon={Clock}
          trend={12}
          sub="ce mois"
          loading={anyLoading}
        />
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <div className="overflow-x-auto">
          <TabsList className="inline-flex min-w-max">
            <TabsTrigger value="overview">
              <BarChart3 className="h-4 w-4 mr-1.5" />
              Vue d'ensemble
            </TabsTrigger>
            <TabsTrigger value="membres">
              <Users className="h-4 w-4 mr-1.5" />
              Membres
            </TabsTrigger>
            <TabsTrigger value="dons">
              <DollarSign className="h-4 w-4 mr-1.5" />
              Dons
            </TabsTrigger>
            <TabsTrigger value="presence">
              <Calendar className="h-4 w-4 mr-1.5" />
              Présence
            </TabsTrigger>
            <TabsTrigger value="benevoles">
              <Heart className="h-4 w-4 mr-1.5" />
              Bénévoles
            </TabsTrigger>
            <TabsTrigger value="saved">
              <Save className="h-4 w-4 mr-1.5" />
              Rapports sauvegardés
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="overview">
          <OverviewTab />
        </TabsContent>

        <TabsContent value="membres">
          <MembresTab />
        </TabsContent>

        <TabsContent value="dons">
          <DonsTab />
        </TabsContent>

        <TabsContent value="presence">
          <PresenceTab />
        </TabsContent>

        <TabsContent value="benevoles">
          <BenevolesTab />
        </TabsContent>

        <TabsContent value="saved">
          <RapportsSauvegardésTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
