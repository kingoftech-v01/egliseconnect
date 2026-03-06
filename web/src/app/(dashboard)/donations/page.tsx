'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Plus,
  Search,
  DollarSign,
  Megaphone,
  FileText,
  HandCoins,
  BarChart3,
  Download,
  Target,
  TrendingUp,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { InfiniteScrollTable } from '@/components/ui/infinite-scroll-table';
import type { Column } from '@/components/ui/data-table';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
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
  useInfiniteDonations,
  useInfiniteDonationCampaigns,
  useCreateDonationCampaign,
  useInfinitePledges,
  useCreatePledge,
  useInfiniteTaxReceipts,
  useGenerateTaxReceipts,
  useDonationAnalytics,
  useTopDonors,
} from '@/hooks/use-donations';
import { DONATION_TYPE_LABELS } from '@egliseconnect/types';
import { formatCurrency, formatDate } from '@egliseconnect/utils';
import type { DonationListItem } from '@egliseconnect/types';

type AnyRecord = Record<string, unknown>;

// ─── Dons Tab ───────────────────────────────────────────────────────────────

function DonsTab() {
  const router = useRouter();
  const [search, setSearch] = useState('');

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteDonations(search);

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as (DonationListItem & AnyRecord)[];
  const totalCount = data?.pages[0]?.count;

  const columns: Column<DonationListItem & AnyRecord>[] = [
    { key: 'donation_number', header: 'No.' },
    {
      key: 'member',
      header: 'Donateur',
      render: (item) =>
        item.is_anonymous
          ? 'Anonyme'
          : (item.member as { full_name: string } | null)?.full_name ?? '—',
    },
    {
      key: 'amount',
      header: 'Montant',
      render: (item) => (
        <span className="font-semibold text-emerald-400">{formatCurrency(item.amount as string)}</span>
      ),
    },
    {
      key: 'donation_type',
      header: 'Type',
      render: (item) => (
        <Badge variant="outline">
          {DONATION_TYPE_LABELS[item.donation_type as keyof typeof DONATION_TYPE_LABELS] || (item.donation_type as string)}
        </Badge>
      ),
    },
    {
      key: 'date',
      header: 'Date',
      render: (item) => formatDate(item.date as string, { year: 'numeric', month: 'short', day: 'numeric' }),
    },
    {
      key: 'campaign',
      header: 'Campagne',
      render: (item) => (item.campaign as { name: string } | null)?.name ?? '—',
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
          <Input
            placeholder="Rechercher un don..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Button onClick={() => router.push('/donations/new')}>
          <Plus className="h-4 w-4 mr-2" />
          Nouveau don
        </Button>
      </div>

      <InfiniteScrollTable
        columns={columns}
        data={items}
        totalCount={totalCount}
        isLoading={isLoading}
        fetchNextPage={fetchNextPage}
        hasNextPage={hasNextPage}
        isFetchingNextPage={isFetchingNextPage}
        error={error}
        emptyMessage="Aucun don trouvé"
        onRowClick={(item) => router.push(`/donations/${item.id}`)}
      />
    </div>
  );
}

// ─── Campaigns Tab ──────────────────────────────────────────────────────────

function CampaignsTab() {
  const { toast } = useToast();
  const [search, setSearch] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({ name: '', description: '', goal_amount: '', end_date: '' });

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteDonationCampaigns(search);
  const createCampaign = useCreateDonationCampaign();

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as AnyRecord[];
  const totalCount = data?.pages[0]?.count;

  const columns: Column<AnyRecord>[] = [
    {
      key: 'name',
      header: 'Campagne',
      render: (item) => (
        <div>
          <p className="font-medium text-white/90">{String(item.name ?? '—')}</p>
          {!!item.description && (
            <p className="text-xs text-white/40 truncate max-w-xs">{String(item.description)}</p>
          )}
        </div>
      ),
    },
    {
      key: 'goal_amount',
      header: 'Objectif',
      render: (item) => (
        <span className="font-medium text-white/70">{formatCurrency(String(item.goal_amount ?? item.target_amount ?? '0'))}</span>
      ),
    },
    {
      key: 'raised_amount',
      header: 'Collecté',
      render: (item) => {
        const raised = Number(item.raised_amount ?? item.current_amount ?? 0);
        const goal = Number(item.goal_amount ?? item.target_amount ?? 0);
        const pct = goal > 0 ? Math.round((raised / goal) * 100) : 0;
        return (
          <div className="flex items-center gap-2">
            <span className="text-emerald-400 font-medium">{formatCurrency(String(raised))}</span>
            <Badge variant={pct >= 100 ? 'success' : 'secondary'}>{pct}%</Badge>
          </div>
        );
      },
    },
    {
      key: 'end_date',
      header: 'Date de fin',
      render: (item) =>
        item.end_date
          ? formatDate(item.end_date as string, { year: 'numeric', month: 'short', day: 'numeric' })
          : '—',
    },
    {
      key: 'is_active',
      header: 'Statut',
      render: (item) => (
        <Badge variant={item.is_active !== false ? 'success' : 'secondary'}>
          {item.is_active !== false ? 'Active' : 'Terminée'}
        </Badge>
      ),
    },
  ];

  function handleCreate() {
    if (!form.name.trim()) {
      toast({ type: 'error', title: 'Nom requis', description: 'Veuillez entrer le nom de la campagne.' });
      return;
    }
    createCampaign.mutate(
      {
        name: form.name,
        description: form.description,
        goal_amount: form.goal_amount ? parseFloat(form.goal_amount) : undefined,
        end_date: form.end_date || undefined,
      },
      {
        onSuccess: () => {
          toast({ type: 'success', title: 'Campagne créée', description: `La campagne "${form.name}" a été créée.` });
          setDialogOpen(false);
          setForm({ name: '', description: '', goal_amount: '', end_date: '' });
        },
        onError: () => {
          toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer la campagne.' });
        },
      },
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
          <Input
            placeholder="Rechercher une campagne..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nouvelle campagne
        </Button>
      </div>

      <InfiniteScrollTable
        columns={columns}
        data={items}
        totalCount={totalCount}
        isLoading={isLoading}
        fetchNextPage={fetchNextPage}
        hasNextPage={hasNextPage}
        isFetchingNextPage={isFetchingNextPage}
        error={error}
        emptyMessage="Aucune campagne trouvée"
      />

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogHeader>
          <DialogTitle>Nouvelle campagne</DialogTitle>
          <DialogDescription>Créer une campagne de collecte de fonds</DialogDescription>
          <DialogClose onClose={() => setDialogOpen(false)} />
        </DialogHeader>
        <DialogContent>
          <div className="space-y-4">
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Nom *</label>
              <Input
                placeholder="ex. Fonds de construction"
                value={form.name}
                onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Description</label>
              <Input
                placeholder="Brève description..."
                value={form.description}
                onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-white/50 mb-1.5">Objectif (CAD)</label>
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="0.00"
                  value={form.goal_amount}
                  onChange={(e) => setForm((p) => ({ ...p, goal_amount: e.target.value }))}
                />
              </div>
              <div>
                <label className="block text-xs text-white/50 mb-1.5">Date de fin</label>
                <Input
                  type="date"
                  value={form.end_date}
                  onChange={(e) => setForm((p) => ({ ...p, end_date: e.target.value }))}
                />
              </div>
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setDialogOpen(false)}>Annuler</Button>
          <Button onClick={handleCreate} disabled={createCampaign.isPending}>
            {createCampaign.isPending ? 'Création...' : 'Créer'}
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Pledges Tab ────────────────────────────────────────────────────────────

function PledgesTab() {
  const { toast } = useToast();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({ amount: '', frequency: 'monthly', start_date: '', end_date: '' });

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfinitePledges();
  const createPledge = useCreatePledge();

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as AnyRecord[];
  const totalCount = data?.pages[0]?.count;

  const freqLabels: Record<string, string> = {
    weekly: 'Hebdomadaire',
    biweekly: 'Bimensuel',
    monthly: 'Mensuel',
    quarterly: 'Trimestriel',
    annually: 'Annuel',
    one_time: 'Unique',
  };

  const columns: Column<AnyRecord>[] = [
    {
      key: 'member',
      header: 'Donateur',
      render: (item) => {
        const member = item.member as { full_name?: string } | null;
        return <span className="font-medium text-white/80">{member?.full_name ?? '—'}</span>;
      },
    },
    {
      key: 'amount',
      header: 'Montant promis',
      render: (item) => (
        <span className="font-semibold text-purple-400">{formatCurrency(String(item.amount ?? item.pledge_amount ?? '0'))}</span>
      ),
    },
    {
      key: 'fulfilled_amount',
      header: 'Rempli',
      render: (item) => {
        const fulfilled = Number(item.fulfilled_amount ?? item.paid_amount ?? 0);
        const total = Number(item.amount ?? item.pledge_amount ?? 0);
        const pct = total > 0 ? Math.round((fulfilled / total) * 100) : 0;
        return (
          <div className="flex items-center gap-2">
            <span className="text-emerald-400">{formatCurrency(String(fulfilled))}</span>
            <Badge variant={pct >= 100 ? 'success' : 'secondary'}>{pct}%</Badge>
          </div>
        );
      },
    },
    {
      key: 'frequency',
      header: 'Fréquence',
      render: (item) => (
        <Badge variant="outline">
          {freqLabels[item.frequency as string] ?? String(item.frequency ?? '—')}
        </Badge>
      ),
    },
    {
      key: 'status',
      header: 'Statut',
      render: (item) => {
        const status = (item.status as string) ?? 'active';
        const map: Record<string, { variant: 'success' | 'warning' | 'secondary' | 'destructive'; label: string }> = {
          active: { variant: 'success', label: 'Actif' },
          completed: { variant: 'success', label: 'Complété' },
          cancelled: { variant: 'destructive', label: 'Annulé' },
          overdue: { variant: 'warning', label: 'En retard' },
        };
        const resolved = map[status] ?? { variant: 'secondary' as const, label: status };
        return <Badge variant={resolved.variant}>{resolved.label}</Badge>;
      },
    },
  ];

  function handleCreate() {
    const amt = parseFloat(form.amount);
    if (!amt || amt <= 0) {
      toast({ type: 'error', title: 'Montant requis', description: 'Veuillez entrer un montant valide.' });
      return;
    }
    createPledge.mutate(
      { amount: amt, frequency: form.frequency, start_date: form.start_date || undefined, end_date: form.end_date || undefined },
      {
        onSuccess: () => {
          toast({ type: 'success', title: 'Promesse créée', description: 'La promesse de don a été enregistrée.' });
          setDialogOpen(false);
          setForm({ amount: '', frequency: 'monthly', start_date: '', end_date: '' });
        },
        onError: () => {
          toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer la promesse.' });
        },
      },
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nouvelle promesse
        </Button>
      </div>

      <InfiniteScrollTable
        columns={columns}
        data={items}
        totalCount={totalCount}
        isLoading={isLoading}
        fetchNextPage={fetchNextPage}
        hasNextPage={hasNextPage}
        isFetchingNextPage={isFetchingNextPage}
        error={error}
        emptyMessage="Aucune promesse de don trouvée"
      />

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogHeader>
          <DialogTitle>Nouvelle promesse de don</DialogTitle>
          <DialogDescription>Enregistrer un engagement de don</DialogDescription>
          <DialogClose onClose={() => setDialogOpen(false)} />
        </DialogHeader>
        <DialogContent>
          <div className="space-y-4">
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Montant (CAD) *</label>
              <Input
                type="number"
                min="1"
                step="0.01"
                placeholder="0.00"
                value={form.amount}
                onChange={(e) => setForm((p) => ({ ...p, amount: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Fréquence</label>
              <Select
                value={form.frequency}
                onChange={(e) => setForm((p) => ({ ...p, frequency: e.target.value }))}
              >
                {Object.entries(freqLabels).map(([v, l]) => (
                  <option key={v} value={v}>{l}</option>
                ))}
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-white/50 mb-1.5">Date de début</label>
                <Input
                  type="date"
                  value={form.start_date}
                  onChange={(e) => setForm((p) => ({ ...p, start_date: e.target.value }))}
                />
              </div>
              <div>
                <label className="block text-xs text-white/50 mb-1.5">Date de fin</label>
                <Input
                  type="date"
                  value={form.end_date}
                  onChange={(e) => setForm((p) => ({ ...p, end_date: e.target.value }))}
                />
              </div>
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setDialogOpen(false)}>Annuler</Button>
          <Button onClick={handleCreate} disabled={createPledge.isPending}>
            {createPledge.isPending ? 'Création...' : 'Créer'}
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Receipts Tab ───────────────────────────────────────────────────────────

function ReceiptsTab() {
  const { toast } = useToast();
  const [genOpen, setGenOpen] = useState(false);
  const [genYear, setGenYear] = useState(String(new Date().getFullYear()));
  const currentYear = new Date().getFullYear();

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteTaxReceipts();
  const generateReceipts = useGenerateTaxReceipts();

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as AnyRecord[];
  const totalCount = data?.pages[0]?.count;

  const columns: Column<AnyRecord>[] = [
    {
      key: 'receipt_number',
      header: 'No. reçu',
      render: (item) => <span className="font-medium text-white/80">{String(item.receipt_number ?? item.id ?? '—')}</span>,
    },
    {
      key: 'member',
      header: 'Donateur',
      render: (item) => {
        const member = item.member as { full_name?: string } | null;
        return member?.full_name ?? '—';
      },
    },
    {
      key: 'year',
      header: 'Année',
      render: (item) => String(item.year ?? item.tax_year ?? '—'),
    },
    {
      key: 'total_amount',
      header: 'Total',
      render: (item) => (
        <span className="font-semibold text-emerald-400">{formatCurrency(String(item.total_amount ?? '0'))}</span>
      ),
    },
    {
      key: 'download',
      header: '',
      render: () => (
        <Button variant="secondary" size="sm">
          <Download className="h-3.5 w-3.5 mr-1" />
          PDF
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setGenOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Générer les reçus
        </Button>
      </div>

      <InfiniteScrollTable
        columns={columns}
        data={items}
        totalCount={totalCount}
        isLoading={isLoading}
        fetchNextPage={fetchNextPage}
        hasNextPage={hasNextPage}
        isFetchingNextPage={isFetchingNextPage}
        error={error}
        emptyMessage="Aucun reçu fiscal trouvé"
      />

      <Dialog open={genOpen} onClose={() => setGenOpen(false)}>
        <DialogHeader>
          <DialogTitle>Générer les reçus fiscaux</DialogTitle>
          <DialogDescription>Créer les reçus annuels pour tous les donateurs</DialogDescription>
          <DialogClose onClose={() => setGenOpen(false)} />
        </DialogHeader>
        <DialogContent>
          <div>
            <label className="block text-xs text-white/50 mb-1.5">Année fiscale</label>
            <Select value={genYear} onChange={(e) => setGenYear(e.target.value)}>
              {Array.from({ length: 5 }, (_, i) => currentYear - i).map((y) => (
                <option key={y} value={String(y)}>{y}</option>
              ))}
            </Select>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setGenOpen(false)}>Annuler</Button>
          <Button
            onClick={() => {
              generateReceipts.mutate(
                { year: parseInt(genYear) },
                {
                  onSuccess: () => {
                    toast({ type: 'success', title: 'Reçus générés', description: `Les reçus ${genYear} ont été générés.` });
                    setGenOpen(false);
                  },
                  onError: () => {
                    toast({ type: 'error', title: 'Erreur', description: 'Impossible de générer les reçus.' });
                  },
                },
              );
            }}
            disabled={generateReceipts.isPending}
          >
            {generateReceipts.isPending ? 'Génération...' : 'Générer'}
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Analytics Tab ──────────────────────────────────────────────────────────

function AnalyticsTab() {
  const { data: dashData, isLoading: dashLoading } = useDonationAnalytics();
  const { data: topData, isLoading: topLoading } = useTopDonors();

  const dash = dashData as AnyRecord | undefined;
  const topDonors = Array.isArray(topData) ? topData as AnyRecord[] : (topData as AnyRecord | undefined)?.results as AnyRecord[] ?? [];

  const stats = {
    total: Number(dash?.total_amount ?? 0),
    count: Number(dash?.total_donations ?? 0),
    average: Number(dash?.average_donation ?? 0),
    donors: Number(dash?.unique_donors ?? 0),
  };

  const fmt = (v: number) =>
    new Intl.NumberFormat('fr-CA', { style: 'currency', currency: 'CAD' }).format(v);

  if (dashLoading) {
    return (
      <div className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white/[0.05] rounded-2xl border border-white/[0.08] p-5 animate-pulse">
              <div className="h-3 bg-white/[0.06] rounded w-1/2 mb-3" />
              <div className="h-6 bg-white/[0.06] rounded w-2/3" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: 'Total des dons', value: fmt(stats.total), icon: DollarSign, color: 'text-emerald-400' },
          { label: 'Nombre de dons', value: String(stats.count), icon: BarChart3, color: 'text-blue-400' },
          { label: 'Don moyen', value: fmt(stats.average), icon: TrendingUp, color: 'text-purple-400' },
          { label: 'Donateurs uniques', value: String(stats.donors), icon: Target, color: 'text-amber-400' },
        ].map((s) => (
          <div key={s.label} className="bg-white/[0.05] backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs text-white/40">{s.label}</p>
              <s.icon className={`h-4 w-4 ${s.color}`} />
            </div>
            <p className="text-2xl font-bold text-white">{s.value}</p>
          </div>
        ))}
      </div>

      <div className="bg-white/[0.05] backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5">
        <h3 className="text-sm font-medium text-white/70 mb-4">Meilleurs donateurs</h3>
        {topLoading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-10 bg-white/[0.04] rounded-lg animate-pulse" />
            ))}
          </div>
        ) : topDonors.length === 0 ? (
          <p className="text-sm text-white/30 text-center py-6">Aucune donnée disponible</p>
        ) : (
          <div className="space-y-2">
            {topDonors.slice(0, 10).map((d, i) => {
              const name = (d.member as { full_name?: string })?.full_name ?? String(d.donor_name ?? d.name ?? 'Anonyme');
              const total = Number(d.total_amount ?? d.amount ?? 0);
              return (
                <div
                  key={i}
                  className="flex items-center gap-3 p-2.5 rounded-xl bg-white/[0.03] border border-white/[0.04]"
                >
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                    i === 0 ? 'bg-amber-500/20 text-amber-400'
                    : i === 1 ? 'bg-slate-400/20 text-slate-400'
                    : i === 2 ? 'bg-orange-700/20 text-orange-600'
                    : 'bg-white/[0.06] text-white/40'
                  }`}>
                    {i + 1}
                  </div>
                  <span className="flex-1 text-sm text-white/80 truncate">{name}</span>
                  <span className="text-sm font-semibold text-emerald-400">{fmt(total)}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Main Page ──────────────────────────────────────────────────────────────

export default function DonationsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white/90">Dons</h1>
        <p className="text-white/40 text-sm mt-0.5">
          Suivi des dons, campagnes, promesses et reçus fiscaux
        </p>
      </div>

      <Tabs defaultValue="dons">
        <TabsList className="flex-wrap gap-1 h-auto">
          <TabsTrigger value="dons">
            <DollarSign className="h-3.5 w-3.5 mr-1.5 inline" />
            Dons
          </TabsTrigger>
          <TabsTrigger value="campagnes">
            <Megaphone className="h-3.5 w-3.5 mr-1.5 inline" />
            Campagnes
          </TabsTrigger>
          <TabsTrigger value="promesses">
            <HandCoins className="h-3.5 w-3.5 mr-1.5 inline" />
            Promesses
          </TabsTrigger>
          <TabsTrigger value="recus">
            <FileText className="h-3.5 w-3.5 mr-1.5 inline" />
            Reçus fiscaux
          </TabsTrigger>
          <TabsTrigger value="analytique">
            <BarChart3 className="h-3.5 w-3.5 mr-1.5 inline" />
            Analytique
          </TabsTrigger>
        </TabsList>

        <TabsContent value="dons"><DonsTab /></TabsContent>
        <TabsContent value="campagnes"><CampaignsTab /></TabsContent>
        <TabsContent value="promesses"><PledgesTab /></TabsContent>
        <TabsContent value="recus"><ReceiptsTab /></TabsContent>
        <TabsContent value="analytique"><AnalyticsTab /></TabsContent>
      </Tabs>
    </div>
  );
}
