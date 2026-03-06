'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Users,
  Clock,
  Calendar,
  ArrowLeftRight,
  Plus,
  Search,
  CheckCircle,
  Briefcase,
  Wrench,
  CalendarOff,
  Timer,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
  useSchedules,
  useInfinitePositions,
  useInfiniteSchedules,
  useInfiniteAvailability,
  useInfiniteSwapRequests,
  useInfiniteSkills,
  useInfinitePlannedAbsences,
  useInfiniteVolunteerHours,
  useConfirmSchedule,
  useCreatePosition,
  useCreateAvailability,
  useCreateSkill,
  useCreatePlannedAbsence,
  useLogVolunteerHours,
  type Position,
  type Schedule,
  type Availability,
  type SwapRequest,
} from '@/hooks/use-volunteers';

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

const SCHEDULE_STATUS_VARIANT: Record<string, 'default' | 'success' | 'warning' | 'destructive' | 'secondary'> = {
  pending: 'warning',
  confirmed: 'success',
  absent: 'destructive',
  replaced: 'secondary',
};

const SWAP_STATUS_LABELS: Record<string, string> = {
  pending: 'En attente',
  accepted: 'Accepté',
  rejected: 'Refusé',
  cancelled: 'Annulé',
};

const SWAP_STATUS_VARIANT: Record<string, 'default' | 'success' | 'warning' | 'destructive' | 'secondary'> = {
  pending: 'warning',
  accepted: 'success',
  rejected: 'destructive',
  cancelled: 'secondary',
};

const DAY_LABELS: Record<number, string> = {
  0: 'Lundi',
  1: 'Mardi',
  2: 'Mercredi',
  3: 'Jeudi',
  4: 'Vendredi',
  5: 'Samedi',
  6: 'Dimanche',
};

// ─── Column definitions ───────────────────────────────────────────────────────

function usePositionColumns() {
  const columns: Column<Position & Record<string, unknown>>[] = [
    {
      key: 'name',
      header: 'Poste',
      render: (item) => (
        <div>
          <p className="font-medium text-white/90">{item.name}</p>
          {!!item.description && (
            <p className="text-xs text-white/40 mt-0.5 truncate max-w-xs">{item.description}</p>
          )}
        </div>
      ),
    },
    {
      key: 'position_type',
      header: 'Type',
      render: (item) => (
        <Badge variant="outline">
          {POSITION_TYPE_LABELS[item.position_type] || item.position_type}
        </Badge>
      ),
    },
    {
      key: 'min_volunteers',
      header: 'Min / Max',
      render: (item) => (
        <span className="text-white/70 tabular-nums">
          {item.min_volunteers} – {item.max_volunteers}
        </span>
      ),
    },
    {
      key: 'active_volunteer_count',
      header: 'Bénévoles actifs',
      render: (item) => (
        <div className="flex items-center gap-2">
          <span className="text-white/70 tabular-nums">
            {item.active_volunteer_count ?? '—'}
          </span>
          {typeof item.active_volunteer_count === 'number' &&
            item.active_volunteer_count < item.min_volunteers && (
              <Badge variant="destructive">Insuffisant</Badge>
            )}
        </div>
      ),
    },
    {
      key: 'is_active',
      header: 'État',
      render: (item) => (
        <Badge variant={item.is_active ? 'success' : 'secondary'}>
          {item.is_active ? 'Actif' : 'Inactif'}
        </Badge>
      ),
    },
  ];
  return columns;
}

const scheduleColumns: Column<Schedule & Record<string, unknown>>[] = [
  {
    key: 'member_name',
    header: 'Bénévole',
    render: (item) => (
      <p className="font-medium text-white/90">{item.member_name || '—'}</p>
    ),
  },
  {
    key: 'position_name',
    header: 'Poste',
    render: (item) => (
      <p className="text-white/70">{item.position_name || '—'}</p>
    ),
  },
  {
    key: 'scheduled_date',
    header: 'Date',
    render: (item) =>
      item.scheduled_date
        ? new Date(item.scheduled_date).toLocaleDateString('fr-CA', {
            year: 'numeric',
            month: 'short',
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
];

const availabilityColumns: Column<Availability & Record<string, unknown>>[] = [
  {
    key: 'member_name',
    header: 'Bénévole',
    render: (item) => (
      <p className="font-medium text-white/90">{item.member_name || '—'}</p>
    ),
  },
  {
    key: 'day_of_week',
    header: 'Jour',
    render: (item) =>
      item.day_of_week_display ||
      (typeof item.day_of_week === 'number' ? DAY_LABELS[item.day_of_week] : '—'),
  },
  {
    key: 'start_time',
    header: 'Début',
    render: (item) => item.start_time || '—',
  },
  {
    key: 'end_time',
    header: 'Fin',
    render: (item) => item.end_time || '—',
  },
  {
    key: 'is_available',
    header: 'Disponible',
    render: (item) => (
      <Badge variant={item.is_available ? 'success' : 'destructive'}>
        {item.is_available ? 'Oui' : 'Non'}
      </Badge>
    ),
  },
];

const swapColumns: Column<SwapRequest & Record<string, unknown>>[] = [
  {
    key: 'requester_name',
    header: 'Demandeur',
    render: (item) => (
      <p className="font-medium text-white/90">{item.requester_name || '—'}</p>
    ),
  },
  {
    key: 'target_name',
    header: 'Remplaçant',
    render: (item) => (
      <p className="text-white/70">{item.target_name || '—'}</p>
    ),
  },
  {
    key: 'schedule_name',
    header: 'Planification',
    render: (item) => (
      <p className="text-white/70">{item.schedule_name || '—'}</p>
    ),
  },
  {
    key: 'status',
    header: 'Statut',
    render: (item) => (
      <Badge variant={SWAP_STATUS_VARIANT[item.status] || 'secondary'}>
        {SWAP_STATUS_LABELS[item.status] || item.status}
      </Badge>
    ),
  },
  {
    key: 'created_at',
    header: 'Créé le',
    render: (item) =>
      item.created_at
        ? new Date(item.created_at).toLocaleDateString('fr-CA', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
          })
        : '—',
  },
];

// ─── Stat Card ────────────────────────────────────────────────────────────────

function StatCard({
  title,
  value,
  icon: Icon,
  color = 'text-purple-400',
  loading = false,
}: {
  title: string;
  value: string | number;
  icon: React.ElementType;
  color?: string;
  loading?: boolean;
}) {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-xs text-white/40 uppercase tracking-wider">{title}</p>
            {loading ? (
              <div className="h-8 w-16 bg-white/[0.06] rounded-lg animate-pulse" />
            ) : (
              <p className="text-2xl font-bold text-white">{value}</p>
            )}
          </div>
          <div className={`p-3 rounded-xl bg-white/[0.04] border border-white/[0.06] ${color}`}>
            <Icon className="h-5 w-5" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Create Position Dialog ───────────────────────────────────────────────────

function CreatePositionDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const createPosition = useCreatePosition();
  const [form, setForm] = useState({
    name: '',
    description: '',
    position_type: 'other',
    min_volunteers: '1',
    max_volunteers: '5',
  });

  function handleChange(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name.trim()) return;
    try {
      await createPosition.mutateAsync({
        name: form.name.trim(),
        description: form.description.trim() || undefined,
        position_type: form.position_type,
        min_volunteers: parseInt(form.min_volunteers, 10),
        max_volunteers: parseInt(form.max_volunteers, 10),
      });
      toast({ type: 'success', title: 'Poste créé avec succès' });
      setForm({ name: '', description: '', position_type: 'other', min_volunteers: '1', max_volunteers: '5' });
      onClose();
    } catch {
      toast({ type: 'error', title: 'Erreur lors de la création', description: 'Veuillez réessayer.' });
    }
  }

  return (
    <Dialog open={open} onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <DialogHeader>
          <DialogTitle>Nouveau poste de bénévolat</DialogTitle>
          <DialogDescription>Définissez un nouveau rôle pour les bénévoles.</DialogDescription>
          <DialogClose onClose={onClose} />
        </DialogHeader>
        <DialogContent className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs text-white/50 uppercase tracking-wider">Nom du poste *</label>
            <Input
              placeholder="ex. Sonoriste, Accueil, Louange..."
              value={form.name}
              onChange={(e) => handleChange('name', e.target.value)}
              required
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs text-white/50 uppercase tracking-wider">Type</label>
            <Select value={form.position_type} onChange={(e) => handleChange('position_type', e.target.value)}>
              {Object.entries(POSITION_TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </Select>
          </div>
          <div className="space-y-1.5">
            <label className="text-xs text-white/50 uppercase tracking-wider">Description</label>
            <Textarea
              placeholder="Décrivez les responsabilités de ce poste..."
              value={form.description}
              onChange={(e) => handleChange('description', e.target.value)}
              rows={3}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs text-white/50 uppercase tracking-wider">Minimum bénévoles</label>
              <Input
                type="number"
                min="0"
                value={form.min_volunteers}
                onChange={(e) => handleChange('min_volunteers', e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs text-white/50 uppercase tracking-wider">Maximum bénévoles</label>
              <Input
                type="number"
                min="1"
                value={form.max_volunteers}
                onChange={(e) => handleChange('max_volunteers', e.target.value)}
              />
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button type="button" variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button type="submit" disabled={createPosition.isPending}>
            {createPosition.isPending ? 'Création...' : 'Créer le poste'}
          </Button>
        </DialogFooter>
      </form>
    </Dialog>
  );
}

// ─── Create Availability Dialog ───────────────────────────────────────────────

function CreateAvailabilityDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const createAvailability = useCreateAvailability();
  const [form, setForm] = useState({
    day_of_week: '6',
    start_time: '09:00',
    end_time: '12:00',
    is_available: 'true',
    notes: '',
  });

  function handleChange(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      await createAvailability.mutateAsync({
        day_of_week: parseInt(form.day_of_week, 10),
        start_time: form.start_time,
        end_time: form.end_time,
        is_available: form.is_available === 'true',
        notes: form.notes.trim() || undefined,
      });
      toast({ type: 'success', title: 'Disponibilité ajoutée' });
      setForm({ day_of_week: '6', start_time: '09:00', end_time: '12:00', is_available: 'true', notes: '' });
      onClose();
    } catch {
      toast({ type: 'error', title: "Erreur lors de l'ajout", description: 'Veuillez réessayer.' });
    }
  }

  return (
    <Dialog open={open} onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <DialogHeader>
          <DialogTitle>Ajouter une disponibilité</DialogTitle>
          <DialogDescription>Indiquez vos plages de disponibilité hebdomadaire.</DialogDescription>
          <DialogClose onClose={onClose} />
        </DialogHeader>
        <DialogContent className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs text-white/50 uppercase tracking-wider">Jour de la semaine</label>
            <Select value={form.day_of_week} onChange={(e) => handleChange('day_of_week', e.target.value)}>
              {Object.entries(DAY_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs text-white/50 uppercase tracking-wider">Heure de début</label>
              <Input
                type="time"
                value={form.start_time}
                onChange={(e) => handleChange('start_time', e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs text-white/50 uppercase tracking-wider">Heure de fin</label>
              <Input
                type="time"
                value={form.end_time}
                onChange={(e) => handleChange('end_time', e.target.value)}
              />
            </div>
          </div>
          <div className="space-y-1.5">
            <label className="text-xs text-white/50 uppercase tracking-wider">Disponible</label>
            <Select value={form.is_available} onChange={(e) => handleChange('is_available', e.target.value)}>
              <option value="true">Oui</option>
              <option value="false">Non</option>
            </Select>
          </div>
          <div className="space-y-1.5">
            <label className="text-xs text-white/50 uppercase tracking-wider">Notes</label>
            <Textarea
              placeholder="Notes supplémentaires..."
              value={form.notes}
              onChange={(e) => handleChange('notes', e.target.value)}
              rows={2}
            />
          </div>
        </DialogContent>
        <DialogFooter>
          <Button type="button" variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button type="submit" disabled={createAvailability.isPending}>
            {createAvailability.isPending ? 'Ajout...' : 'Ajouter'}
          </Button>
        </DialogFooter>
      </form>
    </Dialog>
  );
}

// ─── Planning Tab with Confirm Action ────────────────────────────────────────

function PlanningTab({ search }: { search: string }) {
  const { toast } = useToast();
  const confirmSchedule = useConfirmSchedule();

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteSchedules(search);

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as (Schedule & Record<string, unknown>)[];
  const totalCount = data?.pages[0]?.count;

  const columnsWithAction: Column<Schedule & Record<string, unknown>>[] = [
    ...scheduleColumns,
    {
      key: '_action',
      header: 'Action',
      render: (item) =>
        item.status === 'pending' ? (
          <Button
            size="sm"
            variant="success"
            onClick={(e) => {
              e.stopPropagation();
              confirmSchedule.mutate(item.id, {
                onSuccess: () => toast({ type: 'success', title: 'Présence confirmée' }),
                onError: () => toast({ type: 'error', title: 'Erreur de confirmation' }),
              });
            }}
            disabled={confirmSchedule.isPending}
          >
            <CheckCircle className="h-3.5 w-3.5 mr-1.5" />
            Confirmer
          </Button>
        ) : null,
    },
  ];

  return (
    <InfiniteScrollTable
      columns={columnsWithAction}
      data={items}
      totalCount={totalCount}
      isLoading={isLoading}
      fetchNextPage={fetchNextPage}
      hasNextPage={hasNextPage}
      isFetchingNextPage={isFetchingNextPage}
      error={error}
      emptyMessage="Aucune planification trouvée"
    />
  );
}

// ─── Skills Tab ──────────────────────────────────────────────────────────────

function SkillsTab({ search }: { search: string }) {
  const { toast } = useToast();
  const [showCreate, setShowCreate] = useState(false);
  const createSkill = useCreateSkill();
  const [form, setForm] = useState({ name: '', category: '' });

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteSkills(search);

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as (Record<string, unknown>)[];
  const totalCount = data?.pages[0]?.count;

  const columns: Column<Record<string, unknown>>[] = [
    {
      key: 'name',
      header: 'Compétence',
      render: (item) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-purple-500/10">
            <Wrench className="h-4 w-4 text-purple-400" />
          </div>
          <span className="font-medium text-white/90">{String(item.name ?? '—')}</span>
        </div>
      ),
    },
    {
      key: 'category',
      header: 'Catégorie',
      render: (item) => (
        <Badge variant="outline">{String(item.category ?? '—')}</Badge>
      ),
    },
    {
      key: 'members_count',
      header: 'Bénévoles',
      render: (item) => (
        <span className="text-white/70 tabular-nums">{String(item.members_count ?? 0)}</span>
      ),
    },
  ];

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!form.name.trim()) return;
    try {
      await createSkill.mutateAsync({ name: form.name.trim(), category: form.category.trim() || undefined });
      toast({ type: 'success', title: 'Compétence créée' });
      setForm({ name: '', category: '' });
      setShowCreate(false);
    } catch {
      toast({ type: 'error', title: 'Erreur lors de la création' });
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nouvelle compétence
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
        emptyMessage="Aucune compétence trouvée"
      />

      <Dialog open={showCreate} onClose={() => setShowCreate(false)}>
        <form onSubmit={handleCreate}>
          <DialogHeader>
            <DialogTitle>Nouvelle compétence</DialogTitle>
            <DialogDescription>Ajouter une compétence au catalogue de bénévolat.</DialogDescription>
            <DialogClose onClose={() => setShowCreate(false)} />
          </DialogHeader>
          <DialogContent className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs text-white/50 uppercase tracking-wider">Nom *</label>
              <Input
                placeholder="ex. Sonorisation, Piano, Premiers soins..."
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                required
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs text-white/50 uppercase tracking-wider">Catégorie</label>
              <Input
                placeholder="ex. Technique, Musique, Santé..."
                value={form.category}
                onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
              />
            </div>
          </DialogContent>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => setShowCreate(false)}>Annuler</Button>
            <Button type="submit" disabled={createSkill.isPending}>
              {createSkill.isPending ? 'Création...' : 'Créer'}
            </Button>
          </DialogFooter>
        </form>
      </Dialog>
    </div>
  );
}

// ─── Absences Tab ────────────────────────────────────────────────────────────

function AbsencesTab({ search }: { search: string }) {
  const { toast } = useToast();
  const [showCreate, setShowCreate] = useState(false);
  const createAbsence = useCreatePlannedAbsence();
  const [form, setForm] = useState({ start_date: '', end_date: '', reason: '' });

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfinitePlannedAbsences(search);

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as (Record<string, unknown>)[];
  const totalCount = data?.pages[0]?.count;

  const columns: Column<Record<string, unknown>>[] = [
    {
      key: 'member_name',
      header: 'Bénévole',
      render: (item) => (
        <span className="font-medium text-white/90">{String(item.member_name ?? '—')}</span>
      ),
    },
    {
      key: 'start_date',
      header: 'Début',
      render: (item) =>
        item.start_date
          ? new Date(item.start_date as string).toLocaleDateString('fr-CA', { year: 'numeric', month: 'short', day: 'numeric' })
          : '—',
    },
    {
      key: 'end_date',
      header: 'Fin',
      render: (item) =>
        item.end_date
          ? new Date(item.end_date as string).toLocaleDateString('fr-CA', { year: 'numeric', month: 'short', day: 'numeric' })
          : '—',
    },
    {
      key: 'reason',
      header: 'Raison',
      render: (item) => (
        <span className="text-white/60 truncate max-w-xs">{String(item.reason ?? '—')}</span>
      ),
    },
    {
      key: 'status',
      header: 'Statut',
      render: (item) => {
        const status = String(item.status ?? 'pending');
        const labels: Record<string, string> = { pending: 'En attente', approved: 'Approuvé', rejected: 'Refusé' };
        const variants: Record<string, 'warning' | 'success' | 'destructive'> = { pending: 'warning', approved: 'success', rejected: 'destructive' };
        return <Badge variant={variants[status] ?? 'secondary'}>{labels[status] ?? status}</Badge>;
      },
    },
  ];

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!form.start_date || !form.end_date) return;
    try {
      await createAbsence.mutateAsync({
        start_date: form.start_date,
        end_date: form.end_date,
        reason: form.reason.trim() || undefined,
      });
      toast({ type: 'success', title: 'Absence planifiée' });
      setForm({ start_date: '', end_date: '', reason: '' });
      setShowCreate(false);
    } catch {
      toast({ type: 'error', title: "Erreur lors de l'ajout" });
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Planifier une absence
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
        emptyMessage="Aucune absence planifiée"
      />

      <Dialog open={showCreate} onClose={() => setShowCreate(false)}>
        <form onSubmit={handleCreate}>
          <DialogHeader>
            <DialogTitle>Planifier une absence</DialogTitle>
            <DialogDescription>Indiquer une période d&apos;absence à venir.</DialogDescription>
            <DialogClose onClose={() => setShowCreate(false)} />
          </DialogHeader>
          <DialogContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs text-white/50 uppercase tracking-wider">Date de début *</label>
                <Input type="date" value={form.start_date} onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value }))} required />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs text-white/50 uppercase tracking-wider">Date de fin *</label>
                <Input type="date" value={form.end_date} onChange={(e) => setForm((f) => ({ ...f, end_date: e.target.value }))} required />
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs text-white/50 uppercase tracking-wider">Raison</label>
              <Textarea
                placeholder="Vacances, maladie, etc."
                value={form.reason}
                onChange={(e) => setForm((f) => ({ ...f, reason: e.target.value }))}
                rows={2}
              />
            </div>
          </DialogContent>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => setShowCreate(false)}>Annuler</Button>
            <Button type="submit" disabled={createAbsence.isPending}>
              {createAbsence.isPending ? 'Ajout...' : 'Planifier'}
            </Button>
          </DialogFooter>
        </form>
      </Dialog>
    </div>
  );
}

// ─── Hours Tab ───────────────────────────────────────────────────────────────

function HoursTab({ search }: { search: string }) {
  const { toast } = useToast();
  const [showLog, setShowLog] = useState(false);
  const logHours = useLogVolunteerHours();
  const [form, setForm] = useState({ date: '', hours: '', description: '' });

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteVolunteerHours(search);

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as (Record<string, unknown>)[];
  const totalCount = data?.pages[0]?.count;

  const columns: Column<Record<string, unknown>>[] = [
    {
      key: 'member_name',
      header: 'Bénévole',
      render: (item) => (
        <span className="font-medium text-white/90">{String(item.member_name ?? '—')}</span>
      ),
    },
    {
      key: 'date',
      header: 'Date',
      render: (item) =>
        item.date
          ? new Date(item.date as string).toLocaleDateString('fr-CA', { year: 'numeric', month: 'short', day: 'numeric' })
          : '—',
    },
    {
      key: 'hours',
      header: 'Heures',
      render: (item) => (
        <span className="text-emerald-400 font-semibold tabular-nums">{String(item.hours ?? item.duration ?? '—')}h</span>
      ),
    },
    {
      key: 'position_name',
      header: 'Poste',
      render: (item) => (
        <span className="text-white/60">{String(item.position_name ?? '—')}</span>
      ),
    },
    {
      key: 'description',
      header: 'Description',
      render: (item) => (
        <span className="text-white/50 truncate max-w-xs">{String(item.description ?? '—')}</span>
      ),
    },
  ];

  async function handleLog(e: React.FormEvent) {
    e.preventDefault();
    if (!form.date || !form.hours) return;
    try {
      await logHours.mutateAsync({
        date: form.date,
        hours: parseFloat(form.hours),
        description: form.description.trim() || undefined,
      });
      toast({ type: 'success', title: 'Heures enregistrées' });
      setForm({ date: '', hours: '', description: '' });
      setShowLog(false);
    } catch {
      toast({ type: 'error', title: "Erreur lors de l'enregistrement" });
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setShowLog(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Enregistrer des heures
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
        emptyMessage="Aucune heure enregistrée"
      />

      <Dialog open={showLog} onClose={() => setShowLog(false)}>
        <form onSubmit={handleLog}>
          <DialogHeader>
            <DialogTitle>Enregistrer des heures</DialogTitle>
            <DialogDescription>Consigner les heures de bénévolat effectuées.</DialogDescription>
            <DialogClose onClose={() => setShowLog(false)} />
          </DialogHeader>
          <DialogContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs text-white/50 uppercase tracking-wider">Date *</label>
                <Input type="date" value={form.date} onChange={(e) => setForm((f) => ({ ...f, date: e.target.value }))} required />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs text-white/50 uppercase tracking-wider">Heures *</label>
                <Input type="number" min="0.25" step="0.25" placeholder="2" value={form.hours} onChange={(e) => setForm((f) => ({ ...f, hours: e.target.value }))} required />
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs text-white/50 uppercase tracking-wider">Description</label>
              <Input
                placeholder="Activité réalisée..."
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              />
            </div>
          </DialogContent>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => setShowLog(false)}>Annuler</Button>
            <Button type="submit" disabled={logHours.isPending}>
              {logHours.isPending ? 'Enregistrement...' : 'Enregistrer'}
            </Button>
          </DialogFooter>
        </form>
      </Dialog>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function VolunteersPage() {
  const router = useRouter();
  const [search, setSearch] = useState('');
  const [showCreatePosition, setShowCreatePosition] = useState(false);
  const [showCreateAvailability, setShowCreateAvailability] = useState(false);
  const [activeTab, setActiveTab] = useState('positions');

  // Infinite scroll hooks
  const positionsQuery = useInfinitePositions(search);
  const availQuery = useInfiniteAvailability(search);
  const swapQuery = useInfiniteSwapRequests(search);

  // Still need schedules for stats
  const { data: allSchedules } = useSchedules('page_size=100');

  const positionColumns = usePositionColumns();

  // Flatten data
  const positions = (positionsQuery.data?.pages.flatMap((p) => p.results) ?? []) as (Position & Record<string, unknown>)[];
  const availability = (availQuery.data?.pages.flatMap((p) => p.results) ?? []) as (Availability & Record<string, unknown>)[];
  const swapRequests = (swapQuery.data?.pages.flatMap((p) => p.results) ?? []) as (SwapRequest & Record<string, unknown>)[];

  // Derive stats
  const scheduledThisWeek = (() => {
    if (!allSchedules?.results) return 0;
    const now = new Date();
    const weekStart = new Date(now);
    weekStart.setDate(now.getDate() - now.getDay() + 1);
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekStart.getDate() + 6);
    return allSchedules.results.filter((s) => {
      const d = new Date(s.scheduled_date);
      return d >= weekStart && d <= weekEnd;
    }).length;
  })();

  const openPositions = (() => {
    if (!positions.length) return 0;
    return positions.filter(
      (p) =>
        p.is_active &&
        typeof p.active_volunteer_count === 'number' &&
        p.active_volunteer_count < p.min_volunteers,
    ).length;
  })();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Bénévoles</h1>
          <p className="text-white/40 mt-0.5">Gérer les postes, planifications et disponibilités</p>
        </div>
        {activeTab === 'positions' && (
          <Button onClick={() => setShowCreatePosition(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Nouveau poste
          </Button>
        )}
        {activeTab === 'disponibilites' && (
          <Button onClick={() => setShowCreateAvailability(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Ajouter disponibilité
          </Button>
        )}
      </div>

      {/* Stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Postes actifs"
          value={positionsQuery.data?.pages[0]?.count ?? '—'}
          icon={Users}
          color="text-purple-400"
          loading={positionsQuery.isLoading}
        />
        <StatCard
          title="Heures ce mois"
          value="—"
          icon={Clock}
          color="text-sky-400"
        />
        <StatCard
          title="Planifiés cette semaine"
          value={scheduledThisWeek}
          icon={Calendar}
          color="text-emerald-400"
        />
        <StatCard
          title="Postes à combler"
          value={openPositions}
          icon={Briefcase}
          color="text-amber-400"
          loading={positionsQuery.isLoading}
        />
      </div>

      {/* Search bar */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
        <Input
          placeholder="Rechercher..."
          className="pl-9"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Tabs */}
      <Tabs defaultValue="positions" onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="positions">
            <Users className="h-4 w-4 mr-2" />
            Postes
          </TabsTrigger>
          <TabsTrigger value="planning">
            <Calendar className="h-4 w-4 mr-2" />
            Planning
          </TabsTrigger>
          <TabsTrigger value="disponibilites">
            <Clock className="h-4 w-4 mr-2" />
            Disponibilités
          </TabsTrigger>
          <TabsTrigger value="echanges">
            <ArrowLeftRight className="h-4 w-4 mr-2" />
            Échanges
          </TabsTrigger>
          <TabsTrigger value="competences">
            <Wrench className="h-4 w-4 mr-2" />
            Compétences
          </TabsTrigger>
          <TabsTrigger value="absences">
            <CalendarOff className="h-4 w-4 mr-2" />
            Absences
          </TabsTrigger>
          <TabsTrigger value="heures">
            <Timer className="h-4 w-4 mr-2" />
            Heures
          </TabsTrigger>
        </TabsList>

        {/* Positions tab */}
        <TabsContent value="positions">
          <InfiniteScrollTable
            columns={positionColumns}
            data={positions}
            totalCount={positionsQuery.data?.pages[0]?.count}
            isLoading={positionsQuery.isLoading}
            fetchNextPage={positionsQuery.fetchNextPage}
            hasNextPage={positionsQuery.hasNextPage}
            isFetchingNextPage={positionsQuery.isFetchingNextPage}
            error={positionsQuery.error}
            emptyMessage="Aucun poste trouvé"
            onRowClick={(item) => router.push(`/volunteers/${item.id}`)}
          />
        </TabsContent>

        {/* Planning tab */}
        <TabsContent value="planning">
          <PlanningTab search={search} />
        </TabsContent>

        {/* Disponibilités tab */}
        <TabsContent value="disponibilites">
          <InfiniteScrollTable
            columns={availabilityColumns}
            data={availability}
            totalCount={availQuery.data?.pages[0]?.count}
            isLoading={availQuery.isLoading}
            fetchNextPage={availQuery.fetchNextPage}
            hasNextPage={availQuery.hasNextPage}
            isFetchingNextPage={availQuery.isFetchingNextPage}
            error={availQuery.error}
            emptyMessage="Aucune disponibilité enregistrée"
          />
        </TabsContent>

        {/* Échanges tab */}
        <TabsContent value="echanges">
          <InfiniteScrollTable
            columns={swapColumns}
            data={swapRequests}
            totalCount={swapQuery.data?.pages[0]?.count}
            isLoading={swapQuery.isLoading}
            fetchNextPage={swapQuery.fetchNextPage}
            hasNextPage={swapQuery.hasNextPage}
            isFetchingNextPage={swapQuery.isFetchingNextPage}
            error={swapQuery.error}
            emptyMessage="Aucune demande d'échange"
          />
        </TabsContent>

        {/* Compétences tab */}
        <TabsContent value="competences">
          <SkillsTab search={search} />
        </TabsContent>

        {/* Absences tab */}
        <TabsContent value="absences">
          <AbsencesTab search={search} />
        </TabsContent>

        {/* Heures tab */}
        <TabsContent value="heures">
          <HoursTab search={search} />
        </TabsContent>
      </Tabs>

      {/* Dialogs */}
      <CreatePositionDialog
        open={showCreatePosition}
        onClose={() => setShowCreatePosition(false)}
      />
      <CreateAvailabilityDialog
        open={showCreateAvailability}
        onClose={() => setShowCreateAvailability(false)}
      />
    </div>
  );
}
