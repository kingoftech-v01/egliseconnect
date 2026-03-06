'use client';

import { useState } from 'react';
import {
  CreditCard,
  Repeat,
  FileText,
  Target,
  ClipboardList,
  Megaphone,
  Plus,
  Search,
  DollarSign,
  Download,
  X,
  TrendingUp,
  AlertCircle,
  Building2,
  MessageSquare,
  Mail,
  CheckCircle,
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
  usePayments,
  useCreatePaymentIntent,
  useRecurringDonations,
  useCancelRecurring,
  useGivingGoals,
  useCreateGivingGoal,
  useGivingCampaigns,
  useInfinitePayments,
  useInfiniteRecurringDonations,
  useInfiniteGivingStatements,
  useInfinitePaymentPlans,
  useGenerateStatement,
  useCreatePaymentPlan,
  useInfiniteEmployerMatches,
  useCreateEmployerMatch,
  useInfiniteSMSDonations,
  useRefundPayment,
  useSendStatementEmail,
  useCompletePlanEarly,
} from '@/hooks/use-payments';
import { formatCurrency, formatDate } from '@egliseconnect/utils';

// ─── Type helpers ─────────────────────────────────────────────────────────────

type AnyRecord = Record<string, unknown>;

// ─── Status badge helper ──────────────────────────────────────────────────────

function PaymentStatusBadge({ status }: { status: string }) {
  const map: Record<string, { variant: 'success' | 'warning' | 'destructive' | 'secondary'; label: string }> = {
    succeeded: { variant: 'success', label: 'Réussi' },
    paid: { variant: 'success', label: 'Payé' },
    pending: { variant: 'warning', label: 'En attente' },
    processing: { variant: 'warning', label: 'Traitement' },
    failed: { variant: 'destructive', label: 'Échoué' },
    canceled: { variant: 'destructive', label: 'Annulé' },
    active: { variant: 'success', label: 'Actif' },
    paused: { variant: 'warning', label: 'Suspendu' },
    cancelled: { variant: 'destructive', label: 'Annulé' },
  };
  const resolved = map[status] ?? { variant: 'secondary' as const, label: status };
  return <Badge variant={resolved.variant}>{resolved.label}</Badge>;
}

// ─── Progress bar ─────────────────────────────────────────────────────────────

function ProgressBar({ pct }: { pct: number }) {
  const clamped = Math.min(100, Math.max(0, pct));
  return (
    <div className="w-full h-2 rounded-full bg-white/[0.06] overflow-hidden">
      <div
        className="h-full rounded-full bg-gradient-to-r from-purple-600 to-purple-400 transition-all duration-500"
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}

// ─── Stat card ────────────────────────────────────────────────────────────────

function StatCard({
  icon: Icon,
  label,
  value,
  sub,
  iconColor,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  sub?: string;
  iconColor: string;
}) {
  return (
    <div className="bg-white/[0.05] backdrop-blur-xl border border-white/[0.08] rounded-2xl shadow-[0_8px_32px_rgba(0,0,0,0.2)] p-5 flex items-center gap-4">
      <div className={`p-3 rounded-xl bg-white/[0.06] ${iconColor}`}>
        <Icon className="h-5 w-5" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-white/40 uppercase tracking-wider truncate">{label}</p>
        <p className="text-xl font-bold text-white/90 mt-0.5">{value}</p>
        {sub && <p className="text-xs text-white/40 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

// ─── Payments tab ─────────────────────────────────────────────────────────────

function PaymentsTab() {
  const { toast } = useToast();
  const [search, setSearch] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState('cad');

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfinitePayments(search);
  const createIntent = useCreatePaymentIntent();

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as AnyRecord[];
  const totalCount = data?.pages[0]?.count;

  const columns: Column<AnyRecord>[] = [
    {
      key: 'created',
      header: 'Date',
      render: (item) =>
        item.created
          ? formatDate(item.created as string, { year: 'numeric', month: 'short', day: 'numeric' })
          : '—',
    },
    {
      key: 'donor',
      header: 'Donateur',
      render: (item) => {
        const member = item.member as { full_name?: string } | null;
        const name = item.donor_name as string | undefined;
        return (
          <span className="text-white/80 font-medium">
            {member?.full_name ?? name ?? (item.metadata as { donor?: string } | null)?.donor ?? 'Anonyme'}
          </span>
        );
      },
    },
    {
      key: 'amount',
      header: 'Montant',
      render: (item) => (
        <span className="font-semibold text-emerald-400">
          {formatCurrency(String((Number(item.amount ?? 0) / 100).toFixed(2)))}
        </span>
      ),
    },
    {
      key: 'payment_method_type',
      header: 'Méthode',
      render: (item) => {
        const method = (item.payment_method_type as string) ?? (item.method as string) ?? 'card';
        const labels: Record<string, string> = {
          card: 'Carte',
          bank_transfer: 'Virement',
          cash: 'Comptant',
          check: 'Chèque',
          interac: 'Interac',
        };
        return <Badge variant="secondary">{labels[method] ?? method}</Badge>;
      },
    },
    {
      key: 'status',
      header: 'Statut',
      render: (item) => <PaymentStatusBadge status={(item.status as string) ?? 'pending'} />,
    },
  ];

  function handleCreateIntent() {
    const parsed = parseFloat(amount);
    if (!parsed || parsed <= 0) {
      toast({ type: 'error', title: 'Montant invalide', description: 'Veuillez entrer un montant valide.' });
      return;
    }
    createIntent.mutate(
      { amount: Math.round(parsed * 100), currency },
      {
        onSuccess: () => {
          toast({ type: 'success', title: 'Intention créée', description: 'L\'intention de paiement a été créée.' });
          setDialogOpen(false);
          setAmount('');
        },
        onError: () => {
          toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer l\'intention de paiement.' });
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
            placeholder="Rechercher un paiement..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nouveau paiement
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
        emptyMessage="Aucun paiement trouvé"
      />

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogHeader>
          <DialogTitle>Nouveau paiement</DialogTitle>
          <DialogDescription>Créer une intention de paiement Stripe</DialogDescription>
          <DialogClose onClose={() => setDialogOpen(false)} />
        </DialogHeader>
        <DialogContent>
          <div className="space-y-4">
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Montant</label>
              <div className="flex gap-2">
                <Input
                  type="number"
                  min="1"
                  step="0.01"
                  placeholder="0.00"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="flex-1"
                />
                <Select value={currency} onChange={(e) => setCurrency(e.target.value)} className="w-24">
                  <option value="cad">CAD</option>
                  <option value="usd">USD</option>
                </Select>
              </div>
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setDialogOpen(false)}>Annuler</Button>
          <Button onClick={handleCreateIntent} disabled={createIntent.isPending}>
            {createIntent.isPending ? 'Création...' : 'Créer'}
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Recurring tab ────────────────────────────────────────────────────────────

function RecurringTab() {
  const { toast } = useToast();
  const [cancelId, setCancelId] = useState<string | null>(null);

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteRecurringDonations();
  const cancelRecurring = useCancelRecurring();

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as AnyRecord[];
  const totalCount = data?.pages[0]?.count;

  const frequencyLabels: Record<string, string> = {
    weekly: 'Hebdomadaire',
    biweekly: 'Bimensuel',
    monthly: 'Mensuel',
    quarterly: 'Trimestriel',
    annually: 'Annuel',
  };

  const columns: Column<AnyRecord>[] = [
    {
      key: 'donor',
      header: 'Donateur',
      render: (item) => {
        const member = item.member as { full_name?: string } | null;
        return <span className="font-medium text-white/80">{member?.full_name ?? '—'}</span>;
      },
    },
    {
      key: 'amount',
      header: 'Montant',
      render: (item) => (
        <span className="font-semibold text-emerald-400">
          {formatCurrency(String(item.amount ?? '0'))}
        </span>
      ),
    },
    {
      key: 'frequency',
      header: 'Fréquence',
      render: (item) => (
        <Badge variant="secondary">
          {frequencyLabels[item.frequency as string] ?? (item.frequency as string) ?? '—'}
        </Badge>
      ),
    },
    {
      key: 'next_payment_date',
      header: 'Prochain paiement',
      render: (item) =>
        item.next_payment_date
          ? formatDate(item.next_payment_date as string, { year: 'numeric', month: 'short', day: 'numeric' })
          : '—',
    },
    {
      key: 'status',
      header: 'Statut',
      render: (item) => <PaymentStatusBadge status={(item.status as string) ?? 'active'} />,
    },
    {
      key: 'actions',
      header: '',
      render: (item) =>
        (item.status as string) === 'active' ? (
          <Button
            variant="destructive"
            size="sm"
            onClick={(e) => { e.stopPropagation(); setCancelId(item.id as string); }}
          >
            <X className="h-3.5 w-3.5 mr-1" />
            Annuler
          </Button>
        ) : null,
    },
  ];

  function handleCancel() {
    if (!cancelId) return;
    cancelRecurring.mutate(cancelId, {
      onSuccess: () => {
        toast({ type: 'success', title: 'Don récurrent annulé', description: 'Le don récurrent a été annulé avec succès.' });
        setCancelId(null);
      },
      onError: () => {
        toast({ type: 'error', title: 'Erreur', description: 'Impossible d\'annuler le don récurrent.' });
      },
    });
  }

  return (
    <div className="space-y-4">
      <InfiniteScrollTable
        columns={columns}
        data={items}
        totalCount={totalCount}
        isLoading={isLoading}
        fetchNextPage={fetchNextPage}
        hasNextPage={hasNextPage}
        isFetchingNextPage={isFetchingNextPage}
        error={error}
        emptyMessage="Aucun don récurrent trouvé"
      />

      <Dialog open={!!cancelId} onClose={() => setCancelId(null)}>
        <DialogHeader>
          <DialogTitle>Confirmer l&apos;annulation</DialogTitle>
          <DialogDescription>Cette action est irréversible. Le donateur ne sera plus prélevé.</DialogDescription>
          <DialogClose onClose={() => setCancelId(null)} />
        </DialogHeader>
        <DialogContent>
          <div className="flex items-start gap-3 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20">
            <AlertCircle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
            <p className="text-sm text-white/70">
              Êtes-vous certain de vouloir annuler ce don récurrent ? Cette action ne peut pas être annulée.
            </p>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setCancelId(null)}>Retour</Button>
          <Button variant="destructive" onClick={handleCancel} disabled={cancelRecurring.isPending}>
            {cancelRecurring.isPending ? 'Annulation...' : 'Confirmer l\'annulation'}
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Statements tab ───────────────────────────────────────────────────────────

function StatementsTab() {
  const { toast } = useToast();
  const [search, setSearch] = useState('');
  const [genOpen, setGenOpen] = useState(false);
  const [genYear, setGenYear] = useState(String(new Date().getFullYear()));

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteGivingStatements(search);
  const generateStatement = useGenerateStatement();

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as AnyRecord[];
  const totalCount = data?.pages[0]?.count;

  const currentYear = new Date().getFullYear();

  const columns: Column<AnyRecord>[] = [
    {
      key: 'period',
      header: 'Période',
      render: (item) => {
        const year = item.year ?? item.period;
        return <span className="font-medium text-white/80">{String(year ?? '—')}</span>;
      },
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
      key: 'total_amount',
      header: 'Total',
      render: (item) => (
        <span className="font-semibold text-emerald-400">
          {formatCurrency(String(item.total_amount ?? item.total ?? '0'))}
        </span>
      ),
    },
    {
      key: 'download',
      header: '',
      render: (item) => (
        <Button
          variant="secondary"
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            toast({ type: 'info', title: 'Téléchargement', description: `Relevé ${item.year ?? item.period} en préparation...` });
          }}
        >
          <Download className="h-3.5 w-3.5 mr-1" />
          Télécharger
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
          <Input
            placeholder="Rechercher un donateur..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Button onClick={() => setGenOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Générer un relevé
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
        emptyMessage="Aucun relevé trouvé"
      />

      <Dialog open={genOpen} onClose={() => setGenOpen(false)}>
        <DialogHeader>
          <DialogTitle>Générer un relevé fiscal</DialogTitle>
          <DialogDescription>Générer les relevés annuels pour tous les donateurs</DialogDescription>
          <DialogClose onClose={() => setGenOpen(false)} />
        </DialogHeader>
        <DialogContent>
          <div className="space-y-4">
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Année fiscale</label>
              <Select value={genYear} onChange={(e) => setGenYear(e.target.value)}>
                {Array.from({ length: 5 }, (_, i) => currentYear - i).map((y) => (
                  <option key={y} value={String(y)}>{y}</option>
                ))}
              </Select>
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setGenOpen(false)}>Annuler</Button>
          <Button
            onClick={() => {
              generateStatement.mutate(
                { year: parseInt(genYear) },
                {
                  onSuccess: () => {
                    toast({ type: 'success', title: 'Relevés générés', description: `Les relevés ${genYear} ont été générés.` });
                    setGenOpen(false);
                  },
                  onError: () => {
                    toast({ type: 'error', title: 'Erreur', description: 'Impossible de générer les relevés.' });
                  },
                },
              );
            }}
            disabled={generateStatement.isPending}
          >
            {generateStatement.isPending ? 'Génération...' : 'Générer'}
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Goals tab ────────────────────────────────────────────────────────────────

function GoalsTab() {
  const { toast } = useToast();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [goalName, setGoalName] = useState('');
  const [targetAmount, setTargetAmount] = useState('');
  const [goalYear, setGoalYear] = useState(String(new Date().getFullYear()));

  const { data, isLoading } = useGivingGoals();
  const createGoal = useCreateGivingGoal();

  const currentYear = new Date().getFullYear();
  const goals = (data?.results ?? []) as AnyRecord[];

  function handleCreate() {
    if (!goalName.trim()) {
      toast({ type: 'error', title: 'Nom requis', description: 'Veuillez entrer un nom pour l\'objectif.' });
      return;
    }
    const target = parseFloat(targetAmount);
    if (!target || target <= 0) {
      toast({ type: 'error', title: 'Montant invalide', description: 'Veuillez entrer un montant cible valide.' });
      return;
    }
    createGoal.mutate(
      { name: goalName, target_amount: target, year: parseInt(goalYear) },
      {
        onSuccess: () => {
          toast({ type: 'success', title: 'Objectif créé', description: `L'objectif "${goalName}" a été créé.` });
          setDialogOpen(false);
          setGoalName('');
          setTargetAmount('');
        },
        onError: () => {
          toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer l\'objectif.' });
        },
      },
    );
  }

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white/[0.05] rounded-2xl border border-white/[0.08] p-5 animate-pulse">
            <div className="h-4 bg-white/[0.06] rounded w-2/3 mb-3" />
            <div className="h-8 bg-white/[0.06] rounded w-1/3 mb-4" />
            <div className="h-2 bg-white/[0.06] rounded-full" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nouvel objectif
        </Button>
      </div>

      {goals.length === 0 ? (
        <div className="rounded-2xl bg-white/[0.05] backdrop-blur-xl border border-white/[0.08] p-12 text-center">
          <Target className="h-10 w-10 text-white/20 mx-auto mb-3" />
          <p className="text-white/40">Aucun objectif de collecte défini</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {goals.map((goal, idx) => {
            const target = Number(goal.target_amount ?? 0);
            const current = Number(goal.current_amount ?? goal.raised_amount ?? 0);
            const pct = target > 0 ? Math.round((current / target) * 100) : 0;
            return (
              <div
                key={(goal.id as string) ?? idx}
                className="bg-white/[0.05] backdrop-blur-xl border border-white/[0.08] rounded-2xl shadow-[0_8px_32px_rgba(0,0,0,0.2)] p-5 space-y-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-semibold text-white/90">{String(goal.name ?? 'Objectif')}</p>
                    <p className="text-xs text-white/40 mt-0.5">Année {String(goal.year ?? currentYear)}</p>
                  </div>
                  <Badge variant={pct >= 100 ? 'success' : 'secondary'}>{pct}%</Badge>
                </div>
                <ProgressBar pct={pct} />
                <div className="flex items-center justify-between text-sm">
                  <span className="text-emerald-400 font-medium">{formatCurrency(String(current))}</span>
                  <span className="text-white/40">/ {formatCurrency(String(target))}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogHeader>
          <DialogTitle>Nouvel objectif de collecte</DialogTitle>
          <DialogDescription>Définir un objectif annuel pour la collecte de fonds</DialogDescription>
          <DialogClose onClose={() => setDialogOpen(false)} />
        </DialogHeader>
        <DialogContent>
          <div className="space-y-4">
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Nom de l&apos;objectif</label>
              <Input
                placeholder="ex. Fonds de construction"
                value={goalName}
                onChange={(e) => setGoalName(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Montant cible (CAD)</label>
              <Input
                type="number"
                min="1"
                step="0.01"
                placeholder="0.00"
                value={targetAmount}
                onChange={(e) => setTargetAmount(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Année</label>
              <Select value={goalYear} onChange={(e) => setGoalYear(e.target.value)}>
                {Array.from({ length: 5 }, (_, i) => currentYear + i).map((y) => (
                  <option key={y} value={String(y)}>{y}</option>
                ))}
              </Select>
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setDialogOpen(false)}>Annuler</Button>
          <Button onClick={handleCreate} disabled={createGoal.isPending}>
            {createGoal.isPending ? 'Création...' : 'Créer l\'objectif'}
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Plans tab ────────────────────────────────────────────────────────────────

function PlansTab() {
  const { toast } = useToast();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [planDonor, setPlanDonor] = useState('');
  const [planTotal, setPlanTotal] = useState('');
  const [planFrequency, setPlanFrequency] = useState('monthly');

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfinitePaymentPlans();
  const createPlan = useCreatePaymentPlan();

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as AnyRecord[];
  const totalCount = data?.pages[0]?.count;

  const frequencyLabels: Record<string, string> = {
    weekly: 'Hebdomadaire',
    biweekly: 'Bimensuel',
    monthly: 'Mensuel',
    quarterly: 'Trimestriel',
    annually: 'Annuel',
  };

  const columns: Column<AnyRecord>[] = [
    {
      key: 'member',
      header: 'Donateur',
      render: (item) => {
        const member = item.member as { full_name?: string } | null;
        return <span className="font-medium text-white/80">{member?.full_name ?? (item.donor_name as string) ?? '—'}</span>;
      },
    },
    {
      key: 'total_amount',
      header: 'Total',
      render: (item) => (
        <span className="font-semibold text-white/80">{formatCurrency(String(item.total_amount ?? '0'))}</span>
      ),
    },
    {
      key: 'paid_amount',
      header: 'Payé',
      render: (item) => (
        <span className="text-emerald-400">{formatCurrency(String(item.paid_amount ?? '0'))}</span>
      ),
    },
    {
      key: 'remaining_amount',
      header: 'Restant',
      render: (item) => {
        const total = Number(item.total_amount ?? 0);
        const paid = Number(item.paid_amount ?? 0);
        const remaining = item.remaining_amount != null ? Number(item.remaining_amount) : total - paid;
        return <span className="text-amber-400">{formatCurrency(String(remaining))}</span>;
      },
    },
    {
      key: 'frequency',
      header: 'Fréquence',
      render: (item) => (
        <Badge variant="secondary">
          {frequencyLabels[item.frequency as string] ?? (item.frequency as string) ?? '—'}
        </Badge>
      ),
    },
    {
      key: 'next_payment_date',
      header: 'Prochain paiement',
      render: (item) =>
        item.next_payment_date
          ? formatDate(item.next_payment_date as string, { year: 'numeric', month: 'short', day: 'numeric' })
          : '—',
    },
    {
      key: 'status',
      header: 'Statut',
      render: (item) => <PaymentStatusBadge status={(item.status as string) ?? 'active'} />,
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nouveau plan
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
        emptyMessage="Aucun plan de paiement trouvé"
      />

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogHeader>
          <DialogTitle>Nouveau plan de paiement</DialogTitle>
          <DialogDescription>Configurer un plan de versements échelonnés</DialogDescription>
          <DialogClose onClose={() => setDialogOpen(false)} />
        </DialogHeader>
        <DialogContent>
          <div className="space-y-4">
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Nom du donateur</label>
              <Input
                placeholder="Nom complet"
                value={planDonor}
                onChange={(e) => setPlanDonor(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Montant total (CAD)</label>
              <Input
                type="number"
                min="1"
                step="0.01"
                placeholder="0.00"
                value={planTotal}
                onChange={(e) => setPlanTotal(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Fréquence</label>
              <Select value={planFrequency} onChange={(e) => setPlanFrequency(e.target.value)}>
                {Object.entries(frequencyLabels).map(([v, l]) => (
                  <option key={v} value={v}>{l}</option>
                ))}
              </Select>
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setDialogOpen(false)}>Annuler</Button>
          <Button
            onClick={() => {
              if (!planDonor.trim() || !parseFloat(planTotal)) {
                toast({ type: 'error', title: 'Champs requis', description: 'Veuillez remplir tous les champs.' });
                return;
              }
              createPlan.mutate(
                { donor_name: planDonor, total_amount: parseFloat(planTotal), frequency: planFrequency },
                {
                  onSuccess: () => {
                    toast({ type: 'success', title: 'Plan créé', description: `Plan de paiement pour ${planDonor} créé.` });
                    setDialogOpen(false);
                    setPlanDonor('');
                    setPlanTotal('');
                  },
                  onError: () => {
                    toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer le plan de paiement.' });
                  },
                },
              );
            }}
            disabled={createPlan.isPending}
          >
            {createPlan.isPending ? 'Création...' : 'Créer le plan'}
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Campaigns tab ────────────────────────────────────────────────────────────

function CampaignsTab() {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const { data, isLoading } = useGivingCampaigns();
  const campaigns = (data?.results ?? []) as AnyRecord[];

  const currentYear = new Date().getFullYear();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white/[0.05] rounded-2xl border border-white/[0.08] p-5 animate-pulse">
            <div className="h-4 bg-white/[0.06] rounded w-3/4 mb-2" />
            <div className="h-3 bg-white/[0.06] rounded w-1/2 mb-4" />
            <div className="h-2 bg-white/[0.06] rounded-full mb-3" />
            <div className="flex justify-between">
              <div className="h-3 bg-white/[0.06] rounded w-1/4" />
              <div className="h-3 bg-white/[0.06] rounded w-1/4" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (campaigns.length === 0) {
    return (
      <div className="rounded-2xl bg-white/[0.05] backdrop-blur-xl border border-white/[0.08] p-12 text-center">
        <Megaphone className="h-10 w-10 text-white/20 mx-auto mb-3" />
        <p className="text-white/40">Aucune campagne de financement active</p>
      </div>
    );
  }

  const selected = selectedId ? campaigns.find((c) => (c.id as string) === selectedId) ?? null : null;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {campaigns.map((campaign, idx) => {
          const goal = Number(campaign.goal_amount ?? campaign.target_amount ?? 0);
          const raised = Number(campaign.raised_amount ?? campaign.current_amount ?? 0);
          const pct = goal > 0 ? Math.round((raised / goal) * 100) : 0;
          const endYear = campaign.end_date
            ? new Date(campaign.end_date as string).getFullYear()
            : campaign.year
              ? Number(campaign.year)
              : null;
          const isYearEnd = endYear === currentYear;

          return (
            <button
              key={(campaign.id as string) ?? idx}
              onClick={() => setSelectedId(campaign.id as string)}
              className="bg-white/[0.05] backdrop-blur-xl border border-white/[0.08] rounded-2xl shadow-[0_8px_32px_rgba(0,0,0,0.2)] p-5 space-y-3 text-left hover:bg-white/[0.08] hover:border-purple-500/30 transition-all duration-200 group"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-white/90 group-hover:text-white truncate">
                    {String(campaign.name ?? 'Campagne')}
                  </p>
                  {!!campaign.description && (
                    <p className="text-xs text-white/40 mt-0.5 line-clamp-2">
                      {String(campaign.description)}
                    </p>
                  )}
                </div>
                <div className="flex flex-col items-end gap-1 shrink-0">
                  {isYearEnd && (
                    <Badge variant="warning" className="text-[10px] px-1.5 py-0">Fin d&apos;année</Badge>
                  )}
                  <Badge variant={pct >= 100 ? 'success' : 'default'}>{pct}%</Badge>
                </div>
              </div>

              <ProgressBar pct={pct} />

              <div className="flex items-center justify-between text-sm">
                <div>
                  <p className="text-emerald-400 font-semibold">{formatCurrency(String(raised))}</p>
                  <p className="text-xs text-white/40">collectés</p>
                </div>
                <div className="text-right">
                  <p className="text-white/60 font-medium">{formatCurrency(String(goal))}</p>
                  <p className="text-xs text-white/40">objectif</p>
                </div>
              </div>

              {!!campaign.end_date && (
                <p className="text-xs text-white/30">
                  Fin le {formatDate(campaign.end_date as string, { year: 'numeric', month: 'long', day: 'numeric' })}
                </p>
              )}
            </button>
          );
        })}
      </div>

      {/* Campaign detail dialog */}
      <Dialog open={!!selected} onClose={() => setSelectedId(null)} className="max-w-xl">
        {selected && (() => {
          const goal = Number(selected.goal_amount ?? selected.target_amount ?? 0);
          const raised = Number(selected.raised_amount ?? selected.current_amount ?? 0);
          const pct = goal > 0 ? Math.round((raised / goal) * 100) : 0;
          return (
            <>
              <DialogHeader>
                <DialogTitle>{String(selected.name ?? 'Campagne')}</DialogTitle>
                {!!selected.description && (
                  <DialogDescription>{String(selected.description)}</DialogDescription>
                )}
                <DialogClose onClose={() => setSelectedId(null)} />
              </DialogHeader>
              <DialogContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-white/[0.04] rounded-xl p-3 border border-white/[0.06]">
                      <p className="text-xs text-white/40 mb-1">Montant collecté</p>
                      <p className="text-lg font-bold text-emerald-400">{formatCurrency(String(raised))}</p>
                    </div>
                    <div className="bg-white/[0.04] rounded-xl p-3 border border-white/[0.06]">
                      <p className="text-xs text-white/40 mb-1">Objectif</p>
                      <p className="text-lg font-bold text-white/80">{formatCurrency(String(goal))}</p>
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className="text-white/50">Progression</span>
                      <span className="font-semibold text-purple-400">{pct}%</span>
                    </div>
                    <ProgressBar pct={pct} />
                  </div>

                  {!!selected.end_date && (
                    <div className="flex items-center gap-2 text-sm text-white/50">
                      <span>Date de fin :</span>
                      <span className="text-white/70">
                        {formatDate(selected.end_date as string, { year: 'numeric', month: 'long', day: 'numeric' })}
                      </span>
                    </div>
                  )}
                </div>
              </DialogContent>
              <DialogFooter>
                <Button variant="ghost" onClick={() => setSelectedId(null)}>Fermer</Button>
              </DialogFooter>
            </>
          );
        })()}
      </Dialog>
    </div>
  );
}

// ─── Employer Matches tab ─────────────────────────────────────────────────────

function EmployerMatchesTab() {
  const { toast } = useToast();
  const [showCreate, setShowCreate] = useState(false);
  const createMatch = useCreateEmployerMatch();
  const [form, setForm] = useState({ employer_name: '', match_percentage: '100', max_amount: '' });

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteEmployerMatches();

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as AnyRecord[];
  const totalCount = data?.pages[0]?.count;

  const columns: Column<AnyRecord>[] = [
    {
      key: 'employer_name',
      header: 'Employeur',
      render: (item) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-blue-500/10">
            <Building2 className="h-4 w-4 text-blue-400" />
          </div>
          <span className="font-medium text-white/90">{String(item.employer_name ?? '—')}</span>
        </div>
      ),
    },
    {
      key: 'member',
      header: 'Membre',
      render: (item) => {
        const member = item.member as { full_name?: string } | null;
        return <span className="text-white/70">{member?.full_name ?? String(item.member_name ?? '—')}</span>;
      },
    },
    {
      key: 'match_percentage',
      header: 'Pourcentage',
      render: (item) => (
        <Badge variant="secondary">{String(item.match_percentage ?? item.percentage ?? 100)}%</Badge>
      ),
    },
    {
      key: 'max_amount',
      header: 'Maximum',
      render: (item) =>
        item.max_amount
          ? <span className="text-emerald-400 font-semibold">{formatCurrency(String(item.max_amount))}</span>
          : <span className="text-white/30">Illimité</span>,
    },
    {
      key: 'matched_amount',
      header: 'Montant apparié',
      render: (item) => (
        <span className="text-white/70">{formatCurrency(String(item.matched_amount ?? 0))}</span>
      ),
    },
    {
      key: 'status',
      header: 'Statut',
      render: (item) => <PaymentStatusBadge status={(item.status as string) ?? 'active'} />,
    },
  ];

  function handleCreate() {
    if (!form.employer_name.trim()) {
      toast({ type: 'error', title: 'Nom requis' });
      return;
    }
    createMatch.mutate(
      {
        employer_name: form.employer_name.trim(),
        match_percentage: parseInt(form.match_percentage) || 100,
        max_amount: form.max_amount ? parseFloat(form.max_amount) : undefined,
      },
      {
        onSuccess: () => {
          toast({ type: 'success', title: 'Appariement créé' });
          setShowCreate(false);
          setForm({ employer_name: '', match_percentage: '100', max_amount: '' });
        },
        onError: () => {
          toast({ type: 'error', title: 'Erreur' });
        },
      },
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nouvel appariement
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
        emptyMessage="Aucun appariement employeur trouvé"
      />

      <Dialog open={showCreate} onClose={() => setShowCreate(false)}>
        <DialogHeader>
          <DialogTitle>Nouvel appariement employeur</DialogTitle>
          <DialogDescription>Configurer un programme d&apos;appariement de dons par l&apos;employeur</DialogDescription>
          <DialogClose onClose={() => setShowCreate(false)} />
        </DialogHeader>
        <DialogContent className="space-y-4">
          <div>
            <label className="block text-xs text-white/50 mb-1.5">Nom de l&apos;employeur *</label>
            <Input placeholder="ex. Entreprise ABC" value={form.employer_name} onChange={(e) => setForm((f) => ({ ...f, employer_name: e.target.value }))} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Pourcentage d&apos;appariement</label>
              <Input type="number" min="1" max="200" value={form.match_percentage} onChange={(e) => setForm((f) => ({ ...f, match_percentage: e.target.value }))} />
            </div>
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Montant maximum (CAD)</label>
              <Input type="number" min="0" step="0.01" placeholder="Illimité" value={form.max_amount} onChange={(e) => setForm((f) => ({ ...f, max_amount: e.target.value }))} />
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setShowCreate(false)}>Annuler</Button>
          <Button onClick={handleCreate} disabled={createMatch.isPending}>
            {createMatch.isPending ? 'Création...' : 'Créer'}
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── SMS Donations tab ───────────────────────────────────────────────────────

function SMSDonationsTab() {
  const [search, setSearch] = useState('');
  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteSMSDonations(search);

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as AnyRecord[];
  const totalCount = data?.pages[0]?.count;

  const columns: Column<AnyRecord>[] = [
    {
      key: 'phone_number',
      header: 'Téléphone',
      render: (item) => (
        <div className="flex items-center gap-2">
          <MessageSquare className="h-4 w-4 text-blue-400" />
          <span className="font-medium text-white/90">{String(item.phone_number ?? item.from_number ?? '—')}</span>
        </div>
      ),
    },
    {
      key: 'amount',
      header: 'Montant',
      render: (item) => (
        <span className="font-semibold text-emerald-400">{formatCurrency(String(item.amount ?? '0'))}</span>
      ),
    },
    {
      key: 'donation_type',
      header: 'Type',
      render: (item) => (
        <Badge variant="secondary">{String(item.donation_type ?? 'général')}</Badge>
      ),
    },
    {
      key: 'created_at',
      header: 'Date',
      render: (item) =>
        item.created_at
          ? formatDate(item.created_at as string, { year: 'numeric', month: 'short', day: 'numeric' })
          : '—',
    },
    {
      key: 'status',
      header: 'Statut',
      render: (item) => <PaymentStatusBadge status={(item.status as string) ?? 'succeeded'} />,
    },
  ];

  return (
    <div className="space-y-4">
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
        <Input placeholder="Rechercher par numéro..." className="pl-9" value={search} onChange={(e) => setSearch(e.target.value)} />
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
        emptyMessage="Aucun don par SMS trouvé"
      />
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function PaymentsPage() {
  const { data: paymentsData } = usePayments('page=1&page_size=1');
  const { data: recurringData } = useRecurringDonations('status=active');
  const { data: campaignsData } = useGivingCampaigns();

  // Derive stats
  const totalReceived = (() => {
    const results = (paymentsData?.results ?? []) as AnyRecord[];
    if (results.length === 0) return formatCurrency('0');
    const total = results.reduce((acc, p) => acc + Number(p.amount ?? 0) / 100, 0);
    return formatCurrency(String(total.toFixed(2)));
  })();

  const activeRecurring = recurringData?.count ?? 0;

  const avgDonation = (() => {
    const results = (paymentsData?.results ?? []) as AnyRecord[];
    if (results.length === 0) return formatCurrency('0');
    const total = results.reduce((acc, p) => acc + Number(p.amount ?? 0) / 100, 0);
    return formatCurrency(String((total / results.length).toFixed(2)));
  })();

  const campaignProgress = (() => {
    const campaigns = (campaignsData?.results ?? []) as AnyRecord[];
    if (campaigns.length === 0) return '0%';
    const goal = campaigns.reduce((acc, c) => acc + Number(c.goal_amount ?? c.target_amount ?? 0), 0);
    const raised = campaigns.reduce((acc, c) => acc + Number(c.raised_amount ?? c.current_amount ?? 0), 0);
    if (goal === 0) return '0%';
    return `${Math.round((raised / goal) * 100)}%`;
  })();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white/90">Paiements</h1>
          <p className="text-white/40 text-sm mt-0.5">Gestion des paiements en ligne, dons récurrents et campagnes</p>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={DollarSign}
          label="Total reçu"
          value={totalReceived}
          iconColor="text-emerald-400"
        />
        <StatCard
          icon={Repeat}
          label="Dons récurrents actifs"
          value={String(activeRecurring)}
          sub="abonnements"
          iconColor="text-blue-400"
        />
        <StatCard
          icon={TrendingUp}
          label="Don moyen"
          value={avgDonation}
          iconColor="text-purple-400"
        />
        <StatCard
          icon={Target}
          label="Progression campagnes"
          value={campaignProgress}
          sub={`${(campaignsData?.results ?? []).length} campagne(s)`}
          iconColor="text-amber-400"
        />
      </div>

      {/* Tabs */}
      <Tabs defaultValue="paiements">
        <TabsList className="flex-wrap gap-1 h-auto">
          <TabsTrigger value="paiements">
            <CreditCard className="h-3.5 w-3.5 mr-1.5 inline" />
            Paiements
          </TabsTrigger>
          <TabsTrigger value="recurrents">
            <Repeat className="h-3.5 w-3.5 mr-1.5 inline" />
            Récurrents
          </TabsTrigger>
          <TabsTrigger value="releves">
            <FileText className="h-3.5 w-3.5 mr-1.5 inline" />
            Relevés
          </TabsTrigger>
          <TabsTrigger value="objectifs">
            <Target className="h-3.5 w-3.5 mr-1.5 inline" />
            Objectifs
          </TabsTrigger>
          <TabsTrigger value="plans">
            <ClipboardList className="h-3.5 w-3.5 mr-1.5 inline" />
            Plans
          </TabsTrigger>
          <TabsTrigger value="campagnes">
            <Megaphone className="h-3.5 w-3.5 mr-1.5 inline" />
            Campagnes
          </TabsTrigger>
          <TabsTrigger value="employeurs">
            <Building2 className="h-3.5 w-3.5 mr-1.5 inline" />
            Employeurs
          </TabsTrigger>
          <TabsTrigger value="sms">
            <MessageSquare className="h-3.5 w-3.5 mr-1.5 inline" />
            SMS
          </TabsTrigger>
        </TabsList>

        <TabsContent value="paiements">
          <PaymentsTab />
        </TabsContent>

        <TabsContent value="recurrents">
          <RecurringTab />
        </TabsContent>

        <TabsContent value="releves">
          <StatementsTab />
        </TabsContent>

        <TabsContent value="objectifs">
          <GoalsTab />
        </TabsContent>

        <TabsContent value="plans">
          <PlansTab />
        </TabsContent>

        <TabsContent value="campagnes">
          <CampaignsTab />
        </TabsContent>

        <TabsContent value="employeurs">
          <EmployerMatchesTab />
        </TabsContent>

        <TabsContent value="sms">
          <SMSDonationsTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
