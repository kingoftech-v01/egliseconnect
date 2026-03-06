'use client';

import { useState } from 'react';
import {
  GraduationCap,
  ClipboardList,
  UserPlus,
  Users,
  FileText,
  Calendar,
  Plus,
  Search,
  Check,
  X,
  Clock,
  BookOpen,
  Shield,
  ArrowRight,
  Eye,
  Sparkles,
  Route,
  Mail,
  Phone,
  Trophy,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Avatar } from '@/components/ui/avatar';
import { InfiniteScrollTable } from '@/components/ui/infinite-scroll-table';
import type { Column } from '@/components/ui/data-table';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from '@/components/ui/tabs';
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
  useOnboardingStats,
  useCreateCourse,
  useTrainings,
  useAcceptInterview,
  useCounterProposeInterview,
  useCreateInvitationCode,
  useMentors,
  useInfiniteCourses,
  useInfiniteInterviews,
  useInfiniteInvitationCodes,
  useInfiniteOnboardingDocuments,
  useInfiniteVisitors,
  useCreateVisitorFollowUp,
  useInfiniteWelcomeSequences,
  useCreateWelcomeSequence,
  useInfiniteAchievements,
  useCreateAchievement,
} from '@/hooks/use-onboarding';

// ─── Types ──────────────────────────────────────────────────────────────────

interface StatsData {
  in_pipeline?: number;
  completed_this_month?: number;
  avg_completion_days?: number;
  active_mentors?: number;
}

interface CourseItem extends Record<string, unknown> {
  id: string;
  title: string;
  lessons_count?: number;
  enrolled_count?: number;
  is_active?: boolean;
  status?: string;
}

interface TrainingItem extends Record<string, unknown> {
  id: string;
  member_name?: string;
  member_photo?: string | null;
  stage?: string;
  enrolled_at?: string;
  progress?: number;
}

interface InterviewItem extends Record<string, unknown> {
  id: string;
  member_name?: string;
  member_photo?: string | null;
  scheduled_date?: string;
  scheduled_time?: string;
  status?: string;
}

interface InvitationItem extends Record<string, unknown> {
  id: string;
  code?: string;
  role?: string;
  max_uses?: number;
  used_count?: number;
  expires_at?: string;
  is_active?: boolean;
}

interface MentorItem extends Record<string, unknown> {
  id: string;
  mentor_name?: string;
  mentor_photo?: string | null;
  mentee_name?: string;
  mentee_photo?: string | null;
  checkin_count?: number;
  next_checkin?: string;
}

interface DocumentItem extends Record<string, unknown> {
  id: string;
  title?: string;
  document_type?: string;
  is_required?: boolean;
  signed_count?: number;
  total_count?: number;
}

// ─── Constants ───────────────────────────────────────────────────────────────

const PIPELINE_STAGES = [
  { key: 'inscrit', label: 'Inscrit', color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/20', dot: 'bg-blue-400' },
  { key: 'formulaire', label: 'Formulaire', color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/20', dot: 'bg-amber-400' },
  { key: 'formation', label: 'Formation', color: 'text-purple-400', bg: 'bg-purple-500/10 border-purple-500/20', dot: 'bg-purple-400' },
  { key: 'entrevue', label: 'Entrevue', color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20', dot: 'bg-emerald-400' },
];

const ROLE_LABELS: Record<string, string> = {
  member: 'Membre',
  leader: 'Leader',
  deacon: 'Diacre',
  elder: 'Ancien',
  pastor: 'Pasteur',
  admin: 'Admin',
};

const DOCUMENT_TYPE_LABELS: Record<string, string> = {
  covenant: 'Alliance',
  policy: 'Politique',
  consent: 'Consentement',
  waiver: 'Décharge',
};

const INTERVIEW_STATUS_CONFIG: Record<string, { label: string; variant: 'default' | 'success' | 'warning' | 'secondary' | 'destructive' | 'outline' }> = {
  pending: { label: 'En attente', variant: 'warning' },
  accepted: { label: 'Acceptée', variant: 'success' },
  counter_proposed: { label: 'Contre-proposée', variant: 'default' },
  completed: { label: 'Complétée', variant: 'secondary' },
};

// ─── Stat Card ───────────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  icon: Icon,
  iconBg,
  loading,
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
  iconBg: string;
  loading?: boolean;
}) {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-start gap-4">
          <div className={`p-2.5 rounded-xl ${iconBg}`}>
            <Icon className="h-5 w-5 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs text-white/40 uppercase tracking-wider font-medium">{label}</p>
            {loading ? (
              <div className="h-7 w-16 bg-white/[0.06] rounded-lg mt-1 animate-pulse" />
            ) : (
              <p className="text-2xl font-bold text-white mt-0.5">{value}</p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Pipeline Tab ─────────────────────────────────────────────────────────────

function PipelineTab() {
  const { data: trainingsData, isLoading } = useTrainings();
  const trainings = (trainingsData?.results ?? []) as TrainingItem[];

  const byStage = PIPELINE_STAGES.reduce<Record<string, TrainingItem[]>>((acc, s) => {
    acc[s.key] = trainings.filter((t) => (t.stage || 'inscrit') === s.key);
    return acc;
  }, {});

  if (isLoading) {
    return (
      <div className="grid grid-cols-4 gap-4">
        {PIPELINE_STAGES.map((s) => (
          <Card key={s.key} className="animate-pulse">
            <CardHeader className="pb-3">
              <div className="h-4 w-24 bg-white/[0.06] rounded" />
            </CardHeader>
            <CardContent className="space-y-3">
              {[1, 2].map((i) => (
                <div key={i} className="h-20 bg-white/[0.04] rounded-xl" />
              ))}
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
      {PIPELINE_STAGES.map((stage) => {
        const items = byStage[stage.key] ?? [];
        return (
          <Card key={stage.key} className={`border ${stage.bg}`}>
            <CardHeader className="pb-3 pt-4 px-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`h-2 w-2 rounded-full ${stage.dot}`} />
                  <CardTitle className={`text-sm font-semibold ${stage.color}`}>
                    {stage.label}
                  </CardTitle>
                </div>
                <span className="text-xs text-white/30 font-medium bg-white/[0.06] px-2 py-0.5 rounded-full">
                  {items.length}
                </span>
              </div>
            </CardHeader>
            <CardContent className="px-4 pb-4 space-y-2.5">
              {items.length === 0 ? (
                <div className="text-center py-6 text-white/20 text-xs">
                  Aucun membre
                </div>
              ) : (
                items.map((item) => (
                  <PipelineCard key={item.id} item={item} stageColor={stage.color} />
                ))
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

function PipelineCard({ item, stageColor }: { item: TrainingItem; stageColor: string }) {
  const progress = item.progress ?? 0;
  const enrolledAt = item.enrolled_at
    ? new Date(item.enrolled_at).toLocaleDateString('fr-CA', { month: 'short', day: 'numeric' })
    : '—';

  return (
    <div className="rounded-xl bg-white/[0.04] border border-white/[0.06] p-3 hover:bg-white/[0.07] transition-colors">
      <div className="flex items-center gap-2.5 mb-2.5">
        <Avatar
          src={item.member_photo ?? null}
          fallback={item.member_name ?? '?'}
          size="sm"
        />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white/90 truncate">
            {item.member_name ?? 'Membre inconnu'}
          </p>
          <p className="text-xs text-white/30">{enrolledAt}</p>
        </div>
      </div>
      <div className="space-y-1">
        <div className="flex justify-between text-xs">
          <span className="text-white/30">Progression</span>
          <span className={`font-medium ${stageColor}`}>{progress}%</span>
        </div>
        <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-purple-600 to-purple-400 transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    </div>
  );
}

// ─── Cours Tab ────────────────────────────────────────────────────────────────

function CoursTab() {
  const [search, setSearch] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const { toast } = useToast();

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteCourses(search);
  const createCourse = useCreateCourse();

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as CourseItem[];
  const totalCount = data?.pages[0]?.count;

  const [form, setForm] = useState({ title: '', description: '' });

  const handleCreate = async () => {
    if (!form.title.trim()) return;
    try {
      await createCourse.mutateAsync(form);
      toast({ type: 'success', title: 'Cours créé', description: `"${form.title}" a été ajouté.` });
      setShowCreate(false);
      setForm({ title: '', description: '' });
    } catch {
      toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer le cours.' });
    }
  };

  const columns: Column<CourseItem>[] = [
    {
      key: 'title',
      header: 'Titre',
      render: (item) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-purple-500/10">
            <BookOpen className="h-4 w-4 text-purple-400" />
          </div>
          <span className="font-medium text-white/90">{item.title}</span>
        </div>
      ),
    },
    {
      key: 'lessons_count',
      header: 'Leçons',
      render: (item) => (
        <span className="text-white/60">{item.lessons_count ?? 0}</span>
      ),
    },
    {
      key: 'enrolled_count',
      header: 'Inscrits',
      render: (item) => (
        <span className="text-white/60">{item.enrolled_count ?? 0}</span>
      ),
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
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
          <Input
            placeholder="Rechercher un cours..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nouveau cours
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
        emptyMessage="Aucun cours trouvé"
      />

      <Dialog open={showCreate} onClose={() => setShowCreate(false)}>
        <DialogHeader>
          <DialogTitle>Créer un cours</DialogTitle>
          <DialogDescription>Ajouter un nouveau cours au programme d&apos;intégration.</DialogDescription>
          <DialogClose onClose={() => setShowCreate(false)} />
        </DialogHeader>
        <DialogContent>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-white/50 uppercase tracking-wider">Titre</label>
              <Input
                placeholder="Titre du cours..."
                value={form.title}
                onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-white/50 uppercase tracking-wider">Description</label>
              <Input
                placeholder="Description du cours..."
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              />
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="secondary" onClick={() => setShowCreate(false)}>Annuler</Button>
          <Button onClick={handleCreate} disabled={createCourse.isPending || !form.title.trim()}>
            {createCourse.isPending ? 'Création...' : 'Créer'}
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Entrevues Tab ────────────────────────────────────────────────────────────

function EntrevuesTab() {
  const [counterProposalId, setCounterProposalId] = useState<string | null>(null);
  const [newDate, setNewDate] = useState('');
  const { toast } = useToast();

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteInterviews();
  const acceptInterview = useAcceptInterview();
  const counterPropose = useCounterProposeInterview();

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as InterviewItem[];
  const totalCount = data?.pages[0]?.count;

  const handleAccept = async (id: string) => {
    try {
      await acceptInterview.mutateAsync(id);
      toast({ type: 'success', title: 'Entrevue acceptée', description: "L'entrevue a été confirmée." });
    } catch {
      toast({ type: 'error', title: 'Erreur', description: "Impossible d'accepter l'entrevue." });
    }
  };

  const handleCounterPropose = async () => {
    if (!counterProposalId || !newDate) return;
    try {
      await counterPropose.mutateAsync({ id: counterProposalId, proposedDate: newDate });
      toast({ type: 'success', title: 'Contre-proposition envoyée', description: 'La nouvelle date a été proposée.' });
      setCounterProposalId(null);
      setNewDate('');
    } catch {
      toast({ type: 'error', title: 'Erreur', description: 'Impossible d\'envoyer la contre-proposition.' });
    }
  };

  const columns: Column<InterviewItem>[] = [
    {
      key: 'member_name',
      header: 'Membre',
      render: (item) => (
        <div className="flex items-center gap-3">
          <Avatar src={item.member_photo ?? null} fallback={item.member_name ?? '?'} size="sm" />
          <span className="font-medium text-white/90">{item.member_name ?? '—'}</span>
        </div>
      ),
    },
    {
      key: 'scheduled_date',
      header: 'Date',
      render: (item) => item.scheduled_date
        ? new Date(item.scheduled_date).toLocaleDateString('fr-CA', { year: 'numeric', month: 'short', day: 'numeric' })
        : '—',
    },
    {
      key: 'scheduled_time',
      header: 'Heure',
      render: (item) => <span className="text-white/60">{item.scheduled_time ?? '—'}</span>,
    },
    {
      key: 'status',
      header: 'Statut',
      render: (item) => {
        const cfg = INTERVIEW_STATUS_CONFIG[item.status ?? ''] ?? { label: item.status ?? '—', variant: 'secondary' as const };
        return <Badge variant={cfg.variant}>{cfg.label}</Badge>;
      },
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (item) => {
        const isPending = item.status === 'pending';
        if (!isPending) return null;
        return (
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="success"
              onClick={(e) => { e.stopPropagation(); handleAccept(item.id); }}
              disabled={acceptInterview.isPending}
            >
              <Check className="h-3.5 w-3.5 mr-1" />
              Accepter
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={(e) => { e.stopPropagation(); setCounterProposalId(item.id); }}
            >
              <Calendar className="h-3.5 w-3.5 mr-1" />
              Contre-proposer
            </Button>
          </div>
        );
      },
    },
  ];

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
        emptyMessage="Aucune entrevue trouvée"
      />

      <Dialog open={!!counterProposalId} onClose={() => { setCounterProposalId(null); setNewDate(''); }}>
        <DialogHeader>
          <DialogTitle>Contre-proposer une date</DialogTitle>
          <DialogDescription>Suggérer une nouvelle date pour l&apos;entrevue.</DialogDescription>
          <DialogClose onClose={() => { setCounterProposalId(null); setNewDate(''); }} />
        </DialogHeader>
        <DialogContent>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-white/50 uppercase tracking-wider">Nouvelle date et heure</label>
            <Input
              type="datetime-local"
              value={newDate}
              onChange={(e) => setNewDate(e.target.value)}
            />
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="secondary" onClick={() => { setCounterProposalId(null); setNewDate(''); }}>Annuler</Button>
          <Button onClick={handleCounterPropose} disabled={counterPropose.isPending || !newDate}>
            {counterPropose.isPending ? 'Envoi...' : 'Envoyer'}
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Invitations Tab ──────────────────────────────────────────────────────────

function InvitationsTab() {
  const [showCreate, setShowCreate] = useState(false);
  const { toast } = useToast();

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteInvitationCodes();
  const createInvitation = useCreateInvitationCode();

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as InvitationItem[];
  const totalCount = data?.pages[0]?.count;

  const [form, setForm] = useState({ role: 'member', max_uses: '1', expires_at: '' });

  const handleCreate = async () => {
    try {
      await createInvitation.mutateAsync({
        role: form.role,
        max_uses: parseInt(form.max_uses, 10),
        expires_at: form.expires_at || undefined,
      });
      toast({ type: 'success', title: 'Code créé', description: 'Le code d\'invitation a été généré.' });
      setShowCreate(false);
      setForm({ role: 'member', max_uses: '1', expires_at: '' });
    } catch {
      toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer le code.' });
    }
  };

  const columns: Column<InvitationItem>[] = [
    {
      key: 'code',
      header: 'Code',
      render: (item) => (
        <code className="text-sm font-mono bg-white/[0.06] px-2 py-1 rounded-lg text-purple-300">
          {item.code ?? '—'}
        </code>
      ),
    },
    {
      key: 'role',
      header: 'Rôle',
      render: (item) => (
        <Badge variant="outline">{ROLE_LABELS[item.role ?? ''] ?? item.role ?? '—'}</Badge>
      ),
    },
    {
      key: 'usage',
      header: 'Utilisations',
      render: (item) => (
        <span className="text-white/60">
          {item.used_count ?? 0} / {item.max_uses ?? '∞'}
        </span>
      ),
    },
    {
      key: 'expires_at',
      header: 'Expiration',
      render: (item) => item.expires_at
        ? new Date(item.expires_at).toLocaleDateString('fr-CA', { year: 'numeric', month: 'short', day: 'numeric' })
        : <span className="text-white/30">Aucune</span>,
    },
    {
      key: 'is_active',
      header: 'Statut',
      render: (item) => (
        <Badge variant={item.is_active !== false ? 'success' : 'secondary'}>
          {item.is_active !== false ? 'Actif' : 'Expiré'}
        </Badge>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Créer un code
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
        emptyMessage="Aucun code d'invitation trouvé"
      />

      <Dialog open={showCreate} onClose={() => setShowCreate(false)}>
        <DialogHeader>
          <DialogTitle>Créer un code d&apos;invitation</DialogTitle>
          <DialogDescription>Générer un code pour inviter un nouveau membre.</DialogDescription>
          <DialogClose onClose={() => setShowCreate(false)} />
        </DialogHeader>
        <DialogContent>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-white/50 uppercase tracking-wider">Rôle</label>
              <Select
                value={form.role}
                onChange={(e) => setForm((f) => ({ ...f, role: e.target.value }))}
              >
                {Object.entries(ROLE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </Select>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-white/50 uppercase tracking-wider">Utilisations maximales</label>
              <Input
                type="number"
                min="1"
                placeholder="1"
                value={form.max_uses}
                onChange={(e) => setForm((f) => ({ ...f, max_uses: e.target.value }))}
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-white/50 uppercase tracking-wider">Date d&apos;expiration (optionnel)</label>
              <Input
                type="date"
                value={form.expires_at}
                onChange={(e) => setForm((f) => ({ ...f, expires_at: e.target.value }))}
              />
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="secondary" onClick={() => setShowCreate(false)}>Annuler</Button>
          <Button onClick={handleCreate} disabled={createInvitation.isPending}>
            {createInvitation.isPending ? 'Création...' : 'Créer'}
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Mentors Tab ──────────────────────────────────────────────────────────────

function MentorsTab() {
  const [page] = useState(1);
  const params = new URLSearchParams();
  params.set('page', String(page));

  const { data, isLoading } = useMentors(params.toString());
  const mentors = (data?.results ?? []) as MentorItem[];

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="p-5 space-y-4">
              <div className="h-10 bg-white/[0.06] rounded-xl" />
              <div className="h-10 bg-white/[0.04] rounded-xl" />
              <div className="h-4 bg-white/[0.04] rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!mentors.length) {
    return (
      <div className="rounded-2xl bg-white/[0.05] backdrop-blur-xl border border-white/[0.08] p-16 text-center">
        <Users className="h-10 w-10 text-white/20 mx-auto mb-3" />
        <p className="text-white/40 text-sm">Aucune paire mentor-mentee trouvée</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {mentors.map((item) => {
        const nextCheckin = item.next_checkin
          ? new Date(item.next_checkin).toLocaleDateString('fr-CA', { month: 'short', day: 'numeric' })
          : null;

        return (
          <Card key={item.id} className="hover:border-white/[0.14] transition-all duration-200">
            <CardContent className="p-5">
              <div className="space-y-3">
                {/* Mentor */}
                <div className="flex items-center gap-3">
                  <Avatar
                    src={item.mentor_photo ?? null}
                    fallback={item.mentor_name ?? '?'}
                    size="md"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-white/30 font-medium uppercase tracking-wider">Mentor</p>
                    <p className="text-sm font-semibold text-white/90 truncate">
                      {item.mentor_name ?? 'Inconnu'}
                    </p>
                  </div>
                </div>

                {/* Arrow */}
                <div className="flex items-center gap-2 px-1">
                  <div className="flex-1 h-px bg-white/[0.06]" />
                  <ArrowRight className="h-3.5 w-3.5 text-white/20" />
                  <div className="flex-1 h-px bg-white/[0.06]" />
                </div>

                {/* Mentee */}
                <div className="flex items-center gap-3">
                  <Avatar
                    src={item.mentee_photo ?? null}
                    fallback={item.mentee_name ?? '?'}
                    size="md"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-white/30 font-medium uppercase tracking-wider">Mentee</p>
                    <p className="text-sm font-semibold text-white/90 truncate">
                      {item.mentee_name ?? 'Inconnu'}
                    </p>
                  </div>
                </div>

                {/* Stats row */}
                <div className="flex items-center justify-between pt-1 border-t border-white/[0.06]">
                  <div className="flex items-center gap-1.5 text-xs text-white/40">
                    <Check className="h-3.5 w-3.5 text-emerald-400" />
                    <span>{item.checkin_count ?? 0} rencontres</span>
                  </div>
                  {nextCheckin && (
                    <div className="flex items-center gap-1.5 text-xs text-white/40">
                      <Calendar className="h-3.5 w-3.5 text-purple-400" />
                      <span>{nextCheckin}</span>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

// ─── Documents Tab ────────────────────────────────────────────────────────────

function DocumentsTab() {
  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteOnboardingDocuments();

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as DocumentItem[];
  const totalCount = data?.pages[0]?.count;

  const columns: Column<DocumentItem>[] = [
    {
      key: 'title',
      header: 'Document',
      render: (item) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-white/[0.06]">
            <FileText className="h-4 w-4 text-white/50" />
          </div>
          <span className="font-medium text-white/90">{item.title ?? '—'}</span>
        </div>
      ),
    },
    {
      key: 'document_type',
      header: 'Type',
      render: (item) => (
        <Badge variant="outline">
          {DOCUMENT_TYPE_LABELS[item.document_type ?? ''] ?? item.document_type ?? '—'}
        </Badge>
      ),
    },
    {
      key: 'is_required',
      header: 'Requis',
      render: (item) => item.is_required
        ? <Badge variant="destructive">Requis</Badge>
        : <Badge variant="secondary">Optionnel</Badge>,
    },
    {
      key: 'signed_count',
      header: 'Signatures',
      render: (item) => (
        <div className="flex items-center gap-2">
          <span className="text-white/90 font-medium">{item.signed_count ?? 0}</span>
          {item.total_count != null && (
            <span className="text-white/30 text-xs">/ {item.total_count}</span>
          )}
        </div>
      ),
    },
  ];

  return (
    <InfiniteScrollTable
      columns={columns}
      data={items}
      totalCount={totalCount}
      isLoading={isLoading}
      fetchNextPage={fetchNextPage}
      hasNextPage={hasNextPage}
      isFetchingNextPage={isFetchingNextPage}
      error={error}
      emptyMessage="Aucun document trouvé"
    />
  );
}

// ─── Visitors Tab ────────────────────────────────────────────────────────────

function VisitorsTab() {
  const [showCreate, setShowCreate] = useState(false);
  const { toast } = useToast();
  const createVisitor = useCreateVisitorFollowUp();
  const [form, setForm] = useState({ name: '', email: '', phone: '', notes: '' });

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteVisitors();

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as (Record<string, unknown>)[];
  const totalCount = data?.pages[0]?.count;

  const columns: Column<Record<string, unknown>>[] = [
    {
      key: 'name',
      header: 'Visiteur',
      render: (item) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-blue-500/10">
            <Eye className="h-4 w-4 text-blue-400" />
          </div>
          <span className="font-medium text-white/90">{String(item.name ?? item.visitor_name ?? '—')}</span>
        </div>
      ),
    },
    {
      key: 'email',
      header: 'Email',
      render: (item) => (
        <span className="text-white/60">{String(item.email ?? '—')}</span>
      ),
    },
    {
      key: 'phone',
      header: 'Téléphone',
      render: (item) => (
        <span className="text-white/60">{String(item.phone ?? '—')}</span>
      ),
    },
    {
      key: 'follow_up_status',
      header: 'Suivi',
      render: (item) => {
        const status = String(item.follow_up_status ?? item.status ?? 'pending');
        const labels: Record<string, string> = { pending: 'En attente', contacted: 'Contacté', completed: 'Complété' };
        const variants: Record<string, 'warning' | 'success' | 'secondary'> = { pending: 'warning', contacted: 'default' as 'warning', completed: 'success' };
        return <Badge variant={variants[status] ?? 'secondary'}>{labels[status] ?? status}</Badge>;
      },
    },
    {
      key: 'visit_date',
      header: 'Date de visite',
      render: (item) =>
        item.visit_date
          ? new Date(item.visit_date as string).toLocaleDateString('fr-CA', { year: 'numeric', month: 'short', day: 'numeric' })
          : '—',
    },
  ];

  async function handleCreate() {
    if (!form.name.trim()) return;
    try {
      await createVisitor.mutateAsync({
        name: form.name.trim(),
        email: form.email.trim() || undefined,
        phone: form.phone.trim() || undefined,
        notes: form.notes.trim() || undefined,
      });
      toast({ type: 'success', title: 'Visiteur ajouté' });
      setShowCreate(false);
      setForm({ name: '', email: '', phone: '', notes: '' });
    } catch {
      toast({ type: 'error', title: 'Erreur' });
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Ajouter un visiteur
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
        emptyMessage="Aucun visiteur trouvé"
      />

      <Dialog open={showCreate} onClose={() => setShowCreate(false)}>
        <DialogHeader>
          <DialogTitle>Ajouter un visiteur</DialogTitle>
          <DialogDescription>Enregistrer un nouveau visiteur pour suivi.</DialogDescription>
          <DialogClose onClose={() => setShowCreate(false)} />
        </DialogHeader>
        <DialogContent className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-white/50 uppercase tracking-wider">Nom *</label>
            <Input placeholder="Nom complet" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-white/50 uppercase tracking-wider">Email</label>
              <Input type="email" placeholder="email@exemple.com" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-white/50 uppercase tracking-wider">Téléphone</label>
              <Input placeholder="514-555-1234" value={form.phone} onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))} />
            </div>
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-white/50 uppercase tracking-wider">Notes</label>
            <Input placeholder="Notes de suivi..." value={form.notes} onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))} />
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="secondary" onClick={() => setShowCreate(false)}>Annuler</Button>
          <Button onClick={handleCreate} disabled={createVisitor.isPending || !form.name.trim()}>
            {createVisitor.isPending ? 'Ajout...' : 'Ajouter'}
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Welcome Sequences Tab ──────────────────────────────────────────────────

function SequencesTab() {
  const [showCreate, setShowCreate] = useState(false);
  const { toast } = useToast();
  const createSequence = useCreateWelcomeSequence();
  const [form, setForm] = useState({ name: '', description: '', delay_days: '0' });

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteWelcomeSequences();

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as (Record<string, unknown>)[];
  const totalCount = data?.pages[0]?.count;

  const columns: Column<Record<string, unknown>>[] = [
    {
      key: 'name',
      header: 'Séquence',
      render: (item) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-emerald-500/10">
            <Route className="h-4 w-4 text-emerald-400" />
          </div>
          <div>
            <span className="font-medium text-white/90">{String(item.name ?? '—')}</span>
            {!!item.description && (
              <p className="text-xs text-white/40 mt-0.5 truncate max-w-xs">{String(item.description)}</p>
            )}
          </div>
        </div>
      ),
    },
    {
      key: 'steps_count',
      header: 'Étapes',
      render: (item) => (
        <span className="text-white/60">{String(item.steps_count ?? item.step_count ?? 0)}</span>
      ),
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

  async function handleCreate() {
    if (!form.name.trim()) return;
    try {
      await createSequence.mutateAsync({
        name: form.name.trim(),
        description: form.description.trim() || undefined,
        delay_days: parseInt(form.delay_days) || 0,
      });
      toast({ type: 'success', title: 'Séquence créée' });
      setShowCreate(false);
      setForm({ name: '', description: '', delay_days: '0' });
    } catch {
      toast({ type: 'error', title: 'Erreur' });
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nouvelle séquence
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
        emptyMessage="Aucune séquence de bienvenue"
      />

      <Dialog open={showCreate} onClose={() => setShowCreate(false)}>
        <DialogHeader>
          <DialogTitle>Nouvelle séquence de bienvenue</DialogTitle>
          <DialogDescription>Créer une séquence automatisée pour accueillir les nouveaux membres.</DialogDescription>
          <DialogClose onClose={() => setShowCreate(false)} />
        </DialogHeader>
        <DialogContent className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-white/50 uppercase tracking-wider">Nom *</label>
            <Input placeholder="ex. Bienvenue standard" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-white/50 uppercase tracking-wider">Description</label>
            <Input placeholder="Description de la séquence..." value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-white/50 uppercase tracking-wider">Délai initial (jours)</label>
            <Input type="number" min="0" value={form.delay_days} onChange={(e) => setForm((f) => ({ ...f, delay_days: e.target.value }))} />
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="secondary" onClick={() => setShowCreate(false)}>Annuler</Button>
          <Button onClick={handleCreate} disabled={createSequence.isPending || !form.name.trim()}>
            {createSequence.isPending ? 'Création...' : 'Créer'}
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Achievements Tab ────────────────────────────────────────────────────────

function AchievementsTab() {
  const [showCreate, setShowCreate] = useState(false);
  const { toast } = useToast();
  const createAchievement = useCreateAchievement();
  const [form, setForm] = useState({ name: '', description: '', points: '10' });

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteAchievements();

  const items = (data?.pages.flatMap((p) => p.results) ?? []) as (Record<string, unknown>)[];
  const totalCount = data?.pages[0]?.count;

  const columns: Column<Record<string, unknown>>[] = [
    {
      key: 'name',
      header: 'Accomplissement',
      render: (item) => (
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-amber-500/10">
            <Trophy className="h-4 w-4 text-amber-400" />
          </div>
          <div>
            <span className="font-medium text-white/90">{String(item.name ?? '—')}</span>
            {!!item.description && (
              <p className="text-xs text-white/40 mt-0.5 truncate max-w-xs">{String(item.description)}</p>
            )}
          </div>
        </div>
      ),
    },
    {
      key: 'points',
      header: 'Points',
      render: (item) => (
        <span className="text-amber-400 font-semibold tabular-nums">{String(item.points ?? 0)}</span>
      ),
    },
    {
      key: 'earned_count',
      header: 'Obtenus',
      render: (item) => (
        <span className="text-white/60">{String(item.earned_count ?? item.members_count ?? 0)}</span>
      ),
    },
  ];

  async function handleCreate() {
    if (!form.name.trim()) return;
    try {
      await createAchievement.mutateAsync({
        name: form.name.trim(),
        description: form.description.trim() || undefined,
        points: parseInt(form.points) || 10,
      });
      toast({ type: 'success', title: 'Accomplissement créé' });
      setShowCreate(false);
      setForm({ name: '', description: '', points: '10' });
    } catch {
      toast({ type: 'error', title: 'Erreur' });
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nouvel accomplissement
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
        emptyMessage="Aucun accomplissement défini"
      />

      <Dialog open={showCreate} onClose={() => setShowCreate(false)}>
        <DialogHeader>
          <DialogTitle>Nouvel accomplissement</DialogTitle>
          <DialogDescription>Définir un badge ou accomplissement pour la gamification.</DialogDescription>
          <DialogClose onClose={() => setShowCreate(false)} />
        </DialogHeader>
        <DialogContent className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-white/50 uppercase tracking-wider">Nom *</label>
            <Input placeholder="ex. Premier pas, Explorateur..." value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-white/50 uppercase tracking-wider">Description</label>
            <Input placeholder="Critères pour obtenir cet accomplissement..." value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-white/50 uppercase tracking-wider">Points</label>
            <Input type="number" min="1" value={form.points} onChange={(e) => setForm((f) => ({ ...f, points: e.target.value }))} />
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="secondary" onClick={() => setShowCreate(false)}>Annuler</Button>
          <Button onClick={handleCreate} disabled={createAchievement.isPending || !form.name.trim()}>
            {createAchievement.isPending ? 'Création...' : 'Créer'}
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function OnboardingPage() {
  const { data: statsData, isLoading: statsLoading } = useOnboardingStats();
  const stats = (statsData as StatsData) ?? {};

  const avgDays = stats.avg_completion_days
    ? `${Math.round(stats.avg_completion_days)} j`
    : '—';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Intégration</h1>
          <p className="text-white/40 text-sm mt-0.5">
            Gestion du pipeline d&apos;intégration des nouveaux membres
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs text-white/40">En temps réel</span>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard
          label="En pipeline"
          value={stats.in_pipeline ?? '—'}
          icon={ClipboardList}
          iconBg="bg-blue-600"
          loading={statsLoading}
        />
        <StatCard
          label="Complétés ce mois"
          value={stats.completed_this_month ?? '—'}
          icon={Check}
          iconBg="bg-emerald-600"
          loading={statsLoading}
        />
        <StatCard
          label="Durée moyenne"
          value={statsLoading ? '—' : avgDays}
          icon={Clock}
          iconBg="bg-amber-600"
          loading={statsLoading}
        />
        <StatCard
          label="Mentors actifs"
          value={stats.active_mentors ?? '—'}
          icon={Users}
          iconBg="bg-purple-600"
          loading={statsLoading}
        />
      </div>

      {/* Tabs */}
      <Tabs defaultValue="pipeline">
        <TabsList className="flex-wrap gap-1">
          <TabsTrigger value="pipeline">
            <ClipboardList className="h-3.5 w-3.5 mr-1.5" />
            Pipeline
          </TabsTrigger>
          <TabsTrigger value="cours">
            <GraduationCap className="h-3.5 w-3.5 mr-1.5" />
            Cours
          </TabsTrigger>
          <TabsTrigger value="entrevues">
            <Calendar className="h-3.5 w-3.5 mr-1.5" />
            Entrevues
          </TabsTrigger>
          <TabsTrigger value="invitations">
            <UserPlus className="h-3.5 w-3.5 mr-1.5" />
            Invitations
          </TabsTrigger>
          <TabsTrigger value="mentors">
            <Users className="h-3.5 w-3.5 mr-1.5" />
            Mentors
          </TabsTrigger>
          <TabsTrigger value="documents">
            <FileText className="h-3.5 w-3.5 mr-1.5" />
            Documents
          </TabsTrigger>
          <TabsTrigger value="visiteurs">
            <Eye className="h-3.5 w-3.5 mr-1.5" />
            Visiteurs
          </TabsTrigger>
          <TabsTrigger value="sequences">
            <Route className="h-3.5 w-3.5 mr-1.5" />
            Séquences
          </TabsTrigger>
          <TabsTrigger value="accomplissements">
            <Trophy className="h-3.5 w-3.5 mr-1.5" />
            Accomplissements
          </TabsTrigger>
        </TabsList>

        <TabsContent value="pipeline">
          <PipelineTab />
        </TabsContent>

        <TabsContent value="cours">
          <CoursTab />
        </TabsContent>

        <TabsContent value="entrevues">
          <EntrevuesTab />
        </TabsContent>

        <TabsContent value="invitations">
          <InvitationsTab />
        </TabsContent>

        <TabsContent value="mentors">
          <MentorsTab />
        </TabsContent>

        <TabsContent value="documents">
          <DocumentsTab />
        </TabsContent>

        <TabsContent value="visiteurs">
          <VisitorsTab />
        </TabsContent>

        <TabsContent value="sequences">
          <SequencesTab />
        </TabsContent>

        <TabsContent value="accomplissements">
          <AchievementsTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
