'use client';

import { useState } from 'react';
import {
  Heart,
  HandHeart,
  Users,
  UtensilsCrossed,
  ShieldCheck,
  Plus,
  Search,
  AlertTriangle,
  HandHelping,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { InfiniteScrollTable } from '@/components/ui/infinite-scroll-table';
import { InfiniteScrollList } from '@/components/ui/infinite-scroll-list';
import type { Column } from '@/components/ui/data-table';
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
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/toast';
import {
  useHelpRequests,
  useHelpRequestCategories,
  useCreateHelpRequest,
  usePrayerWall,
  useCreatePrayerRequest,
  usePastoralCare,
  useCareTeams,
  useBenevolenceFunds,
  useBenevolenceRequests,
  useMealTrains,
  useInfiniteHelpRequests,
  useInfinitePrayerWall,
  useInfinitePastoralCare,
  useInfiniteCareTeams,
  useInfiniteBenevolenceRequests,
  useInfiniteMealTrains,
  useCreatePastoralCare,
  useCreateBenevolenceRequest,
  useMealTrainSignup,
} from '@/hooks/use-help-requests';

// ─── Type helpers ──────────────────────────────────────────────────────────────

type AnyRecord = Record<string, unknown>;

function asString(v: unknown, fallback = '—'): string {
  return typeof v === 'string' && v ? v : fallback;
}

function asNumber(v: unknown, fallback = 0): number {
  return typeof v === 'number' ? v : fallback;
}

// ─── Label maps ────────────────────────────────────────────────────────────────

const URGENCY_LABELS: Record<string, string> = {
  high: 'Urgent',
  medium: 'Moyen',
  low: 'Faible',
};

const STATUS_LABELS: Record<string, string> = {
  open: 'Ouvert',
  assigned: 'Assigné',
  resolved: 'Résolu',
  closed: 'Fermé',
};

const PASTORAL_CARE_TYPE_LABELS: Record<string, string> = {
  visit: 'Visite',
  phone: 'Appel',
  counseling: 'Counseling',
  prayer: 'Prière',
  other: 'Autre',
};

// ─── Badge helpers ─────────────────────────────────────────────────────────────

function UrgencyBadge({ urgency }: { urgency: string }) {
  const variant =
    urgency === 'high'
      ? 'destructive'
      : urgency === 'medium'
        ? 'warning'
        : 'secondary';
  return <Badge variant={variant}>{URGENCY_LABELS[urgency] ?? urgency}</Badge>;
}

function StatusBadge({ status }: { status: string }) {
  const variant =
    status === 'open'
      ? 'default'
      : status === 'assigned'
        ? 'warning'
        : status === 'resolved'
          ? 'success'
          : 'secondary';
  return <Badge variant={variant}>{STATUS_LABELS[status] ?? status}</Badge>;
}

// ─── Stat card ─────────────────────────────────────────────────────────────────

function StatCard({
  title,
  value,
  icon: Icon,
  color,
  loading,
}: {
  title: string;
  value: string | number;
  icon: React.ElementType;
  color: string;
  loading?: boolean;
}) {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-white/50 uppercase tracking-wide">{title}</p>
            {loading ? (
              <Skeleton className="h-7 w-16 mt-1" />
            ) : (
              <p className="text-2xl font-bold mt-1 text-white">{value}</p>
            )}
          </div>
          <div className={`p-3 rounded-xl ${color}`}>
            <Icon className="h-5 w-5 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Empty state ───────────────────────────────────────────────────────────────

function EmptyState({ message }: { message: string }) {
  return (
    <div className="rounded-2xl bg-white/[0.05] backdrop-blur-xl border border-white/[0.08] p-12 text-center">
      <p className="text-white/40">{message}</p>
    </div>
  );
}

// ─── Skeleton card grid ────────────────────────────────────────────────────────

function SkeletonCardGrid({ count = 6 }: { count?: number }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <Card key={i}>
          <CardContent className="p-5 space-y-3">
            <Skeleton className="h-5 w-2/3" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-1/2" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// TAB: Demandes
// ═══════════════════════════════════════════════════════════════════════════════

const demandesColumns: Column<AnyRecord>[] = [
  {
    key: 'request_number',
    header: 'No.',
    render: (item) => (
      <span className="font-mono text-white/60">
        #{asString(item.request_number, String(item.id)).slice(0, 8)}
      </span>
    ),
  },
  {
    key: 'category',
    header: 'Catégorie',
    render: (item) => {
      const cat = item.category as { name: string } | null;
      return <span>{cat?.name ?? '—'}</span>;
    },
  },
  {
    key: 'urgency',
    header: 'Urgence',
    render: (item) => <UrgencyBadge urgency={asString(item.urgency, 'low')} />,
  },
  {
    key: 'status',
    header: 'Statut',
    render: (item) => <StatusBadge status={asString(item.status, 'open')} />,
  },
  {
    key: 'assigned_to',
    header: 'Assigné à',
    render: (item) => {
      const assignee = item.assigned_to as { full_name: string } | null;
      return <span>{assignee?.full_name ?? '—'}</span>;
    },
  },
  {
    key: 'created_at',
    header: 'Date',
    render: (item) => {
      const d = item.created_at ?? item.date;
      if (!d) return <span>—</span>;
      return (
        <span>
          {new Date(d as string).toLocaleDateString('fr-CA', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
          })}
        </span>
      );
    },
  },
];

function DemandesTab() {
  const { toast } = useToast();
  const [search, setSearch] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({
    category: '',
    description: '',
    urgency: 'low',
    is_confidential: false,
  });

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteHelpRequests(search);

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as AnyRecord[];
  const totalCount = data?.pages[0]?.count;

  const { data: categoriesRaw } = useHelpRequestCategories();
  const categories = Array.isArray(categoriesRaw) ? categoriesRaw : (categoriesRaw as any)?.results ?? [];
  const createMutation = useCreateHelpRequest();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    createMutation.mutate(
      { ...form, category_id: form.category || undefined },
      {
        onSuccess: () => {
          toast({ type: 'success', title: 'Demande créée', description: 'Votre demande a été soumise.' });
          setDialogOpen(false);
          setForm({ category: '', description: '', urgency: 'low', is_confidential: false });
        },
        onError: () => {
          toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer la demande.' });
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
            placeholder="Rechercher..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nouvelle demande
        </Button>
      </div>

      <InfiniteScrollTable
        columns={demandesColumns}
        data={items}
        totalCount={totalCount}
        isLoading={isLoading}
        fetchNextPage={fetchNextPage}
        hasNextPage={hasNextPage}
        isFetchingNextPage={isFetchingNextPage}
        error={error}
        emptyMessage="Aucune demande trouvée"
      />

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogHeader>
          <DialogTitle>Nouvelle demande d&apos;aide</DialogTitle>
          <DialogDescription>
            Remplissez les informations ci-dessous. Les demandes confidentielles ne sont visibles que par les pasteurs.
          </DialogDescription>
          <DialogClose onClose={() => setDialogOpen(false)} />
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <DialogContent className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs text-white/50 uppercase tracking-wide">Catégorie</label>
              <Select
                value={form.category}
                onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
              >
                <option value="">Aucune catégorie</option>
                {(categories as AnyRecord[] | undefined)?.map((cat) => (
                  <option key={cat.id as string} value={cat.id as string}>
                    {cat.name as string}
                  </option>
                ))}
              </Select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs text-white/50 uppercase tracking-wide">Description *</label>
              <Textarea
                placeholder="Décrivez votre demande..."
                rows={4}
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                required
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs text-white/50 uppercase tracking-wide">Urgence</label>
              <Select
                value={form.urgency}
                onChange={(e) => setForm((f) => ({ ...f, urgency: e.target.value }))}
              >
                <option value="low">Faible</option>
                <option value="medium">Moyen</option>
                <option value="high">Urgent</option>
              </Select>
            </div>

            <label className="flex items-center gap-3 cursor-pointer select-none">
              <div
                role="checkbox"
                aria-checked={form.is_confidential}
                tabIndex={0}
                onClick={() => setForm((f) => ({ ...f, is_confidential: !f.is_confidential }))}
                onKeyDown={(e) => e.key === ' ' && setForm((f) => ({ ...f, is_confidential: !f.is_confidential }))}
                className={`w-5 h-5 rounded border flex items-center justify-center transition-colors cursor-pointer ${
                  form.is_confidential
                    ? 'bg-primary border-primary'
                    : 'bg-white/[0.06] border-white/[0.12]'
                }`}
              >
                {!!form.is_confidential && (
                  <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 12 12" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M2 6l3 3 5-5" />
                  </svg>
                )}
              </div>
              <span className="text-sm text-white/70">Demande confidentielle</span>
            </label>
          </DialogContent>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => setDialogOpen(false)}>
              Annuler
            </Button>
            <Button type="submit" disabled={createMutation.isPending || !form.description.trim()}>
              {createMutation.isPending ? 'Envoi...' : 'Soumettre'}
            </Button>
          </DialogFooter>
        </form>
      </Dialog>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// TAB: Mur de prière
// ═══════════════════════════════════════════════════════════════════════════════

function PrayerWallTab() {
  const { toast } = useToast();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({ request_text: '', is_anonymous: false });

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfinitePrayerWall();
  const createMutation = useCreatePrayerRequest();

  const prayers = (data?.pages.flatMap((p) => p.results) ?? []) as AnyRecord[];
  const totalCount = data?.pages[0]?.count;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    createMutation.mutate(form, {
      onSuccess: () => {
        toast({ type: 'success', title: 'Demande de prière ajoutée', description: 'Votre demande est maintenant sur le mur.' });
        setDialogOpen(false);
        setForm({ request_text: '', is_anonymous: false });
      },
      onError: () => {
        toast({ type: 'error', title: 'Erreur', description: 'Impossible d\'ajouter la demande.' });
      },
    });
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Demande de prière
        </Button>
      </div>

      <InfiniteScrollList
        items={prayers}
        totalCount={totalCount}
        isLoading={isLoading}
        fetchNextPage={fetchNextPage}
        hasNextPage={hasNextPage}
        isFetchingNextPage={isFetchingNextPage}
        error={error}
        emptyMessage="Aucune demande de prière pour le moment"
        renderItem={(prayer, i) => {
          const member = prayer.member as { full_name: string } | null;
          const isAnon = prayer.is_anonymous as boolean | undefined;
          const date = prayer.created_at ?? prayer.date;

          return (
            <Card key={(prayer.id as string) ?? i} className="flex flex-col">
              <CardContent className="p-5 flex-1 space-y-3">
                <div className="flex items-start gap-2">
                  <Heart className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
                  <p className="text-sm text-white/80 leading-relaxed">
                    {asString(prayer.request_text ?? prayer.text)}
                  </p>
                </div>
              </CardContent>
              <CardFooter className="p-5 pt-0 flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-white/60">
                    {isAnon ? 'Anonyme' : (member?.full_name ?? 'Anonyme')}
                  </p>
                  {!!date && (
                    <p className="text-xs text-white/30">
                      {new Date(date as string).toLocaleDateString('fr-CA', {
                        month: 'short',
                        day: 'numeric',
                      })}
                    </p>
                  )}
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 gap-1.5"
                >
                  <Heart className="h-3.5 w-3.5" />
                  Prier
                </Button>
              </CardFooter>
            </Card>
          );
        }}
      />

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogHeader>
          <DialogTitle>Nouvelle demande de prière</DialogTitle>
          <DialogDescription>
            Partagez votre demande sur le mur de prière de la communauté.
          </DialogDescription>
          <DialogClose onClose={() => setDialogOpen(false)} />
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <DialogContent className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs text-white/50 uppercase tracking-wide">Demande de prière *</label>
              <Textarea
                placeholder="Partagez votre demande..."
                rows={4}
                value={form.request_text}
                onChange={(e) => setForm((f) => ({ ...f, request_text: e.target.value }))}
                required
              />
            </div>
            <label className="flex items-center gap-3 cursor-pointer select-none">
              <div
                role="checkbox"
                aria-checked={form.is_anonymous}
                tabIndex={0}
                onClick={() => setForm((f) => ({ ...f, is_anonymous: !f.is_anonymous }))}
                onKeyDown={(e) => e.key === ' ' && setForm((f) => ({ ...f, is_anonymous: !f.is_anonymous }))}
                className={`w-5 h-5 rounded border flex items-center justify-center transition-colors cursor-pointer ${
                  form.is_anonymous
                    ? 'bg-primary border-primary'
                    : 'bg-white/[0.06] border-white/[0.12]'
                }`}
              >
                {!!form.is_anonymous && (
                  <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 12 12" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M2 6l3 3 5-5" />
                  </svg>
                )}
              </div>
              <span className="text-sm text-white/70">Rester anonyme</span>
            </label>
          </DialogContent>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => setDialogOpen(false)}>
              Annuler
            </Button>
            <Button type="submit" disabled={createMutation.isPending || !form.request_text.trim()}>
              {createMutation.isPending ? 'Envoi...' : 'Publier'}
            </Button>
          </DialogFooter>
        </form>
      </Dialog>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// TAB: Soins pastoraux
// ═══════════════════════════════════════════════════════════════════════════════

const pastoralColumns: Column<AnyRecord>[] = [
  {
    key: 'member',
    header: 'Membre',
    render: (item) => {
      const member = item.member as { full_name: string } | null;
      return <span className="font-medium">{member?.full_name ?? '—'}</span>;
    },
  },
  {
    key: 'care_type',
    header: 'Type',
    render: (item) => (
      <Badge variant="outline">
        {PASTORAL_CARE_TYPE_LABELS[asString(item.care_type)] ?? asString(item.care_type)}
      </Badge>
    ),
  },
  {
    key: 'status',
    header: 'Statut',
    render: (item) => <StatusBadge status={asString(item.status, 'open')} />,
  },
  {
    key: 'next_follow_up',
    header: 'Prochain suivi',
    render: (item) => {
      const d = item.next_follow_up ?? item.follow_up_date;
      if (!d) return <span className="text-white/40">—</span>;
      return (
        <span>
          {new Date(d as string).toLocaleDateString('fr-CA', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
          })}
        </span>
      );
    },
  },
  {
    key: 'assigned_to',
    header: 'Responsable',
    render: (item) => {
      const assignee = item.assigned_to as { full_name: string } | null;
      return <span>{assignee?.full_name ?? '—'}</span>;
    },
  },
];

function SoinsPastorauxTab() {
  const { toast } = useToast();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({
    member_id: '',
    care_type: 'visit',
    notes: '',
    next_follow_up: '',
  });

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error: pastoralError,
  } = useInfinitePastoralCare();
  const createMutation = useCreatePastoralCare();

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as AnyRecord[];
  const totalCount = data?.pages[0]?.count;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    createMutation.mutate(
      { member: form.member_id, care_type: form.care_type, notes: form.notes, next_follow_up: form.next_follow_up || undefined },
      {
        onSuccess: () => {
          toast({ type: 'success', title: 'Entrée créée', description: 'Le suivi pastoral a été enregistré.' });
          setDialogOpen(false);
          setForm({ member_id: '', care_type: 'visit', notes: '', next_follow_up: '' });
        },
        onError: () => {
          toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer l\'entrée pastorale.' });
        },
      },
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nouvelle entrée
        </Button>
      </div>

      <InfiniteScrollTable
        columns={pastoralColumns}
        data={items}
        totalCount={totalCount}
        isLoading={isLoading}
        fetchNextPage={fetchNextPage}
        hasNextPage={hasNextPage}
        isFetchingNextPage={isFetchingNextPage}
        error={pastoralError}
        emptyMessage="Aucun suivi pastoral trouvé"
      />

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogHeader>
          <DialogTitle>Nouvelle entrée pastorale</DialogTitle>
          <DialogDescription>
            Enregistrez un suivi pastoral pour un membre de l&apos;église.
          </DialogDescription>
          <DialogClose onClose={() => setDialogOpen(false)} />
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <DialogContent className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs text-white/50 uppercase tracking-wide">ID du membre *</label>
              <Input
                placeholder="Identifiant du membre..."
                value={form.member_id}
                onChange={(e) => setForm((f) => ({ ...f, member_id: e.target.value }))}
                required
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs text-white/50 uppercase tracking-wide">Type de soin</label>
              <Select
                value={form.care_type}
                onChange={(e) => setForm((f) => ({ ...f, care_type: e.target.value }))}
              >
                <option value="visit">Visite</option>
                <option value="phone">Appel téléphonique</option>
                <option value="counseling">Counseling</option>
                <option value="prayer">Prière</option>
                <option value="other">Autre</option>
              </Select>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs text-white/50 uppercase tracking-wide">Notes</label>
              <Textarea
                placeholder="Notes sur le suivi..."
                rows={3}
                value={form.notes}
                onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs text-white/50 uppercase tracking-wide">Prochain suivi</label>
              <Input
                type="date"
                value={form.next_follow_up}
                onChange={(e) => setForm((f) => ({ ...f, next_follow_up: e.target.value }))}
              />
            </div>
          </DialogContent>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => setDialogOpen(false)}>
              Annuler
            </Button>
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Enregistrement...' : 'Enregistrer'}
            </Button>
          </DialogFooter>
        </form>
      </Dialog>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// TAB: Équipes de soins
// ═══════════════════════════════════════════════════════════════════════════════

function EquipesTab() {
  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteCareTeams();
  const teams = (data?.pages.flatMap((p) => p.results) ?? []) as AnyRecord[];
  const totalCount = data?.pages[0]?.count;

  return (
    <div className="space-y-4">
      <InfiniteScrollList
        items={teams}
        totalCount={totalCount}
        isLoading={isLoading}
        fetchNextPage={fetchNextPage}
        hasNextPage={hasNextPage}
        isFetchingNextPage={isFetchingNextPage}
        error={error}
        emptyMessage="Aucune équipe de soins configurée"
        renderItem={(team, i) => {
          const leader = team.leader as { full_name: string } | null;
          const memberCount = asNumber(team.member_count ?? team.members_count);

          return (
            <Card key={(team.id as string) ?? i} className="hover:bg-white/[0.07] transition-colors cursor-pointer">
              <CardHeader className="p-5 pb-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="p-2 rounded-lg bg-purple-500/20">
                    <Users className="h-4 w-4 text-purple-400" />
                  </div>
                  <Badge variant="secondary">
                    {memberCount} membre{memberCount !== 1 ? 's' : ''}
                  </Badge>
                </div>
                <CardTitle className="text-base mt-3">{asString(team.name)}</CardTitle>
                {!!team.description && (
                  <CardDescription className="text-xs line-clamp-2">
                    {asString(team.description)}
                  </CardDescription>
                )}
              </CardHeader>
              <CardFooter className="p-5 pt-0">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-full bg-purple-500/20 flex items-center justify-center">
                    <span className="text-xs text-purple-300 font-medium">
                      {leader?.full_name?.[0] ?? '?'}
                    </span>
                  </div>
                  <span className="text-xs text-white/50">
                    {leader?.full_name ? `Responsable: ${leader.full_name}` : 'Responsable non assigné'}
                  </span>
                </div>
              </CardFooter>
            </Card>
          );
        }}
      />
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// TAB: Bénévolence
// ═══════════════════════════════════════════════════════════════════════════════

const benevolenceRequestColumns: Column<AnyRecord>[] = [
  {
    key: 'member',
    header: 'Demandeur',
    render: (item) => {
      const member = item.member as { full_name: string } | null;
      return <span className="font-medium">{member?.full_name ?? '—'}</span>;
    },
  },
  {
    key: 'amount_requested',
    header: 'Montant demandé',
    render: (item) => {
      const amount = item.amount_requested ?? item.amount;
      if (!amount) return <span className="text-white/40">—</span>;
      return (
        <span className="font-medium">
          {Number(amount).toLocaleString('fr-CA', { style: 'currency', currency: 'CAD' })}
        </span>
      );
    },
  },
  {
    key: 'status',
    header: 'Statut',
    render: (item) => <StatusBadge status={asString(item.status, 'open')} />,
  },
  {
    key: 'created_at',
    header: 'Date',
    render: (item) => {
      const d = item.created_at ?? item.date;
      if (!d) return <span>—</span>;
      return (
        <span>
          {new Date(d as string).toLocaleDateString('fr-CA', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
          })}
        </span>
      );
    },
  },
];

function BenevolenceTab() {
  const { toast } = useToast();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({
    amount_requested: '',
    description: '',
    fund_id: '',
  });

  const { data: fundsData, isLoading: fundsLoading } = useBenevolenceFunds();
  const requestsQuery = useInfiniteBenevolenceRequests();
  const createBenevolence = useCreateBenevolenceRequest();

  const funds = (fundsData?.results ?? []) as AnyRecord[];
  const requestItems = (requestsQuery.data?.pages.flatMap((p) => p.results) ?? []) as AnyRecord[];
  const requestsTotalCount = requestsQuery.data?.pages[0]?.count;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    createBenevolence.mutate(
      {
        amount_requested: parseFloat(form.amount_requested) || 0,
        description: form.description,
        fund: form.fund_id || undefined,
      },
      {
        onSuccess: () => {
          toast({ type: 'success', title: 'Demande créée', description: 'Votre demande de bénévolence a été soumise.' });
          setDialogOpen(false);
          setForm({ amount_requested: '', description: '', fund_id: '' });
        },
        onError: () => {
          toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer la demande.' });
        },
      },
    );
  }

  return (
    <div className="space-y-6">
      {/* Funds section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-white/70 uppercase tracking-wide">
            Fonds disponibles
          </h3>
        </div>
        {fundsLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Card key={i}>
                <CardContent className="p-5 space-y-2">
                  <Skeleton className="h-5 w-2/3" />
                  <Skeleton className="h-4 w-1/2" />
                  <Skeleton className="h-4 w-1/3" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : funds.length === 0 ? (
          <EmptyState message="Aucun fonds de bénévolence configuré" />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {funds.map((fund, i) => {
              const balance = fund.balance ?? fund.current_balance ?? 0;
              const disbursed = fund.total_disbursed ?? fund.amount_disbursed ?? 0;

              return (
                <Card key={(fund.id as string) ?? i}>
                  <CardContent className="p-5 space-y-3">
                    <div className="flex items-center gap-2">
                      <div className="p-2 rounded-lg bg-emerald-500/20">
                        <ShieldCheck className="h-4 w-4 text-emerald-400" />
                      </div>
                      <p className="font-semibold text-white">{asString(fund.name)}</p>
                    </div>
                    {!!fund.description && (
                      <p className="text-xs text-white/50 line-clamp-2">{asString(fund.description)}</p>
                    )}
                    <div className="grid grid-cols-2 gap-2 pt-1">
                      <div className="rounded-lg bg-white/[0.04] p-2.5">
                        <p className="text-xs text-white/40">Solde</p>
                        <p className="text-sm font-bold text-emerald-400 mt-0.5">
                          {Number(balance).toLocaleString('fr-CA', { style: 'currency', currency: 'CAD' })}
                        </p>
                      </div>
                      <div className="rounded-lg bg-white/[0.04] p-2.5">
                        <p className="text-xs text-white/40">Distribué</p>
                        <p className="text-sm font-bold text-white/70 mt-0.5">
                          {Number(disbursed).toLocaleString('fr-CA', { style: 'currency', currency: 'CAD' })}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* Requests section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-white/70 uppercase tracking-wide">
            Demandes de bénévolence
          </h3>
          <Button size="sm" onClick={() => setDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Nouvelle demande
          </Button>
        </div>

        <InfiniteScrollTable
          columns={benevolenceRequestColumns}
          data={requestItems}
          totalCount={requestsTotalCount}
          isLoading={requestsQuery.isLoading}
          fetchNextPage={requestsQuery.fetchNextPage}
          hasNextPage={requestsQuery.hasNextPage}
          isFetchingNextPage={requestsQuery.isFetchingNextPage}
          error={requestsQuery.error}
          emptyMessage="Aucune demande de bénévolence"
        />
      </div>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogHeader>
          <DialogTitle>Demande de bénévolence</DialogTitle>
          <DialogDescription>
            Soumettez une demande d&apos;aide financière.
          </DialogDescription>
          <DialogClose onClose={() => setDialogOpen(false)} />
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <DialogContent className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs text-white/50 uppercase tracking-wide">Fonds</label>
              <Select
                value={form.fund_id}
                onChange={(e) => setForm((f) => ({ ...f, fund_id: e.target.value }))}
              >
                <option value="">Sélectionner un fonds</option>
                {funds.map((fund) => (
                  <option key={fund.id as string} value={fund.id as string}>
                    {fund.name as string}
                  </option>
                ))}
              </Select>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs text-white/50 uppercase tracking-wide">Montant demandé *</label>
              <Input
                type="number"
                min="0"
                step="0.01"
                placeholder="0.00"
                value={form.amount_requested}
                onChange={(e) => setForm((f) => ({ ...f, amount_requested: e.target.value }))}
                required
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs text-white/50 uppercase tracking-wide">Description *</label>
              <Textarea
                placeholder="Expliquez votre besoin..."
                rows={3}
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                required
              />
            </div>
          </DialogContent>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => setDialogOpen(false)}>
              Annuler
            </Button>
            <Button type="submit" disabled={createBenevolence.isPending}>
              {createBenevolence.isPending ? 'Envoi...' : 'Soumettre'}
            </Button>
          </DialogFooter>
        </form>
      </Dialog>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// TAB: Trains de repas
// ═══════════════════════════════════════════════════════════════════════════════

function MealTrainsTab() {
  const { toast } = useToast();
  const mealSignup = useMealTrainSignup();
  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error: mealError,
  } = useInfiniteMealTrains();
  const trains = (data?.pages.flatMap((p) => p.results) ?? []) as AnyRecord[];
  const totalCount = data?.pages[0]?.count;

  async function handleSignup(trainId: string) {
    try {
      await mealSignup.mutateAsync(trainId);
      toast({ type: 'success', title: 'Inscription confirmée', description: 'Vous êtes inscrit pour apporter un repas.' });
    } catch {
      toast({ type: 'error', title: 'Erreur', description: 'Impossible de vous inscrire.' });
    }
  }

  return (
    <div className="space-y-4">
      <InfiniteScrollList
        items={trains}
        totalCount={totalCount}
        isLoading={isLoading}
        fetchNextPage={fetchNextPage}
        hasNextPage={hasNextPage}
        isFetchingNextPage={isFetchingNextPage}
        error={mealError}
        emptyMessage="Aucun train de repas actif"
        renderItem={(train, i) => {
          const recipient = train.recipient as { full_name: string } | null;
          const startDate = train.start_date ?? train.start;
          const endDate = train.end_date ?? train.end;
          const mealsNeeded = asNumber(train.meals_needed ?? train.total_meals);
          const mealsSignedUp = asNumber(train.meals_signed_up ?? train.meals_claimed ?? train.signup_count);
          const progress = mealsNeeded > 0 ? Math.min((mealsSignedUp / mealsNeeded) * 100, 100) : 0;
          const isFull = mealsSignedUp >= mealsNeeded && mealsNeeded > 0;

          return (
            <Card key={(train.id as string) ?? i} className="flex flex-col">
              <CardHeader className="p-5 pb-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="p-2 rounded-lg bg-amber-500/20">
                    <UtensilsCrossed className="h-4 w-4 text-amber-400" />
                  </div>
                  {isFull ? (
                    <Badge variant="success">Complet</Badge>
                  ) : (
                    <Badge variant="warning">{mealsNeeded - mealsSignedUp} repas manquants</Badge>
                  )}
                </div>
                <CardTitle className="text-base mt-3">
                  {recipient?.full_name ?? asString(train.title ?? train.name)}
                </CardTitle>
                {!!(startDate || endDate) && (
                  <CardDescription className="text-xs">
                    {!!startDate && new Date(startDate as string).toLocaleDateString('fr-CA', { month: 'short', day: 'numeric' })}
                    {!!(startDate && endDate) && ' – '}
                    {!!endDate && new Date(endDate as string).toLocaleDateString('fr-CA', { month: 'short', day: 'numeric', year: 'numeric' })}
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent className="p-5 pt-0 space-y-3 flex-1">
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs text-white/50">Repas planifiés</span>
                    <span className="text-xs font-medium text-white/70">
                      {mealsSignedUp} / {mealsNeeded}
                    </span>
                  </div>
                  <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${isFull ? 'bg-emerald-500' : 'bg-amber-500'}`}
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>
              </CardContent>
              <CardFooter className="p-5 pt-0">
                <Button
                  className="w-full"
                  variant={isFull ? 'secondary' : 'default'}
                  size="sm"
                  disabled={isFull || mealSignup.isPending}
                  onClick={() => handleSignup(train.id as string)}
                >
                  <UtensilsCrossed className="h-3.5 w-3.5 mr-2" />
                  {isFull ? 'Complet' : "S'inscrire pour apporter un repas"}
                </Button>
              </CardFooter>
            </Card>
          );
        }}
      />
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════════════════════════════════

export default function HelpRequestsPage() {
  // Fetch counts for stat cards
  const { data: openData, isLoading: openLoading } = useHelpRequests('status=open&page_size=1');
  const { data: prayerData, isLoading: prayerLoading } = usePrayerWall('page_size=1');
  const { data: teamsData, isLoading: teamsLoading } = useCareTeams('page_size=1');
  const { data: mealData, isLoading: mealLoading } = useMealTrains('page_size=1');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Demandes d&apos;aide</h1>
        <p className="text-white/50 mt-0.5">Prière, aide matérielle et soins pastoraux</p>
      </div>

      {/* Stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Demandes ouvertes"
          value={openLoading ? '—' : (openData?.count ?? 0)}
          icon={AlertTriangle}
          color="bg-rose-500"
          loading={openLoading}
        />
        <StatCard
          title="Demandes de prière"
          value={prayerLoading ? '—' : (prayerData?.count ?? 0)}
          icon={Heart}
          color="bg-purple-500"
          loading={prayerLoading}
        />
        <StatCard
          title="Équipes de soins"
          value={teamsLoading ? '—' : (teamsData?.count ?? 0)}
          icon={Users}
          color="bg-blue-500"
          loading={teamsLoading}
        />
        <StatCard
          title="Trains de repas actifs"
          value={mealLoading ? '—' : (mealData?.count ?? 0)}
          icon={UtensilsCrossed}
          color="bg-amber-500"
          loading={mealLoading}
        />
      </div>

      {/* Tabs */}
      <Tabs defaultValue="demandes" className="space-y-4">
        <div className="overflow-x-auto">
          <TabsList className="w-max min-w-full sm:w-auto">
            <TabsTrigger value="demandes">
              <HandHelping className="h-4 w-4 mr-2 inline-block" />
              Demandes
            </TabsTrigger>
            <TabsTrigger value="priere">
              <Heart className="h-4 w-4 mr-2 inline-block" />
              Mur de prière
            </TabsTrigger>
            <TabsTrigger value="pastoral">
              <ShieldCheck className="h-4 w-4 mr-2 inline-block" />
              Soins pastoraux
            </TabsTrigger>
            <TabsTrigger value="equipes">
              <Users className="h-4 w-4 mr-2 inline-block" />
              Équipes
            </TabsTrigger>
            <TabsTrigger value="benevolence">
              <HandHeart className="h-4 w-4 mr-2 inline-block" />
              Bénévolence
            </TabsTrigger>
            <TabsTrigger value="repas">
              <UtensilsCrossed className="h-4 w-4 mr-2 inline-block" />
              Trains de repas
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="demandes">
          <DemandesTab />
        </TabsContent>

        <TabsContent value="priere">
          <PrayerWallTab />
        </TabsContent>

        <TabsContent value="pastoral">
          <SoinsPastorauxTab />
        </TabsContent>

        <TabsContent value="equipes">
          <EquipesTab />
        </TabsContent>

        <TabsContent value="benevolence">
          <BenevolenceTab />
        </TabsContent>

        <TabsContent value="repas">
          <MealTrainsTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
