'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Plus,
  Search,
  Calendar as CalendarIcon,
  DoorOpen,
  LayoutTemplate,
  MapPin,
  Users,
  Clock,
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
  useInfiniteEvents,
  useInfiniteRooms,
  useCreateRoom,
  useInfiniteRoomBookings,
  useCreateRoomBooking,
  useInfiniteEventTemplates,
  useCreateEventTemplate,
  useRooms,
} from '@/hooks/use-events';
import { formatDate } from '@egliseconnect/utils';
import type { EventListItem } from '@egliseconnect/types';

type AnyRecord = Record<string, unknown>;

const eventTypeLabels: Record<string, string> = {
  worship: 'Culte',
  group: 'Groupe',
  meal: 'Repas',
  special: 'Spécial',
  meeting: 'Réunion',
  training: 'Formation',
  outreach: 'Évangélisation',
  other: 'Autre',
};

// ─── Events Tab ─────────────────────────────────────────────────────────────

function EventsTab() {
  const router = useRouter();
  const [search, setSearch] = useState('');

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteEvents(search);

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as (EventListItem & AnyRecord)[];
  const totalCount = data?.pages[0]?.count;

  const columns: Column<EventListItem & AnyRecord>[] = [
    {
      key: 'title',
      header: 'Événement',
      render: (item) => (
        <div>
          <p className="font-medium text-white/90">{item.title}</p>
          <p className="text-xs text-white/40">{item.location || 'Lieu non défini'}</p>
        </div>
      ),
    },
    {
      key: 'event_type',
      header: 'Type',
      render: (item) => (
        <Badge variant="outline">{eventTypeLabels[item.event_type] || item.event_type}</Badge>
      ),
    },
    {
      key: 'start_date',
      header: 'Date',
      render: (item) => formatDate(item.start_date, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
    },
    {
      key: 'attendee_count',
      header: 'Inscrits',
      render: (item) => (
        <span>
          {item.attendee_count}
          {item.max_capacity ? ` / ${item.max_capacity}` : ''}
        </span>
      ),
    },
    {
      key: 'is_published',
      header: 'Statut',
      render: (item) => (
        <Badge variant={item.is_published !== false ? 'success' : 'secondary'}>
          {item.is_published !== false ? 'Publié' : 'Brouillon'}
        </Badge>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
          <Input
            placeholder="Rechercher un événement..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Button variant="outline" onClick={() => router.push('/events/calendar')}>
          <CalendarIcon className="h-4 w-4 mr-2" />
          Calendrier
        </Button>
        <Button onClick={() => router.push('/events/new')}>
          <Plus className="h-4 w-4 mr-2" />
          Nouvel événement
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
        emptyMessage="Aucun événement trouvé"
        onRowClick={(item) => router.push(`/events/${item.id}`)}
      />
    </div>
  );
}

// ─── Rooms Tab ──────────────────────────────────────────────────────────────

function RoomsTab() {
  const { toast } = useToast();
  const [search, setSearch] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({ name: '', capacity: '', location: '', description: '' });

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteRooms(search);
  const createRoom = useCreateRoom();

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as AnyRecord[];
  const totalCount = data?.pages[0]?.count;

  const columns: Column<AnyRecord>[] = [
    {
      key: 'name',
      header: 'Salle',
      render: (item) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-blue-600/10">
            <DoorOpen className="h-4 w-4 text-blue-400" />
          </div>
          <div>
            <p className="font-medium text-white/90">{String(item.name ?? '—')}</p>
            {!!item.location && (
              <p className="text-xs text-white/40">{String(item.location)}</p>
            )}
          </div>
        </div>
      ),
    },
    {
      key: 'capacity',
      header: 'Capacité',
      render: (item) => (
        <div className="flex items-center gap-1.5 text-white/70">
          <Users className="h-3.5 w-3.5" />
          <span>{String(item.capacity ?? '—')} places</span>
        </div>
      ),
    },
    {
      key: 'is_available',
      header: 'Disponibilité',
      render: (item) => (
        <Badge variant={item.is_available !== false ? 'success' : 'warning'}>
          {item.is_available !== false ? 'Disponible' : 'Occupée'}
        </Badge>
      ),
    },
    {
      key: 'equipment',
      header: 'Équipement',
      render: (item) => {
        const equip = item.equipment as string | string[] | undefined;
        if (!equip) return <span className="text-white/30">—</span>;
        const text = Array.isArray(equip) ? equip.join(', ') : String(equip);
        return <span className="text-xs text-white/50 truncate max-w-xs block">{text}</span>;
      },
    },
  ];

  function handleCreate() {
    if (!form.name.trim()) {
      toast({ type: 'error', title: 'Nom requis', description: 'Veuillez entrer le nom de la salle.' });
      return;
    }
    createRoom.mutate(
      { name: form.name, capacity: form.capacity ? parseInt(form.capacity) : undefined, location: form.location || undefined, description: form.description || undefined },
      {
        onSuccess: () => {
          toast({ type: 'success', title: 'Salle créée', description: `La salle "${form.name}" a été créée.` });
          setDialogOpen(false);
          setForm({ name: '', capacity: '', location: '', description: '' });
        },
        onError: () => {
          toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer la salle.' });
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
            placeholder="Rechercher une salle..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nouvelle salle
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
        emptyMessage="Aucune salle trouvée"
      />

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogHeader>
          <DialogTitle>Nouvelle salle</DialogTitle>
          <DialogDescription>Ajouter une salle au système de réservation</DialogDescription>
          <DialogClose onClose={() => setDialogOpen(false)} />
        </DialogHeader>
        <DialogContent>
          <div className="space-y-4">
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Nom *</label>
              <Input
                placeholder="ex. Salle principale"
                value={form.name}
                onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-white/50 mb-1.5">Capacité</label>
                <Input
                  type="number"
                  min="1"
                  placeholder="150"
                  value={form.capacity}
                  onChange={(e) => setForm((p) => ({ ...p, capacity: e.target.value }))}
                />
              </div>
              <div>
                <label className="block text-xs text-white/50 mb-1.5">Emplacement</label>
                <Input
                  placeholder="Bâtiment A, 2e étage"
                  value={form.location}
                  onChange={(e) => setForm((p) => ({ ...p, location: e.target.value }))}
                />
              </div>
            </div>
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Description</label>
              <Input
                placeholder="Équipement disponible, notes..."
                value={form.description}
                onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
              />
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setDialogOpen(false)}>Annuler</Button>
          <Button onClick={handleCreate} disabled={createRoom.isPending}>
            {createRoom.isPending ? 'Création...' : 'Créer'}
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Bookings Tab ───────────────────────────────────────────────────────────

function BookingsTab() {
  const { toast } = useToast();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({ room: '', title: '', start_date: '', end_date: '' });
  const { data: roomsData } = useRooms();
  const rooms = ((roomsData?.results ?? []) as AnyRecord[]);

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteRoomBookings();
  const createBooking = useCreateRoomBooking();

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as AnyRecord[];
  const totalCount = data?.pages[0]?.count;

  const statusMap: Record<string, { variant: 'success' | 'warning' | 'destructive' | 'secondary'; label: string }> = {
    confirmed: { variant: 'success', label: 'Confirmée' },
    pending: { variant: 'warning', label: 'En attente' },
    cancelled: { variant: 'destructive', label: 'Annulée' },
  };

  const columns: Column<AnyRecord>[] = [
    {
      key: 'title',
      header: 'Réservation',
      render: (item) => <span className="font-medium text-white/90">{String(item.title ?? item.event_name ?? '—')}</span>,
    },
    {
      key: 'room',
      header: 'Salle',
      render: (item) => {
        const room = item.room as { name?: string } | null;
        return (
          <div className="flex items-center gap-1.5">
            <DoorOpen className="h-3.5 w-3.5 text-blue-400" />
            <span className="text-white/70">{room?.name ?? String(item.room_name ?? '—')}</span>
          </div>
        );
      },
    },
    {
      key: 'start_date',
      header: 'Début',
      render: (item) =>
        item.start_date
          ? formatDate(item.start_date as string, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
          : '—',
    },
    {
      key: 'end_date',
      header: 'Fin',
      render: (item) =>
        item.end_date
          ? formatDate(item.end_date as string, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
          : '—',
    },
    {
      key: 'status',
      header: 'Statut',
      render: (item) => {
        const s = statusMap[(item.status as string) ?? 'pending'] ?? { variant: 'secondary' as const, label: String(item.status ?? '—') };
        return <Badge variant={s.variant}>{s.label}</Badge>;
      },
    },
  ];

  function handleCreate() {
    if (!form.room || !form.title.trim() || !form.start_date || !form.end_date) {
      toast({ type: 'error', title: 'Champs requis', description: 'Veuillez remplir tous les champs obligatoires.' });
      return;
    }
    createBooking.mutate(
      { room: form.room, title: form.title, start_date: form.start_date, end_date: form.end_date },
      {
        onSuccess: () => {
          toast({ type: 'success', title: 'Réservation créée', description: 'La réservation a été enregistrée.' });
          setDialogOpen(false);
          setForm({ room: '', title: '', start_date: '', end_date: '' });
        },
        onError: () => {
          toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer la réservation.' });
        },
      },
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nouvelle réservation
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
        emptyMessage="Aucune réservation trouvée"
      />

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogHeader>
          <DialogTitle>Nouvelle réservation</DialogTitle>
          <DialogDescription>Réserver une salle pour un événement</DialogDescription>
          <DialogClose onClose={() => setDialogOpen(false)} />
        </DialogHeader>
        <DialogContent>
          <div className="space-y-4">
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Titre *</label>
              <Input
                placeholder="ex. Réunion du conseil"
                value={form.title}
                onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Salle *</label>
              <Select
                value={form.room}
                onChange={(e) => setForm((p) => ({ ...p, room: e.target.value }))}
              >
                <option value="">Sélectionner une salle</option>
                {rooms.map((r) => (
                  <option key={r.id as string} value={r.id as string}>
                    {String(r.name)} {r.capacity ? `(${r.capacity} places)` : ''}
                  </option>
                ))}
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-white/50 mb-1.5">Début *</label>
                <Input
                  type="datetime-local"
                  value={form.start_date}
                  onChange={(e) => setForm((p) => ({ ...p, start_date: e.target.value }))}
                />
              </div>
              <div>
                <label className="block text-xs text-white/50 mb-1.5">Fin *</label>
                <Input
                  type="datetime-local"
                  value={form.end_date}
                  onChange={(e) => setForm((p) => ({ ...p, end_date: e.target.value }))}
                />
              </div>
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setDialogOpen(false)}>Annuler</Button>
          <Button onClick={handleCreate} disabled={createBooking.isPending}>
            {createBooking.isPending ? 'Création...' : 'Réserver'}
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Templates Tab ──────────────────────────────────────────────────────────

function TemplatesTab() {
  const { toast } = useToast();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({ name: '', event_type: 'worship', description: '', default_duration: '60' });

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteEventTemplates();
  const createTemplate = useCreateEventTemplate();

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as AnyRecord[];
  const totalCount = data?.pages[0]?.count;

  const columns: Column<AnyRecord>[] = [
    {
      key: 'name',
      header: 'Modèle',
      render: (item) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-purple-600/10">
            <LayoutTemplate className="h-4 w-4 text-purple-400" />
          </div>
          <div>
            <p className="font-medium text-white/90">{String(item.name ?? '—')}</p>
            {!!item.description && (
              <p className="text-xs text-white/40 truncate max-w-xs">{String(item.description)}</p>
            )}
          </div>
        </div>
      ),
    },
    {
      key: 'event_type',
      header: 'Type',
      render: (item) => (
        <Badge variant="outline">
          {eventTypeLabels[item.event_type as string] ?? String(item.event_type ?? '—')}
        </Badge>
      ),
    },
    {
      key: 'default_duration',
      header: 'Durée',
      render: (item) => {
        const mins = Number(item.default_duration ?? item.duration_minutes ?? 0);
        if (!mins) return <span className="text-white/30">—</span>;
        return (
          <div className="flex items-center gap-1.5 text-white/60">
            <Clock className="h-3.5 w-3.5" />
            <span>{mins >= 60 ? `${Math.floor(mins / 60)}h${mins % 60 ? String(mins % 60).padStart(2, '0') : ''}` : `${mins} min`}</span>
          </div>
        );
      },
    },
    {
      key: 'location',
      header: 'Lieu par défaut',
      render: (item) => {
        if (!item.default_location && !item.location) return <span className="text-white/30">—</span>;
        return (
          <div className="flex items-center gap-1.5 text-white/50">
            <MapPin className="h-3.5 w-3.5" />
            <span className="text-sm">{String(item.default_location ?? item.location)}</span>
          </div>
        );
      },
    },
  ];

  function handleCreate() {
    if (!form.name.trim()) {
      toast({ type: 'error', title: 'Nom requis', description: 'Veuillez entrer le nom du modèle.' });
      return;
    }
    createTemplate.mutate(
      {
        name: form.name,
        event_type: form.event_type,
        description: form.description || undefined,
        default_duration: form.default_duration ? parseInt(form.default_duration) : undefined,
      },
      {
        onSuccess: () => {
          toast({ type: 'success', title: 'Modèle créé', description: `Le modèle "${form.name}" a été créé.` });
          setDialogOpen(false);
          setForm({ name: '', event_type: 'worship', description: '', default_duration: '60' });
        },
        onError: () => {
          toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer le modèle.' });
        },
      },
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nouveau modèle
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
        emptyMessage="Aucun modèle d'événement trouvé"
      />

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogHeader>
          <DialogTitle>Nouveau modèle d&apos;événement</DialogTitle>
          <DialogDescription>Créer un modèle réutilisable pour vos événements</DialogDescription>
          <DialogClose onClose={() => setDialogOpen(false)} />
        </DialogHeader>
        <DialogContent>
          <div className="space-y-4">
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Nom *</label>
              <Input
                placeholder="ex. Culte dominical"
                value={form.name}
                onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Type</label>
              <Select
                value={form.event_type}
                onChange={(e) => setForm((p) => ({ ...p, event_type: e.target.value }))}
              >
                {Object.entries(eventTypeLabels).map(([v, l]) => (
                  <option key={v} value={v}>{l}</option>
                ))}
              </Select>
            </div>
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Durée par défaut (minutes)</label>
              <Input
                type="number"
                min="15"
                step="15"
                placeholder="60"
                value={form.default_duration}
                onChange={(e) => setForm((p) => ({ ...p, default_duration: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Description</label>
              <Input
                placeholder="Détails du modèle..."
                value={form.description}
                onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
              />
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setDialogOpen(false)}>Annuler</Button>
          <Button onClick={handleCreate} disabled={createTemplate.isPending}>
            {createTemplate.isPending ? 'Création...' : 'Créer'}
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Main Page ──────────────────────────────────────────────────────────────

export default function EventsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white/90">Événements</h1>
        <p className="text-white/40 text-sm mt-0.5">
          Gérer les événements, salles et réservations
        </p>
      </div>

      <Tabs defaultValue="evenements">
        <TabsList className="flex-wrap gap-1 h-auto">
          <TabsTrigger value="evenements">
            <CalendarIcon className="h-3.5 w-3.5 mr-1.5 inline" />
            Événements
          </TabsTrigger>
          <TabsTrigger value="salles">
            <DoorOpen className="h-3.5 w-3.5 mr-1.5 inline" />
            Salles
          </TabsTrigger>
          <TabsTrigger value="reservations">
            <Clock className="h-3.5 w-3.5 mr-1.5 inline" />
            Réservations
          </TabsTrigger>
          <TabsTrigger value="modeles">
            <LayoutTemplate className="h-3.5 w-3.5 mr-1.5 inline" />
            Modèles
          </TabsTrigger>
        </TabsList>

        <TabsContent value="evenements"><EventsTab /></TabsContent>
        <TabsContent value="salles"><RoomsTab /></TabsContent>
        <TabsContent value="reservations"><BookingsTab /></TabsContent>
        <TabsContent value="modeles"><TemplatesTab /></TabsContent>
      </Tabs>
    </div>
  );
}
