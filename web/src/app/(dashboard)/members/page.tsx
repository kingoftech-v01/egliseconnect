'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Plus,
  Search,
  Users,
  Home,
  UsersRound,
  BookUser,
  Cake,
  MapPin,
  X,
  UserPlus,
  Calendar,
  Phone,
  Mail,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Avatar } from '@/components/ui/avatar';
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
  useInfiniteMembers,
  useInfiniteFamilies,
  useInfiniteGroups,
  useCreateFamily,
  useCreateGroup,
  useBirthdays,
  useDirectory,
} from '@/hooks/use-members';
import { MEMBERSHIP_STATUS_LABELS, ROLE_LABELS } from '@egliseconnect/types';
import type { MemberListItem } from '@egliseconnect/types';

type AnyRecord = Record<string, unknown>;

const statusVariant: Record<string, 'default' | 'success' | 'warning' | 'secondary' | 'destructive'> = {
  active: 'success',
  registered: 'default',
  inactive: 'secondary',
  suspended: 'destructive',
};

// ─── Membres Tab ──────────────────────────────────────────────────────────────

function MembresTab() {
  const router = useRouter();
  const [search, setSearch] = useState('');

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteMembers(search);

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as (MemberListItem & AnyRecord)[];
  const totalCount = data?.pages[0]?.count;

  const columns: Column<MemberListItem & AnyRecord>[] = [
    {
      key: 'full_name',
      header: 'Membre',
      render: (item) => (
        <div className="flex items-center gap-3">
          <Avatar src={item.photo} fallback={item.full_name} size="sm" />
          <div>
            <p className="font-medium">{item.full_name}</p>
            <p className="text-xs text-white/40">{item.email}</p>
          </div>
        </div>
      ),
    },
    { key: 'member_number', header: 'No.' },
    {
      key: 'role',
      header: 'Rôle',
      render: (item) => (
        <Badge variant="outline">
          {ROLE_LABELS[item.role as keyof typeof ROLE_LABELS] || item.role}
        </Badge>
      ),
    },
    {
      key: 'membership_status',
      header: 'Statut',
      render: (item) => (
        <Badge variant={statusVariant[item.membership_status] || 'secondary'}>
          {MEMBERSHIP_STATUS_LABELS[item.membership_status as keyof typeof MEMBERSHIP_STATUS_LABELS] || item.membership_status}
        </Badge>
      ),
    },
    { key: 'phone', header: 'Téléphone' },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
          <Input
            placeholder="Rechercher un membre..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Button onClick={() => router.push('/members/new')}>
          <Plus className="h-4 w-4 mr-2" />
          Nouveau membre
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
        emptyMessage="Aucun membre trouvé"
        onRowClick={(item) => router.push(`/members/${item.id}`)}
      />
    </div>
  );
}

// ─── Familles Tab ────────────────────────────────────────────────────────────

function FamillesTab() {
  const { toast } = useToast();
  const [search, setSearch] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({ name: '', address: '', city: '', province: 'QC', postal_code: '' });

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteFamilies(search);
  const createFamily = useCreateFamily();

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as AnyRecord[];
  const totalCount = data?.pages[0]?.count;

  const columns: Column<AnyRecord>[] = [
    {
      key: 'name',
      header: 'Famille',
      render: (item) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-purple-600/10">
            <Home className="h-4 w-4 text-purple-400" />
          </div>
          <span className="font-medium text-white/90">{String(item.name ?? '—')}</span>
        </div>
      ),
    },
    {
      key: 'members_count',
      header: 'Membres',
      render: (item) => (
        <Badge variant="secondary">
          {String(item.members_count ?? (item.members as unknown[])?.length ?? 0)} membre(s)
        </Badge>
      ),
    },
    {
      key: 'city',
      header: 'Ville',
      render: (item) => (
        <div className="flex items-center gap-1.5 text-white/60">
          <MapPin className="h-3.5 w-3.5" />
          <span className="text-sm">{String(item.city ?? '—')}</span>
        </div>
      ),
    },
    {
      key: 'address',
      header: 'Adresse',
      render: (item) => <span className="text-sm text-white/50">{String(item.address ?? '—')}</span>,
    },
  ];

  function handleCreate() {
    if (!form.name.trim()) {
      toast({ type: 'error', title: 'Nom requis', description: 'Veuillez entrer le nom de famille.' });
      return;
    }
    createFamily.mutate(form, {
      onSuccess: () => {
        toast({ type: 'success', title: 'Famille créée', description: `La famille ${form.name} a été créée.` });
        setDialogOpen(false);
        setForm({ name: '', address: '', city: '', province: 'QC', postal_code: '' });
      },
      onError: () => {
        toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer la famille.' });
      },
    });
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
          <Input
            placeholder="Rechercher une famille..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nouvelle famille
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
        emptyMessage="Aucune famille trouvée"
      />

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogHeader>
          <DialogTitle>Nouvelle famille</DialogTitle>
          <DialogDescription>Ajouter une famille au répertoire</DialogDescription>
          <DialogClose onClose={() => setDialogOpen(false)} />
        </DialogHeader>
        <DialogContent>
          <div className="space-y-4">
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Nom de famille *</label>
              <Input
                placeholder="ex. Tremblay"
                value={form.name}
                onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Adresse</label>
              <Input
                placeholder="123 rue Principale"
                value={form.address}
                onChange={(e) => setForm((p) => ({ ...p, address: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-white/50 mb-1.5">Ville</label>
                <Input
                  placeholder="Montréal"
                  value={form.city}
                  onChange={(e) => setForm((p) => ({ ...p, city: e.target.value }))}
                />
              </div>
              <div>
                <label className="block text-xs text-white/50 mb-1.5">Code postal</label>
                <Input
                  placeholder="H2X 1Y4"
                  value={form.postal_code}
                  onChange={(e) => setForm((p) => ({ ...p, postal_code: e.target.value }))}
                />
              </div>
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setDialogOpen(false)}>Annuler</Button>
          <Button onClick={handleCreate} disabled={createFamily.isPending}>
            {createFamily.isPending ? 'Création...' : 'Créer'}
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Groupes Tab ─────────────────────────────────────────────────────────────

const GROUP_TYPE_LABELS: Record<string, string> = {
  cell: 'Cellule',
  ministry: 'Ministère',
  committee: 'Comité',
  class: 'Classe',
  other: 'Autre',
};

const DAY_LABELS: Record<string, string> = {
  monday: 'Lundi',
  tuesday: 'Mardi',
  wednesday: 'Mercredi',
  thursday: 'Jeudi',
  friday: 'Vendredi',
  saturday: 'Samedi',
  sunday: 'Dimanche',
};

function GroupesTab() {
  const { toast } = useToast();
  const [search, setSearch] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({
    name: '',
    group_type: 'cell',
    description: '',
    meeting_day: '',
    meeting_time: '',
    meeting_location: '',
  });

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteGroups(search);
  const createGroup = useCreateGroup();

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as AnyRecord[];
  const totalCount = data?.pages[0]?.count;

  const columns: Column<AnyRecord>[] = [
    {
      key: 'name',
      header: 'Groupe',
      render: (item) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-blue-600/10">
            <UsersRound className="h-4 w-4 text-blue-400" />
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
      key: 'group_type',
      header: 'Type',
      render: (item) => (
        <Badge variant="outline">
          {GROUP_TYPE_LABELS[item.group_type as string] ?? String(item.group_type ?? '—')}
        </Badge>
      ),
    },
    {
      key: 'leader',
      header: 'Leader',
      render: (item) => {
        const leader = item.leader as { full_name?: string } | null;
        return <span className="text-white/70">{leader?.full_name ?? String(item.leader_name ?? '—')}</span>;
      },
    },
    {
      key: 'meeting_day',
      header: 'Rencontre',
      render: (item) => {
        const day = DAY_LABELS[item.meeting_day as string] ?? (item.meeting_day as string);
        const time = item.meeting_time as string;
        if (!day && !time) return <span className="text-white/30">—</span>;
        return (
          <div className="text-sm">
            {day && <span className="text-white/70">{day}</span>}
            {time && <span className="text-white/40 ml-1">{time}</span>}
          </div>
        );
      },
    },
    {
      key: 'members_count',
      header: 'Membres',
      render: (item) => (
        <Badge variant="secondary">
          {String(item.members_count ?? 0)}
        </Badge>
      ),
    },
  ];

  function handleCreate() {
    if (!form.name.trim()) {
      toast({ type: 'error', title: 'Nom requis', description: 'Veuillez entrer le nom du groupe.' });
      return;
    }
    createGroup.mutate(form, {
      onSuccess: () => {
        toast({ type: 'success', title: 'Groupe créé', description: `Le groupe "${form.name}" a été créé.` });
        setDialogOpen(false);
        setForm({ name: '', group_type: 'cell', description: '', meeting_day: '', meeting_time: '', meeting_location: '' });
      },
      onError: () => {
        toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer le groupe.' });
      },
    });
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
          <Input
            placeholder="Rechercher un groupe..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nouveau groupe
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
        emptyMessage="Aucun groupe trouvé"
      />

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogHeader>
          <DialogTitle>Nouveau groupe</DialogTitle>
          <DialogDescription>Créer un groupe de cellule, ministère ou comité</DialogDescription>
          <DialogClose onClose={() => setDialogOpen(false)} />
        </DialogHeader>
        <DialogContent>
          <div className="space-y-4">
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Nom du groupe *</label>
              <Input
                placeholder="ex. Cellule Centre-Ville"
                value={form.name}
                onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Type</label>
              <Select
                value={form.group_type}
                onChange={(e) => setForm((p) => ({ ...p, group_type: e.target.value }))}
              >
                {Object.entries(GROUP_TYPE_LABELS).map(([v, l]) => (
                  <option key={v} value={v}>{l}</option>
                ))}
              </Select>
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
                <label className="block text-xs text-white/50 mb-1.5">Jour de rencontre</label>
                <Select
                  value={form.meeting_day}
                  onChange={(e) => setForm((p) => ({ ...p, meeting_day: e.target.value }))}
                >
                  <option value="">—</option>
                  {Object.entries(DAY_LABELS).map(([v, l]) => (
                    <option key={v} value={v}>{l}</option>
                  ))}
                </Select>
              </div>
              <div>
                <label className="block text-xs text-white/50 mb-1.5">Heure</label>
                <Input
                  type="time"
                  value={form.meeting_time}
                  onChange={(e) => setForm((p) => ({ ...p, meeting_time: e.target.value }))}
                />
              </div>
            </div>
            <div>
              <label className="block text-xs text-white/50 mb-1.5">Lieu</label>
              <Input
                placeholder="Adresse ou salle"
                value={form.meeting_location}
                onChange={(e) => setForm((p) => ({ ...p, meeting_location: e.target.value }))}
              />
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setDialogOpen(false)}>Annuler</Button>
          <Button onClick={handleCreate} disabled={createGroup.isPending}>
            {createGroup.isPending ? 'Création...' : 'Créer'}
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Répertoire Tab ──────────────────────────────────────────────────────────

function RepertoireTab() {
  const [search, setSearch] = useState('');
  const { data, isLoading } = useDirectory(search);

  const members = ((data?.results ?? []) as AnyRecord[]);

  return (
    <div className="space-y-4">
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
        <Input
          placeholder="Rechercher dans le répertoire..."
          className="pl-9"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-white/[0.05] rounded-2xl border border-white/[0.08] p-5 animate-pulse">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-full bg-white/[0.06]" />
                <div className="flex-1">
                  <div className="h-4 bg-white/[0.06] rounded w-2/3 mb-1" />
                  <div className="h-3 bg-white/[0.06] rounded w-1/2" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : members.length === 0 ? (
        <div className="rounded-2xl bg-white/[0.05] border border-white/[0.08] p-12 text-center">
          <BookUser className="h-10 w-10 text-white/20 mx-auto mb-3" />
          <p className="text-white/40">Aucun résultat dans le répertoire</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {members.map((member, idx) => (
            <div
              key={(member.id as string) ?? idx}
              className="bg-white/[0.05] backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 hover:bg-white/[0.08] hover:border-purple-500/30 transition-all"
            >
              <div className="flex items-center gap-3 mb-3">
                <Avatar
                  src={member.photo as string | undefined}
                  fallback={String(member.full_name ?? '')}
                  size="md"
                />
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-white/90 truncate">{String(member.full_name ?? '—')}</p>
                  {!!member.role && (
                    <Badge variant="outline" className="text-[10px] mt-0.5">
                      {ROLE_LABELS[member.role as keyof typeof ROLE_LABELS] ?? String(member.role)}
                    </Badge>
                  )}
                </div>
              </div>
              <div className="space-y-1.5">
                {!!member.email && (
                  <div className="flex items-center gap-2 text-sm text-white/50">
                    <Mail className="h-3.5 w-3.5" />
                    <span className="truncate">{String(member.email)}</span>
                  </div>
                )}
                {!!member.phone && (
                  <div className="flex items-center gap-2 text-sm text-white/50">
                    <Phone className="h-3.5 w-3.5" />
                    <span>{String(member.phone)}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Anniversaires Tab ──────────────────────────────────────────────────────

function AnniversairesTab() {
  const [period, setPeriod] = useState<'today' | 'week' | 'month'>('month');
  const { data, isLoading } = useBirthdays(period);

  const members = ((data?.results ?? []) as AnyRecord[]);

  const periodLabels = {
    today: "Aujourd'hui",
    week: 'Cette semaine',
    month: 'Ce mois-ci',
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        {(['today', 'week', 'month'] as const).map((p) => (
          <Button
            key={p}
            variant={period === p ? 'default' : 'outline'}
            size="sm"
            onClick={() => setPeriod(p)}
          >
            {periodLabels[p]}
          </Button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="bg-white/[0.05] rounded-xl border border-white/[0.08] p-4 animate-pulse">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-white/[0.06]" />
                <div className="flex-1">
                  <div className="h-4 bg-white/[0.06] rounded w-1/3 mb-1" />
                  <div className="h-3 bg-white/[0.06] rounded w-1/4" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : members.length === 0 ? (
        <div className="rounded-2xl bg-white/[0.05] border border-white/[0.08] p-12 text-center">
          <Cake className="h-10 w-10 text-white/20 mx-auto mb-3" />
          <p className="text-white/40">Aucun anniversaire {periodLabels[period].toLowerCase()}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {members.map((member, idx) => {
            const birthDate = member.birth_date as string | undefined;
            const formattedDate = birthDate
              ? new Date(birthDate).toLocaleDateString('fr-CA', { month: 'long', day: 'numeric' })
              : '—';
            const age = birthDate
              ? new Date().getFullYear() - new Date(birthDate).getFullYear()
              : null;

            return (
              <div
                key={(member.id as string) ?? idx}
                className="bg-white/[0.05] backdrop-blur-xl border border-white/[0.08] rounded-xl p-4 flex items-center gap-4 hover:bg-white/[0.08] transition-colors"
              >
                <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20">
                  <Cake className="h-5 w-5 text-amber-400" />
                </div>
                <Avatar
                  src={member.photo as string | undefined}
                  fallback={String(member.full_name ?? '')}
                  size="sm"
                />
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-white/90">{String(member.full_name ?? '—')}</p>
                  <div className="flex items-center gap-2 text-xs text-white/40">
                    <Calendar className="h-3 w-3" />
                    <span>{formattedDate}</span>
                    {age !== null && <span>({age} ans)</span>}
                  </div>
                </div>
                {!!member.phone && (
                  <div className="text-xs text-white/40 flex items-center gap-1">
                    <Phone className="h-3 w-3" />
                    {String(member.phone)}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ─── Main Page ──────────────────────────────────────────────────────────────

export default function MembersPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white/90">Membres</h1>
        <p className="text-white/40 text-sm mt-0.5">
          Gérer les membres, familles et groupes de votre église
        </p>
      </div>

      <Tabs defaultValue="membres">
        <TabsList className="flex-wrap gap-1 h-auto">
          <TabsTrigger value="membres">
            <Users className="h-3.5 w-3.5 mr-1.5 inline" />
            Membres
          </TabsTrigger>
          <TabsTrigger value="familles">
            <Home className="h-3.5 w-3.5 mr-1.5 inline" />
            Familles
          </TabsTrigger>
          <TabsTrigger value="groupes">
            <UsersRound className="h-3.5 w-3.5 mr-1.5 inline" />
            Groupes
          </TabsTrigger>
          <TabsTrigger value="repertoire">
            <BookUser className="h-3.5 w-3.5 mr-1.5 inline" />
            Répertoire
          </TabsTrigger>
          <TabsTrigger value="anniversaires">
            <Cake className="h-3.5 w-3.5 mr-1.5 inline" />
            Anniversaires
          </TabsTrigger>
        </TabsList>

        <TabsContent value="membres">
          <MembresTab />
        </TabsContent>
        <TabsContent value="familles">
          <FamillesTab />
        </TabsContent>
        <TabsContent value="groupes">
          <GroupesTab />
        </TabsContent>
        <TabsContent value="repertoire">
          <RepertoireTab />
        </TabsContent>
        <TabsContent value="anniversaires">
          <AnniversairesTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
