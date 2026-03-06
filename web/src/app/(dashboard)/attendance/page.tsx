'use client';

import { useState } from 'react';
import {
  QrCode,
  Users,
  AlertTriangle,
  UserPlus,
  BarChart3,
  Camera,
  Search,
  Plus,
  Check,
  Clock,
  TrendingUp,
  Flame,
  CalendarDays,
  Baby,
  MapPin as MapPinIcon,
  Wifi,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { InfiniteScrollTable } from '@/components/ui/infinite-scroll-table';
import type { Column } from '@/components/ui/data-table';
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
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/components/ui/toast';
import {
  useAttendanceSessions,
  useCreateSession,
  useCheckIn,
  useFamilyCheckIn,
  useAbsenceAlerts,
  useAcknowledgeAlert,
  useVisitors,
  useCreateVisitor,
  useAttendanceTrends,
  useAttendanceAverageByType,
  useInfiniteAttendanceSessions,
  useInfiniteAbsenceAlerts,
  useInfiniteVisitors,
  useRecentCheckIns,
  useInfiniteChildCheckIns,
  useCreateChildCheckIn,
  useChildCheckOut,
  useInfiniteGeoFences,
  useCreateGeoFence,
  useInfiniteNFCTags,
  useCreateNFCTag,
} from '@/hooks/use-attendance';

// ─── Type definitions ────────────────────────────────────────────────────────

interface AttendanceSession extends Record<string, unknown> {
  id: string;
  name: string;
  session_type: string;
  date: string;
  attendance_count: number;
  status: string;
  notes?: string;
}

interface AbsenceAlert extends Record<string, unknown> {
  id: string;
  member_name: string;
  consecutive_absences: number;
  last_seen: string;
  acknowledged: boolean;
}

interface Visitor extends Record<string, unknown> {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  source: string;
  follow_up_assigned?: string;
  date: string;
  notes?: string;
}

interface TrendWeek extends Record<string, unknown> {
  week: string;
  count: number;
  label: string;
}

interface AverageByType extends Record<string, unknown> {
  type: string;
  average: number;
  total_sessions: number;
}

interface RecentCheckIn {
  id: string;
  member_name: string;
  time: string;
  status: 'present' | 'absent' | 'late';
}

// ─── Labels & Helpers ────────────────────────────────────────────────────────

const sessionTypeLabels: Record<string, string> = {
  culte: 'Culte',
  worship: 'Culte',
  event: 'Événement',
  lesson: 'Enseignement',
  group: 'Groupe',
  prayer: 'Prière',
  other: 'Autre',
};

const sessionStatusLabels: Record<string, string> = {
  active: 'Actif',
  closed: 'Terminé',
  upcoming: 'À venir',
  cancelled: 'Annulé',
};

const sessionStatusVariant: Record<string, 'success' | 'default' | 'secondary' | 'destructive' | 'warning'> = {
  active: 'success',
  closed: 'secondary',
  upcoming: 'default',
  cancelled: 'destructive',
};

const sourceLabels: Record<string, string> = {
  invitation: 'Invitation',
  social_media: 'Réseaux sociaux',
  website: 'Site web',
  walk_in: 'Passage spontané',
  referral: 'Recommandation',
  other: 'Autre',
};

function formatTime(iso: string) {
  try {
    return new Date(iso).toLocaleTimeString('fr-CA', { hour: '2-digit', minute: '2-digit' });
  } catch {
    return iso;
  }
}

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleDateString('fr-CA', { year: 'numeric', month: 'short', day: 'numeric' });
  } catch {
    return iso;
  }
}

// ─── Stat Card ───────────────────────────────────────────────────────────────

function StatCard({
  icon: Icon,
  label,
  value,
  sub,
  accent,
  loading,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  sub?: string;
  accent: string;
  loading?: boolean;
}) {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-xs text-white/50 font-medium uppercase tracking-wider">{label}</p>
            {loading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <p className="text-3xl font-bold text-white">{value}</p>
            )}
            {sub && <p className="text-xs text-white/40">{sub}</p>}
          </div>
          <div className={`p-3 rounded-xl ${accent}`}>
            <Icon className="h-5 w-5 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Recent Check-Ins Panel ──────────────────────────────────────────────────

function RecentCheckInsPanel() {
  const { data, isLoading } = useRecentCheckIns();
  const records = ((data?.results ?? []) as Record<string, unknown>[]);

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base">
            <Clock className="h-4 w-4 text-white/50" />
            Présences récentes
          </CardTitle>
          <Badge variant="secondary">{data?.count ?? 0} enregistrées</Badge>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading ? (
          <div className="space-y-0">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="flex items-center gap-3 px-6 py-3 border-b border-white/[0.04] last:border-0">
                <Skeleton className="h-8 w-8 rounded-full" />
                <div className="flex-1 space-y-1">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-3 w-16" />
                </div>
              </div>
            ))}
          </div>
        ) : records.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-sm text-white/40">Aucune présence enregistrée</p>
          </div>
        ) : (
          <ul className="divide-y divide-white/[0.04]">
            {records.map((item) => {
              const memberObj = item.member as { full_name?: string } | null;
              const name = memberObj?.full_name ?? (item.member_name as string) ?? 'Inconnu';
              const time = (item.check_in_time ?? item.time ?? '') as string;
              const status = (item.status as string) ?? 'present';
              const cfg = checkInStatusConfig[status as keyof typeof checkInStatusConfig] ?? checkInStatusConfig.present;
              return (
                <li key={item.id as string} className="flex items-center justify-between px-6 py-3 hover:bg-white/[0.02] transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full bg-purple-500/20 flex items-center justify-center text-xs font-bold text-purple-300">
                      {name.charAt(0)}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white/90">{name}</p>
                      {time && (
                        <p className="text-xs text-white/40 flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {formatTime(time)}
                        </p>
                      )}
                    </div>
                  </div>
                  <Badge variant={cfg.variant}>{cfg.label}</Badge>
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

// ─── Sessions Tab ────────────────────────────────────────────────────────────

function SessionsTab() {
  const { toast } = useToast();
  const [search, setSearch] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    name: '',
    session_type: 'culte',
    date: '',
    notes: '',
  });

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteAttendanceSessions(search);
  const createSession = useCreateSession();

  const sessions = (data?.pages.flatMap((p) => p.results) ?? []) as AttendanceSession[];
  const totalCount = data?.pages[0]?.count;

  const columns: Column<AttendanceSession>[] = [
    {
      key: 'name',
      header: 'Session',
      render: (item) => (
        <div>
          <p className="font-medium text-white/90">{item.name}</p>
          <p className="text-xs text-white/40">{formatDate(item.date)}</p>
        </div>
      ),
    },
    {
      key: 'session_type',
      header: 'Type',
      render: (item) => (
        <Badge variant="outline">
          {sessionTypeLabels[item.session_type] ?? item.session_type}
        </Badge>
      ),
    },
    {
      key: 'attendance_count',
      header: 'Présences',
      render: (item) => (
        <div className="flex items-center gap-1.5">
          <Users className="h-3.5 w-3.5 text-white/40" />
          <span className="font-medium">{item.attendance_count ?? 0}</span>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Statut',
      render: (item) => (
        <Badge variant={sessionStatusVariant[item.status] ?? 'secondary'}>
          {sessionStatusLabels[item.status] ?? item.status}
        </Badge>
      ),
    },
  ];

  async function handleCreate() {
    if (!form.name || !form.date) {
      toast({ type: 'warning', title: 'Champs requis', description: 'Le nom et la date sont obligatoires.' });
      return;
    }
    try {
      await createSession.mutateAsync(form);
      toast({ type: 'success', title: 'Session créée', description: `"${form.name}" a été créée avec succès.` });
      setShowCreate(false);
      setForm({ name: '', session_type: 'culte', date: '', notes: '' });
    } catch {
      toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer la session.' });
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/40" />
          <Input
            placeholder="Rechercher une session..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nouvelle session
        </Button>
      </div>

      <InfiniteScrollTable
        columns={columns}
        data={sessions}
        totalCount={totalCount}
        isLoading={isLoading}
        fetchNextPage={fetchNextPage}
        hasNextPage={hasNextPage}
        isFetchingNextPage={isFetchingNextPage}
        error={error}
        emptyMessage="Aucune session trouvée"
      />

      <Dialog open={showCreate} onClose={() => setShowCreate(false)}>
        <DialogHeader>
          <DialogTitle>Nouvelle session de présence</DialogTitle>
          <DialogDescription>Créez une nouvelle session pour enregistrer les présences.</DialogDescription>
          <DialogClose onClose={() => setShowCreate(false)} />
        </DialogHeader>
        <DialogContent>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1.5">Nom de la session *</label>
              <Input
                placeholder="ex. Culte du dimanche matin"
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1.5">Type *</label>
              <Select
                value={form.session_type}
                onChange={(e) => setForm((f) => ({ ...f, session_type: e.target.value }))}
              >
                <option value="culte">Culte</option>
                <option value="event">Événement</option>
                <option value="lesson">Enseignement</option>
                <option value="group">Groupe</option>
                <option value="prayer">Prière</option>
                <option value="other">Autre</option>
              </Select>
            </div>
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1.5">Date *</label>
              <Input
                type="datetime-local"
                value={form.date}
                onChange={(e) => setForm((f) => ({ ...f, date: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1.5">Notes</label>
              <Textarea
                placeholder="Notes optionnelles..."
                value={form.notes}
                onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
                rows={3}
              />
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setShowCreate(false)}>Annuler</Button>
          <Button onClick={handleCreate} disabled={createSession.isPending}>
            {createSession.isPending ? 'Création...' : 'Créer la session'}
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Scanner QR Tab ──────────────────────────────────────────────────────────

const checkInStatusConfig = {
  present: { label: 'Présent', variant: 'success' as const },
  late: { label: 'En retard', variant: 'warning' as const },
  absent: { label: 'Absent', variant: 'destructive' as const },
};

function ScannerTab() {
  const { toast } = useToast();
  const [memberSearch, setMemberSearch] = useState('');
  const [showFamilyDialog, setShowFamilyDialog] = useState(false);
  const [familyForm, setFamilyForm] = useState({ session_id: '', family_id: '', member_ids: '' });
  const [scanning, setScanning] = useState(false);

  const checkIn = useCheckIn();
  const familyCheckIn = useFamilyCheckIn();

  async function handleManualCheckIn() {
    if (!memberSearch.trim()) {
      toast({ type: 'warning', title: 'Recherche vide', description: 'Veuillez entrer un nom de membre.' });
      return;
    }
    toast({ type: 'info', title: 'Recherche en cours...', description: `Recherche de "${memberSearch}"` });
  }

  function handleScanToggle() {
    setScanning((s) => !s);
    if (!scanning) {
      toast({ type: 'info', title: 'Scanner activé', description: 'Pointez la caméra vers un code QR.' });
    }
  }

  async function handleFamilyCheckIn() {
    if (!familyForm.session_id || !familyForm.family_id) {
      toast({ type: 'warning', title: 'Champs requis', description: 'Session et famille sont obligatoires.' });
      return;
    }
    try {
      await familyCheckIn.mutateAsync({
        session_id: familyForm.session_id,
        family_id: familyForm.family_id,
        member_ids: familyForm.member_ids.split(',').map((s) => s.trim()).filter(Boolean),
      });
      toast({ type: 'success', title: 'Famille enregistrée', description: 'La famille a été enregistrée avec succès.' });
      setShowFamilyDialog(false);
    } catch {
      toast({ type: 'error', title: 'Erreur', description: 'Impossible d\'enregistrer la famille.' });
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Left: Scanner */}
      <div className="space-y-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <QrCode className="h-4 w-4 text-purple-400" />
              Scanner QR
            </CardTitle>
            <CardDescription>Scannez un code QR de membre pour enregistrer sa présence</CardDescription>
          </CardHeader>
          <CardContent>
            {/* QR scan area */}
            <div
              className={`relative rounded-2xl border-2 border-dashed transition-all duration-300 flex flex-col items-center justify-center py-14 gap-4 cursor-pointer
                ${scanning
                  ? 'border-purple-500/60 bg-purple-500/5 shadow-[0_0_30px_rgba(124,58,237,0.15)]'
                  : 'border-white/[0.12] bg-white/[0.02] hover:border-white/20 hover:bg-white/[0.04]'
                }`}
              onClick={handleScanToggle}
            >
              {scanning ? (
                <>
                  <div className="relative">
                    <div className="h-20 w-20 rounded-xl bg-purple-500/20 flex items-center justify-center">
                      <Camera className="h-10 w-10 text-purple-400" />
                    </div>
                    <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-emerald-400 animate-pulse" />
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-medium text-purple-300">Scanner actif</p>
                    <p className="text-xs text-white/40 mt-1">Pointez vers un code QR</p>
                  </div>
                  {/* Scanning animation corners */}
                  <div className="absolute top-4 left-4 h-8 w-8 border-t-2 border-l-2 border-purple-400 rounded-tl-lg" />
                  <div className="absolute top-4 right-4 h-8 w-8 border-t-2 border-r-2 border-purple-400 rounded-tr-lg" />
                  <div className="absolute bottom-4 left-4 h-8 w-8 border-b-2 border-l-2 border-purple-400 rounded-bl-lg" />
                  <div className="absolute bottom-4 right-4 h-8 w-8 border-b-2 border-r-2 border-purple-400 rounded-br-lg" />
                </>
              ) : (
                <>
                  <div className="h-20 w-20 rounded-xl bg-white/[0.04] flex items-center justify-center">
                    <QrCode className="h-10 w-10 text-white/30" />
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-medium text-white/60">Cliquez pour activer le scanner</p>
                    <p className="text-xs text-white/30 mt-1">Caméra requise</p>
                  </div>
                </>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Manual search */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Search className="h-4 w-4 text-white/50" />
              Recherche manuelle
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/40" />
                <Input
                  placeholder="Rechercher un membre par nom..."
                  className="pl-9"
                  value={memberSearch}
                  onChange={(e) => setMemberSearch(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleManualCheckIn()}
                />
              </div>
              <Button onClick={handleManualCheckIn} disabled={checkIn.isPending}>
                <Check className="h-4 w-4 mr-1.5" />
                Enregistrer
              </Button>
            </div>
            <Button
              variant="outline"
              className="w-full"
              onClick={() => setShowFamilyDialog(true)}
            >
              <Users className="h-4 w-4 mr-2" />
              Enregistrement familial
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Right: Recent check-ins */}
      <RecentCheckInsPanel />

      {/* Family check-in dialog */}
      <Dialog open={showFamilyDialog} onClose={() => setShowFamilyDialog(false)}>
        <DialogHeader>
          <DialogTitle>Enregistrement familial</DialogTitle>
          <DialogDescription>Enregistrez tous les membres d&apos;une famille en une seule action.</DialogDescription>
          <DialogClose onClose={() => setShowFamilyDialog(false)} />
        </DialogHeader>
        <DialogContent>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1.5">ID de la session *</label>
              <Input
                placeholder="Identifiant de la session active"
                value={familyForm.session_id}
                onChange={(e) => setFamilyForm((f) => ({ ...f, session_id: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1.5">ID de la famille *</label>
              <Input
                placeholder="Identifiant de la famille"
                value={familyForm.family_id}
                onChange={(e) => setFamilyForm((f) => ({ ...f, family_id: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1.5">IDs des membres</label>
              <Input
                placeholder="ID1, ID2, ID3 (séparés par virgule)"
                value={familyForm.member_ids}
                onChange={(e) => setFamilyForm((f) => ({ ...f, member_ids: e.target.value }))}
              />
              <p className="text-xs text-white/30 mt-1">Laissez vide pour enregistrer toute la famille</p>
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setShowFamilyDialog(false)}>Annuler</Button>
          <Button onClick={handleFamilyCheckIn} disabled={familyCheckIn.isPending}>
            {familyCheckIn.isPending ? 'Enregistrement...' : 'Enregistrer la famille'}
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Alertes Tab ─────────────────────────────────────────────────────────────

function AlertesTab() {
  const { toast } = useToast();

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteAbsenceAlerts();
  const acknowledgeAlert = useAcknowledgeAlert();

  const alerts = (data?.pages.flatMap((p) => p.results) ?? []) as AbsenceAlert[];
  const totalCount = data?.pages[0]?.count;

  async function handleAcknowledge(alertId: string, memberName: string) {
    try {
      await acknowledgeAlert.mutateAsync(alertId);
      toast({ type: 'success', title: 'Alerte acquittée', description: `L'alerte pour ${memberName} a été traitée.` });
    } catch {
      toast({ type: 'error', title: 'Erreur', description: 'Impossible d\'acquitter l\'alerte.' });
    }
  }

  const columns: Column<AbsenceAlert>[] = [
    {
      key: 'member_name',
      header: 'Membre',
      render: (item) => (
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-full bg-rose-500/20 flex items-center justify-center text-xs font-bold text-rose-300">
            {item.member_name?.charAt(0) ?? '?'}
          </div>
          <span className="font-medium text-white/90">{item.member_name}</span>
        </div>
      ),
    },
    {
      key: 'consecutive_absences',
      header: 'Absences consécutives',
      render: (item) => (
        <div className="flex items-center gap-1.5">
          <AlertTriangle className={`h-4 w-4 ${item.consecutive_absences >= 4 ? 'text-rose-400' : 'text-amber-400'}`} />
          <span className={`font-bold ${item.consecutive_absences >= 4 ? 'text-rose-400' : 'text-amber-400'}`}>
            {item.consecutive_absences} semaines
          </span>
        </div>
      ),
    },
    {
      key: 'last_seen',
      header: 'Dernière présence',
      render: (item) => (
        <span className="text-white/50">{item.last_seen ? formatDate(item.last_seen) : 'Inconnu'}</span>
      ),
    },
    {
      key: 'acknowledged',
      header: 'Statut',
      render: (item) => (
        item.acknowledged
          ? <Badge variant="success">Traité</Badge>
          : <Badge variant="warning">En attente</Badge>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (item) => (
        !item.acknowledged ? (
          <Button
            size="sm"
            variant="ghost"
            className="text-xs"
            onClick={(e) => { e.stopPropagation(); handleAcknowledge(item.id, item.member_name); }}
            disabled={acknowledgeAlert.isPending}
          >
            <Check className="h-3.5 w-3.5 mr-1" />
            Acquitter
          </Button>
        ) : null
      ),
    },
  ];

  return (
    <div className="space-y-4">
      {!isLoading && alerts.filter((a) => !a.acknowledged).length > 0 && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-amber-500/10 border border-amber-500/20">
          <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0" />
          <p className="text-sm text-amber-300">
            <span className="font-bold">{alerts.filter((a) => !a.acknowledged).length}</span> alerte(s) d&apos;absence nécessitent votre attention.
          </p>
        </div>
      )}
      <InfiniteScrollTable
        columns={columns}
        data={alerts}
        totalCount={totalCount}
        isLoading={isLoading}
        fetchNextPage={fetchNextPage}
        hasNextPage={hasNextPage}
        isFetchingNextPage={isFetchingNextPage}
        error={error}
        emptyMessage="Aucune alerte d'absence"
      />
    </div>
  );
}

// ─── Visiteurs Tab ───────────────────────────────────────────────────────────

function VisiteursTab() {
  const { toast } = useToast();
  const [search, setSearch] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    name: '',
    email: '',
    phone: '',
    source: 'walk_in',
    notes: '',
  });

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteVisitors(search);
  const createVisitor = useCreateVisitor();

  const visitors = (data?.pages.flatMap((p) => p.results) ?? []) as Visitor[];
  const totalCount = data?.pages[0]?.count;

  const columns: Column<Visitor>[] = [
    {
      key: 'name',
      header: 'Visiteur',
      render: (item) => (
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-full bg-blue-500/20 flex items-center justify-center text-xs font-bold text-blue-300">
            {item.name?.charAt(0) ?? '?'}
          </div>
          <div>
            <p className="font-medium text-white/90">{item.name}</p>
            {item.email && <p className="text-xs text-white/40">{item.email}</p>}
          </div>
        </div>
      ),
    },
    {
      key: 'phone',
      header: 'Téléphone',
      render: (item) => <span className="text-white/60">{item.phone || '—'}</span>,
    },
    {
      key: 'source',
      header: 'Source',
      render: (item) => (
        <Badge variant="outline">{sourceLabels[item.source] ?? item.source}</Badge>
      ),
    },
    {
      key: 'follow_up_assigned',
      header: 'Suivi',
      render: (item) => (
        item.follow_up_assigned
          ? <span className="text-white/70">{item.follow_up_assigned}</span>
          : <span className="text-white/30 italic text-xs">Non assigné</span>
      ),
    },
    {
      key: 'date',
      header: 'Date',
      render: (item) => <span className="text-white/50">{formatDate(item.date)}</span>,
    },
  ];

  async function handleCreate() {
    if (!form.name) {
      toast({ type: 'warning', title: 'Champ requis', description: 'Le nom du visiteur est obligatoire.' });
      return;
    }
    try {
      await createVisitor.mutateAsync(form);
      toast({ type: 'success', title: 'Visiteur ajouté', description: `${form.name} a été enregistré avec succès.` });
      setShowCreate(false);
      setForm({ name: '', email: '', phone: '', source: 'walk_in', notes: '' });
    } catch {
      toast({ type: 'error', title: 'Erreur', description: 'Impossible d\'ajouter le visiteur.' });
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/40" />
          <Input
            placeholder="Rechercher un visiteur..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <UserPlus className="h-4 w-4 mr-2" />
          Nouveau visiteur
        </Button>
      </div>

      <InfiniteScrollTable
        columns={columns}
        data={visitors}
        totalCount={totalCount}
        isLoading={isLoading}
        fetchNextPage={fetchNextPage}
        hasNextPage={hasNextPage}
        isFetchingNextPage={isFetchingNextPage}
        error={error}
        emptyMessage="Aucun visiteur enregistré"
      />

      <Dialog open={showCreate} onClose={() => setShowCreate(false)}>
        <DialogHeader>
          <DialogTitle>Nouveau visiteur</DialogTitle>
          <DialogDescription>Enregistrez un visiteur pour assurer un suivi personnalisé.</DialogDescription>
          <DialogClose onClose={() => setShowCreate(false)} />
        </DialogHeader>
        <DialogContent>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1.5">Nom complet *</label>
              <Input
                placeholder="Prénom Nom"
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-white/60 mb-1.5">Courriel</label>
                <Input
                  type="email"
                  placeholder="exemple@email.com"
                  value={form.email}
                  onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-white/60 mb-1.5">Téléphone</label>
                <Input
                  type="tel"
                  placeholder="514-000-0000"
                  value={form.phone}
                  onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1.5">Source</label>
              <Select
                value={form.source}
                onChange={(e) => setForm((f) => ({ ...f, source: e.target.value }))}
              >
                <option value="walk_in">Passage spontané</option>
                <option value="invitation">Invitation</option>
                <option value="social_media">Réseaux sociaux</option>
                <option value="website">Site web</option>
                <option value="referral">Recommandation</option>
                <option value="other">Autre</option>
              </Select>
            </div>
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1.5">Notes</label>
              <Textarea
                placeholder="Notes de suivi..."
                value={form.notes}
                onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
                rows={3}
              />
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setShowCreate(false)}>Annuler</Button>
          <Button onClick={handleCreate} disabled={createVisitor.isPending}>
            {createVisitor.isPending ? 'Enregistrement...' : 'Ajouter le visiteur'}
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Analytique Tab ──────────────────────────────────────────────────────────

const TYPE_LABELS: Record<string, string> = {
  culte: 'Culte',
  worship: 'Culte',
  event: 'Événement',
  lesson: 'Enseignement',
  group: 'Groupe',
  prayer: 'Prière',
};

const TYPE_COLORS: Record<string, string> = {
  culte: 'bg-purple-500',
  worship: 'bg-purple-500',
  event: 'bg-blue-500',
  lesson: 'bg-emerald-500',
  group: 'bg-amber-500',
  prayer: 'bg-rose-500',
};

const TYPE_ACCENTS: Record<string, string> = {
  culte: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
  worship: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
  event: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  lesson: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  group: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  prayer: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
};

function AnalytiqueTab() {
  const { data: trendsData, isLoading: trendsLoading } = useAttendanceTrends('weeks=12');
  const { data: avgData, isLoading: avgLoading } = useAttendanceAverageByType();

  const trends: TrendWeek[] = Array.isArray(trendsData)
    ? (trendsData as TrendWeek[])
    : [];

  const averages: AverageByType[] = Array.isArray(avgData)
    ? (avgData as AverageByType[])
    : [];

  const maxCount = Math.max(...trends.map((t) => t.count), 1);

  // Growth: compare last 6 weeks vs previous 6
  const half = Math.floor(trends.length / 2);
  const recent = trends.slice(half);
  const previous = trends.slice(0, half);
  const recentAvg = recent.length ? recent.reduce((s, t) => s + t.count, 0) / recent.length : 0;
  const previousAvg = previous.length ? previous.reduce((s, t) => s + t.count, 0) / previous.length : 0;
  const growthPct = previousAvg > 0 ? ((recentAvg - previousAvg) / previousAvg) * 100 : 0;

  return (
    <div className="space-y-6">
      {/* Trend chart */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-purple-400" />
            Tendance des présences — 12 dernières semaines
          </CardTitle>
          <CardDescription>Nombre de personnes présentes par semaine</CardDescription>
        </CardHeader>
        <CardContent>
          {trendsLoading ? (
            <div className="space-y-2">
              {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}
            </div>
          ) : trends.length === 0 ? (
            <div className="flex items-center justify-center h-48">
              <p className="text-white/40 text-sm">Aucune donnée de tendance disponible</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-end gap-2 h-48">
                {trends.map((week, i) => {
                  const heightPct = maxCount > 0 ? (week.count / maxCount) * 100 : 0;
                  return (
                    <div key={i} className="flex-1 flex flex-col items-center gap-1 group">
                      <div className="relative w-full flex items-end justify-center" style={{ height: '160px' }}>
                        <div
                          className="w-full rounded-t-lg bg-purple-500/70 hover:bg-purple-500 transition-all duration-300 relative group-hover:shadow-[0_0_12px_rgba(124,58,237,0.4)]"
                          style={{ height: `${heightPct}%` }}
                        >
                          <div className="absolute -top-7 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity bg-[#1a1145] border border-white/10 rounded-lg px-2 py-1 text-xs text-white whitespace-nowrap pointer-events-none z-10">
                            {week.count}
                          </div>
                        </div>
                      </div>
                      <span className="text-[10px] text-white/30">
                        {week.label || `S${i + 1}`}
                      </span>
                    </div>
                  );
                })}
              </div>
              <div className="flex items-center justify-between text-xs text-white/40 border-t border-white/[0.06] pt-3">
                <span>Il y a 12 semaines</span>
                <span>Aujourd&apos;hui</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Average by type */}
        <div className="lg:col-span-2">
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-blue-400" />
                Moyenne par type de session
              </CardTitle>
              <CardDescription>Présences moyennes selon le type d&apos;activité</CardDescription>
            </CardHeader>
            <CardContent>
              {avgLoading ? (
                <div className="space-y-3">
                  {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-14 w-full" />)}
                </div>
              ) : averages.length === 0 ? (
                <p className="text-white/40 text-sm text-center py-8">Aucune donnée disponible</p>
              ) : (
                <div className="space-y-4">
                  {averages.map((item) => {
                    const barPct = averages.length
                      ? (item.average / Math.max(...averages.map((a) => a.average), 1)) * 100
                      : 0;
                    const color = TYPE_COLORS[item.type] ?? 'bg-purple-500';
                    const accent = TYPE_ACCENTS[item.type] ?? 'text-purple-400 bg-purple-500/10 border-purple-500/20';
                    return (
                      <div key={item.type} className="space-y-1.5">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Badge className={`border ${accent}`}>
                              {TYPE_LABELS[item.type] ?? item.type}
                            </Badge>
                            <span className="text-xs text-white/40">{item.total_sessions} sessions</span>
                          </div>
                          <span className="text-sm font-bold text-white/90">{Math.round(item.average)} moy.</span>
                        </div>
                        <div className="h-2 w-full bg-white/[0.04] rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-700 ${color}`}
                            style={{ width: `${barPct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Growth comparison */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-emerald-400" />
              Croissance
            </CardTitle>
            <CardDescription>6 dernières semaines vs 6 précédentes</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="text-center py-4">
              <div
                className={`text-5xl font-bold mb-2 ${
                  growthPct >= 0 ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {growthPct >= 0 ? '+' : ''}{growthPct.toFixed(1)}%
              </div>
              <p className="text-xs text-white/40">variation de fréquentation</p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]">
                <span className="text-xs text-white/50">Période récente</span>
                <span className="text-sm font-bold text-white/90">{Math.round(recentAvg)} moy./sem.</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]">
                <span className="text-xs text-white/50">Période précédente</span>
                <span className="text-sm font-bold text-white/90">{Math.round(previousAvg)} moy./sem.</span>
              </div>
            </div>

            <div className={`flex items-center gap-2 p-3 rounded-xl border ${
              growthPct >= 0
                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                : 'bg-rose-500/10 border-rose-500/20 text-rose-400'
            }`}>
              <TrendingUp className="h-4 w-4 shrink-0" />
              <p className="text-xs font-medium">
                {growthPct >= 0
                  ? 'Tendance à la hausse'
                  : 'Tendance à la baisse'}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// ─── Child Check-Ins Tab ────────────────────────────────────────────────────

function ChildCheckInsTab() {
  const { toast } = useToast();
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ child_name: '', parent_name: '', session_id: '', allergies: '', notes: '' });
  const createCheckIn = useCreateChildCheckIn();
  const childCheckOut = useChildCheckOut();

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteChildCheckIns();
  const results = (data?.pages.flatMap((p) => p.results) ?? []) as (Record<string, unknown> & { id: string })[];
  const totalCount = data?.pages[0]?.count;

  async function handleCreate() {
    if (!form.child_name) {
      toast({ type: 'warning', title: 'Champ requis', description: 'Le nom de l\'enfant est obligatoire.' });
      return;
    }
    try {
      await createCheckIn.mutateAsync(form);
      toast({ type: 'success', title: 'Enfant enregistré', description: `${form.child_name} a été enregistré.` });
      setShowCreate(false);
      setForm({ child_name: '', parent_name: '', session_id: '', allergies: '', notes: '' });
    } catch {
      toast({ type: 'error', title: 'Erreur', description: 'Impossible d\'enregistrer l\'enfant.' });
    }
  }

  async function handleCheckOut(id: string, securityCode: string) {
    try {
      await childCheckOut.mutateAsync({ id, securityCode });
      toast({ type: 'success', title: 'Départ enregistré', description: 'L\'enfant a été récupéré.' });
    } catch {
      toast({ type: 'error', title: 'Erreur', description: 'Code de sécurité invalide ou erreur.' });
    }
  }

  const columns: Column<Record<string, unknown> & { id: string }>[] = [
    {
      key: 'child_name',
      header: 'Enfant',
      render: (item) => (
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-full bg-pink-500/20 flex items-center justify-center text-xs font-bold text-pink-300">
            {String(item.child_name ?? '').charAt(0) || '?'}
          </div>
          <div>
            <p className="font-medium text-white/90">{String(item.child_name ?? '')}</p>
            {!!item.parent_name && <p className="text-xs text-white/40">Parent: {String(item.parent_name)}</p>}
          </div>
        </div>
      ),
    },
    {
      key: 'security_code',
      header: 'Code sécurité',
      render: (item) => <Badge variant="outline">{String(item.security_code ?? '—')}</Badge>,
    },
    {
      key: 'check_in_time',
      header: 'Arrivée',
      render: (item) => <span className="text-white/60">{item.check_in_time ? formatTime(String(item.check_in_time)) : '—'}</span>,
    },
    {
      key: 'check_out_time',
      header: 'Départ',
      render: (item) => (
        item.check_out_time
          ? <span className="text-white/60">{formatTime(String(item.check_out_time))}</span>
          : <Badge variant="warning">En garderie</Badge>
      ),
    },
    {
      key: 'allergies',
      header: 'Allergies',
      render: (item) => <span className="text-white/50 text-xs">{String(item.allergies || '—')}</span>,
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-white/50">{totalCount ?? 0} enregistrement{(totalCount ?? 0) !== 1 ? 's' : ''}</p>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Enregistrer un enfant
        </Button>
      </div>
      <InfiniteScrollTable columns={columns} data={results} totalCount={totalCount} isLoading={isLoading} fetchNextPage={fetchNextPage} hasNextPage={hasNextPage} isFetchingNextPage={isFetchingNextPage} error={error} emptyMessage="Aucun enfant enregistré" />
      <Dialog open={showCreate} onClose={() => setShowCreate(false)}>
        <DialogHeader>
          <DialogTitle>Enregistrer un enfant</DialogTitle>
          <DialogDescription>Enregistrer un enfant pour la garderie pendant le service</DialogDescription>
          <DialogClose onClose={() => setShowCreate(false)} />
        </DialogHeader>
        <DialogContent>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1.5">Nom de l&apos;enfant *</label>
              <Input placeholder="Prénom Nom" value={form.child_name} onChange={(e) => setForm((f) => ({ ...f, child_name: e.target.value }))} />
            </div>
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1.5">Nom du parent</label>
              <Input placeholder="Prénom Nom du parent" value={form.parent_name} onChange={(e) => setForm((f) => ({ ...f, parent_name: e.target.value }))} />
            </div>
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1.5">Allergies</label>
              <Input placeholder="Aucune allergie connue..." value={form.allergies} onChange={(e) => setForm((f) => ({ ...f, allergies: e.target.value }))} />
            </div>
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1.5">Notes</label>
              <Textarea placeholder="Instructions spéciales..." value={form.notes} onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))} rows={2} />
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setShowCreate(false)}>Annuler</Button>
          <Button onClick={handleCreate} disabled={createCheckIn.isPending}>{createCheckIn.isPending ? 'Enregistrement...' : 'Enregistrer'}</Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Geo-Fences Tab ─────────────────────────────────────────────────────────

function GeoFencesTab() {
  const { toast } = useToast();
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: '', latitude: '', longitude: '', radius_meters: '100' });
  const createGeoFence = useCreateGeoFence();

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteGeoFences();
  const results = (data?.pages.flatMap((p) => p.results) ?? []) as (Record<string, unknown> & { id: string })[];
  const totalCount = data?.pages[0]?.count;

  async function handleCreate() {
    if (!form.name || !form.latitude || !form.longitude) {
      toast({ type: 'warning', title: 'Champs requis', description: 'Nom, latitude et longitude sont obligatoires.' });
      return;
    }
    try {
      await createGeoFence.mutateAsync({
        name: form.name,
        latitude: parseFloat(form.latitude),
        longitude: parseFloat(form.longitude),
        radius_meters: parseInt(form.radius_meters),
      });
      toast({ type: 'success', title: 'Zone créée', description: `"${form.name}" a été ajoutée.` });
      setShowCreate(false);
      setForm({ name: '', latitude: '', longitude: '', radius_meters: '100' });
    } catch {
      toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer la zone.' });
    }
  }

  const columns: Column<Record<string, unknown> & { id: string }>[] = [
    {
      key: 'name',
      header: 'Zone',
      render: (item) => <span className="font-medium text-white/90">{String(item.name ?? '')}</span>,
    },
    {
      key: 'latitude',
      header: 'Coordonnées',
      render: (item) => (
        <span className="text-white/60 text-xs font-mono">
          {Number(item.latitude ?? 0).toFixed(4)}, {Number(item.longitude ?? 0).toFixed(4)}
        </span>
      ),
    },
    {
      key: 'radius_meters',
      header: 'Rayon',
      render: (item) => <span className="text-white/60">{String(item.radius_meters ?? 100)} m</span>,
    },
    {
      key: 'is_active',
      header: 'Statut',
      render: (item) => (
        <Badge variant={item.is_active !== false ? 'success' : 'secondary'}>
          {item.is_active !== false ? 'Active' : 'Inactive'}
        </Badge>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-white/50">{totalCount ?? 0} zone{(totalCount ?? 0) !== 1 ? 's' : ''} géographique{(totalCount ?? 0) !== 1 ? 's' : ''}</p>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nouvelle zone
        </Button>
      </div>
      <InfiniteScrollTable columns={columns} data={results} totalCount={totalCount} isLoading={isLoading} fetchNextPage={fetchNextPage} hasNextPage={hasNextPage} isFetchingNextPage={isFetchingNextPage} error={error} emptyMessage="Aucune zone géographique définie" />
      <Dialog open={showCreate} onClose={() => setShowCreate(false)}>
        <DialogHeader>
          <DialogTitle>Nouvelle zone géographique</DialogTitle>
          <DialogDescription>Définir une zone pour la vérification automatique des présences</DialogDescription>
          <DialogClose onClose={() => setShowCreate(false)} />
        </DialogHeader>
        <DialogContent>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1.5">Nom de la zone *</label>
              <Input placeholder="Église principale..." value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-white/60 mb-1.5">Latitude *</label>
                <Input type="number" step="0.0001" placeholder="45.5017" value={form.latitude} onChange={(e) => setForm((f) => ({ ...f, latitude: e.target.value }))} />
              </div>
              <div>
                <label className="block text-xs font-medium text-white/60 mb-1.5">Longitude *</label>
                <Input type="number" step="0.0001" placeholder="-73.5673" value={form.longitude} onChange={(e) => setForm((f) => ({ ...f, longitude: e.target.value }))} />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1.5">Rayon (mètres)</label>
              <Input type="number" placeholder="100" value={form.radius_meters} onChange={(e) => setForm((f) => ({ ...f, radius_meters: e.target.value }))} />
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setShowCreate(false)}>Annuler</Button>
          <Button onClick={handleCreate} disabled={createGeoFence.isPending}>{createGeoFence.isPending ? 'Création...' : 'Créer la zone'}</Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── NFC Tags Tab ───────────────────────────────────────────────────────────

function NFCTagsTab() {
  const { toast } = useToast();
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ tag_id: '', label: '', location: '' });
  const createTag = useCreateNFCTag();

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteNFCTags();
  const results = (data?.pages.flatMap((p) => p.results) ?? []) as (Record<string, unknown> & { id: string })[];
  const totalCount = data?.pages[0]?.count;

  async function handleCreate() {
    if (!form.tag_id || !form.label) {
      toast({ type: 'warning', title: 'Champs requis', description: 'ID du tag et libellé sont obligatoires.' });
      return;
    }
    try {
      await createTag.mutateAsync(form);
      toast({ type: 'success', title: 'Tag créé', description: `"${form.label}" a été ajouté.` });
      setShowCreate(false);
      setForm({ tag_id: '', label: '', location: '' });
    } catch {
      toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer le tag.' });
    }
  }

  const columns: Column<Record<string, unknown> & { id: string }>[] = [
    {
      key: 'label',
      header: 'Libellé',
      render: (item) => <span className="font-medium text-white/90">{String(item.label ?? '')}</span>,
    },
    {
      key: 'tag_id',
      header: 'ID du tag',
      render: (item) => <span className="text-white/60 font-mono text-xs">{String(item.tag_id ?? '')}</span>,
    },
    {
      key: 'location',
      header: 'Emplacement',
      render: (item) => <span className="text-white/60">{String(item.location ?? '—')}</span>,
    },
    {
      key: 'is_active',
      header: 'Statut',
      render: (item) => (
        <Badge variant={item.is_active !== false ? 'success' : 'secondary'}>
          {item.is_active !== false ? 'Actif' : 'Inactif'}
        </Badge>
      ),
    },
    {
      key: 'last_scanned',
      header: 'Dernier scan',
      render: (item) => <span className="text-white/50">{item.last_scanned ? formatDate(String(item.last_scanned)) : '—'}</span>,
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-white/50">{totalCount ?? 0} tag{(totalCount ?? 0) !== 1 ? 's' : ''} NFC</p>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nouveau tag
        </Button>
      </div>
      <InfiniteScrollTable columns={columns} data={results} totalCount={totalCount} isLoading={isLoading} fetchNextPage={fetchNextPage} hasNextPage={hasNextPage} isFetchingNextPage={isFetchingNextPage} error={error} emptyMessage="Aucun tag NFC configuré" />
      <Dialog open={showCreate} onClose={() => setShowCreate(false)}>
        <DialogHeader>
          <DialogTitle>Nouveau tag NFC</DialogTitle>
          <DialogDescription>Configurer un tag NFC pour l&apos;enregistrement des présences</DialogDescription>
          <DialogClose onClose={() => setShowCreate(false)} />
        </DialogHeader>
        <DialogContent>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1.5">ID du tag *</label>
              <Input placeholder="NFC-001..." value={form.tag_id} onChange={(e) => setForm((f) => ({ ...f, tag_id: e.target.value }))} />
            </div>
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1.5">Libellé *</label>
              <Input placeholder="Entrée principale..." value={form.label} onChange={(e) => setForm((f) => ({ ...f, label: e.target.value }))} />
            </div>
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1.5">Emplacement</label>
              <Input placeholder="Hall d'entrée, salle A..." value={form.location} onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))} />
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setShowCreate(false)}>Annuler</Button>
          <Button onClick={handleCreate} disabled={createTag.isPending}>{createTag.isPending ? 'Création...' : 'Créer le tag'}</Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function AttendancePage() {
  const { data: sessionsData, isLoading: sessionsLoading } = useAttendanceSessions('page=1&page_size=1');
  const { data: alertsData } = useAbsenceAlerts('acknowledged=false');
  const { data: visitorsData } = useVisitors('page=1&page_size=1');
  const { data: avgData } = useAttendanceAverageByType();

  // Derive stats from available data
  const todayCount = (sessionsData?.results?.[0] as AttendanceSession | undefined)?.attendance_count ?? '—';
  const avgAttendance = (() => {
    if (!Array.isArray(avgData)) return '—';
    const culte = (avgData as AverageByType[]).find((a) => a.type === 'culte' || a.type === 'worship');
    return culte ? Math.round(culte.average) : '—';
  })();
  const unacknowledgedAlerts = alertsData?.count ?? '—';
  const visitorsCount = visitorsData?.count ?? '—';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Présence</h1>
          <p className="text-white/50">Suivi des présences, alertes d&apos;absence et enregistrement des visiteurs</p>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Users}
          label="Présences aujourd'hui"
          value={sessionsLoading ? '...' : todayCount}
          sub="Session la plus récente"
          accent="bg-purple-600"
          loading={sessionsLoading}
        />
        <StatCard
          icon={TrendingUp}
          label="Présence moyenne"
          value={avgAttendance}
          sub="Cultes dominicaux"
          accent="bg-blue-600"
        />
        <StatCard
          icon={Flame}
          label="Alertes d'absence"
          value={unacknowledgedAlerts}
          sub="Non acquittées"
          accent="bg-rose-600"
        />
        <StatCard
          icon={CalendarDays}
          label="Visiteurs ce mois"
          value={visitorsCount}
          sub="Nouveau ce mois-ci"
          accent="bg-emerald-600"
        />
      </div>

      {/* Tabs */}
      <Tabs defaultValue="sessions">
        <TabsList className="flex-wrap">
          <TabsTrigger value="sessions">
            <CalendarDays className="h-4 w-4 mr-1.5 inline-block" />
            Sessions
          </TabsTrigger>
          <TabsTrigger value="scanner">
            <QrCode className="h-4 w-4 mr-1.5 inline-block" />
            Scanner QR
          </TabsTrigger>
          <TabsTrigger value="alertes">
            <AlertTriangle className="h-4 w-4 mr-1.5 inline-block" />
            Alertes
          </TabsTrigger>
          <TabsTrigger value="visiteurs">
            <UserPlus className="h-4 w-4 mr-1.5 inline-block" />
            Visiteurs
          </TabsTrigger>
          <TabsTrigger value="analytique">
            <BarChart3 className="h-4 w-4 mr-1.5 inline-block" />
            Analytique
          </TabsTrigger>
          <TabsTrigger value="enfants">
            <Baby className="h-4 w-4 mr-1.5 inline-block" />
            Enfants
          </TabsTrigger>
          <TabsTrigger value="geofences">
            <MapPinIcon className="h-4 w-4 mr-1.5 inline-block" />
            Zones GPS
          </TabsTrigger>
          <TabsTrigger value="nfc">
            <Wifi className="h-4 w-4 mr-1.5 inline-block" />
            Tags NFC
          </TabsTrigger>
        </TabsList>

        <TabsContent value="sessions">
          <SessionsTab />
        </TabsContent>

        <TabsContent value="scanner">
          <ScannerTab />
        </TabsContent>

        <TabsContent value="alertes">
          <AlertesTab />
        </TabsContent>

        <TabsContent value="visiteurs">
          <VisiteursTab />
        </TabsContent>

        <TabsContent value="analytique">
          <AnalytiqueTab />
        </TabsContent>

        <TabsContent value="enfants">
          <ChildCheckInsTab />
        </TabsContent>

        <TabsContent value="geofences">
          <GeoFencesTab />
        </TabsContent>

        <TabsContent value="nfc">
          <NFCTagsTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
