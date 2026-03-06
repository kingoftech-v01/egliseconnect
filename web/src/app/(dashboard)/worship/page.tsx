'use client';

import { useState } from 'react';
import {
  Music,
  Mic2,
  BookOpen,
  ListMusic,
  UserCheck,
  Clock,
  Plus,
  Search,
  Play,
  Check,
  X,
  Calendar,
  MapPin,
  Users,
  Hash,
  Gauge,
  Tag,
  HandMetal,
  Radio,
  Library,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';

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
  useWorshipServices,
  useCreateWorshipService,
  useSongs,
  useCreateSong,
  useCreateSermon,
  useSetlists,
  useMyAssignments,
  useConfirmAssignment,
  useDeclineAssignment,
  useRehearsals,
  useInfiniteWorshipServices,
  useInfiniteSermons,
  useInfiniteAssignments,
  useInfiniteRehearsals,
  useCreateSetlist,
  useCreateRehearsal,
  useRehearsalRSVP,
  useInfiniteSongRequests,
  useCreateSongRequest,
  useInfiniteLiveStreams,
  useCreateLiveStream,
  useInfiniteSermonSeries,
  useCreateSermonSeries,
} from '@/hooks/use-worship';

// ─── Types ───────────────────────────────────────────────────────────────────

type ServiceRecord = Record<string, unknown> & {
  id: string;
  title: string;
  date: string;
  service_type: string;
  sections_count?: number;
  confirmation_rate?: number;
  notes?: string;
};

type SongRecord = Record<string, unknown> & {
  id: string;
  title: string;
  artist?: string;
  key?: string;
  bpm?: number;
  ccli_number?: string;
  tags?: string[];
  lyrics?: string;
  chords?: string;
};

type SermonRecord = Record<string, unknown> & {
  id: string;
  title: string;
  speaker?: string;
  date: string;
  series?: string;
  scripture_reference?: string;
  notes?: string;
  audio_url?: string;
  video_url?: string;
};

type SetlistRecord = Record<string, unknown> & {
  id: string;
  name: string;
  service_date?: string;
  songs?: { title: string; key?: string; duration_seconds?: number }[];
  total_duration_seconds?: number;
};

type AssignmentRecord = Record<string, unknown> & {
  id: string;
  member_name?: string;
  position?: string;
  service_title?: string;
  service_date?: string;
  status: 'assigned' | 'confirmed' | 'declined';
};

type RehearsalRecord = Record<string, unknown> & {
  id: string;
  date: string;
  time?: string;
  location?: string;
  attendees_count?: number;
  notes?: string;
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

const SERVICE_TYPES = [
  { value: 'sunday_morning', label: 'Culte du dimanche matin' },
  { value: 'sunday_evening', label: 'Culte du dimanche soir' },
  { value: 'wednesday', label: 'Service du mercredi' },
  { value: 'special', label: 'Service spécial' },
  { value: 'prayer', label: 'Réunion de prière' },
  { value: 'other', label: 'Autre' },
];

const MUSICAL_KEYS = [
  'C', 'C#', 'Db', 'D', 'D#', 'Eb', 'E', 'F',
  'F#', 'Gb', 'G', 'G#', 'Ab', 'A', 'A#', 'Bb', 'B',
  'Cm', 'Dm', 'Em', 'Fm', 'Gm', 'Am', 'Bm',
];

function formatDate(dateStr: string) {
  if (!dateStr) return '—';
  try {
    return new Intl.DateTimeFormat('fr-CA', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    }).format(new Date(dateStr));
  } catch {
    return dateStr;
  }
}

function formatDuration(seconds: number) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
}

function statusBadgeVariant(status: string): 'warning' | 'success' | 'destructive' | 'secondary' {
  if (status === 'confirmed') return 'success';
  if (status === 'declined') return 'destructive';
  if (status === 'assigned') return 'warning';
  return 'secondary';
}

function statusLabel(status: string) {
  const map: Record<string, string> = {
    assigned: 'Assigné',
    confirmed: 'Confirmé',
    declined: 'Refusé',
  };
  return map[status] ?? status;
}

// ─── Stat Card ────────────────────────────────────────────────────────────────

function StatCard({
  icon: Icon,
  label,
  value,
  isLoading,
  accent,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  isLoading?: boolean;
  accent: string;
}) {
  return (
    <div className="rounded-2xl bg-white/[0.05] backdrop-blur-xl border border-white/[0.08] shadow-[0_8px_32px_rgba(0,0,0,0.2)] p-5 flex items-center gap-4">
      <div className={`rounded-xl p-3 ${accent}`}>
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <p className="text-xs text-white/40 uppercase tracking-wide">{label}</p>
        {isLoading ? (
          <Skeleton className="h-7 w-12 mt-1" />
        ) : (
          <p className="text-2xl font-bold text-white">{value}</p>
        )}
      </div>
    </div>
  );
}

// ─── Create Service Dialog ────────────────────────────────────────────────────

function CreateServiceDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const createService = useCreateWorshipService();
  const [form, setForm] = useState({
    title: '',
    date: '',
    service_type: 'sunday_morning',
    notes: '',
  });

  function handleChange(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit() {
    if (!form.title || !form.date) {
      toast({ type: 'error', title: 'Champs requis', description: 'Titre et date sont obligatoires.' });
      return;
    }
    try {
      await createService.mutateAsync(form);
      toast({ type: 'success', title: 'Service créé', description: `"${form.title}" a été ajouté.` });
      onClose();
      setForm({ title: '', date: '', service_type: 'sunday_morning', notes: '' });
    } catch {
      toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer le service.' });
    }
  }

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogHeader>
        <DialogTitle>Nouveau service</DialogTitle>
        <DialogDescription>Planifier un nouveau service de culte</DialogDescription>
        <DialogClose onClose={onClose} />
      </DialogHeader>
      <DialogContent>
        <div className="space-y-4">
          <div>
            <label className="text-xs text-white/50 mb-1.5 block">Titre *</label>
            <Input
              placeholder="Culte du dimanche 9h..."
              value={form.title}
              onChange={(e) => handleChange('title', e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs text-white/50 mb-1.5 block">Date *</label>
            <Input
              type="datetime-local"
              value={form.date}
              onChange={(e) => handleChange('date', e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs text-white/50 mb-1.5 block">Type de service</label>
            <Select
              value={form.service_type}
              onChange={(e) => handleChange('service_type', e.target.value)}
            >
              {SERVICE_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </Select>
          </div>
          <div>
            <label className="text-xs text-white/50 mb-1.5 block">Notes</label>
            <Textarea
              placeholder="Notes ou instructions..."
              value={form.notes}
              onChange={(e) => handleChange('notes', e.target.value)}
              className="min-h-[80px]"
            />
          </div>
        </div>
      </DialogContent>
      <DialogFooter>
        <Button variant="ghost" onClick={onClose}>Annuler</Button>
        <Button onClick={handleSubmit} disabled={createService.isPending}>
          {createService.isPending ? 'Création...' : 'Créer le service'}
        </Button>
      </DialogFooter>
    </Dialog>
  );
}

// ─── Create Song Dialog ───────────────────────────────────────────────────────

function CreateSongDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const createSong = useCreateSong();
  const [form, setForm] = useState({
    title: '',
    artist: '',
    key: 'C',
    bpm: '',
    ccli_number: '',
    lyrics: '',
    chords: '',
    tags: '',
  });

  function handleChange(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit() {
    if (!form.title) {
      toast({ type: 'error', title: 'Champ requis', description: 'Le titre du chant est obligatoire.' });
      return;
    }
    try {
      await createSong.mutateAsync({
        ...form,
        bpm: form.bpm ? parseInt(form.bpm) : undefined,
        tags: form.tags ? form.tags.split(',').map((t) => t.trim()).filter(Boolean) : [],
      });
      toast({ type: 'success', title: 'Chant ajouté', description: `"${form.title}" a été ajouté à la bibliothèque.` });
      onClose();
      setForm({ title: '', artist: '', key: 'C', bpm: '', ccli_number: '', lyrics: '', chords: '', tags: '' });
    } catch {
      toast({ type: 'error', title: 'Erreur', description: 'Impossible d\'ajouter le chant.' });
    }
  }

  return (
    <Dialog open={open} onClose={onClose} className="max-w-2xl">
      <DialogHeader>
        <DialogTitle>Nouveau chant</DialogTitle>
        <DialogDescription>Ajouter un chant à la bibliothèque musicale</DialogDescription>
        <DialogClose onClose={onClose} />
      </DialogHeader>
      <DialogContent>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-white/50 mb-1.5 block">Titre *</label>
              <Input
                placeholder="Amazing Grace..."
                value={form.title}
                onChange={(e) => handleChange('title', e.target.value)}
              />
            </div>
            <div>
              <label className="text-xs text-white/50 mb-1.5 block">Artiste / Auteur</label>
              <Input
                placeholder="Chris Tomlin..."
                value={form.artist}
                onChange={(e) => handleChange('artist', e.target.value)}
              />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-xs text-white/50 mb-1.5 block">Tonalité</label>
              <Select value={form.key} onChange={(e) => handleChange('key', e.target.value)}>
                {MUSICAL_KEYS.map((k) => (
                  <option key={k} value={k}>{k}</option>
                ))}
              </Select>
            </div>
            <div>
              <label className="text-xs text-white/50 mb-1.5 block">BPM</label>
              <Input
                type="number"
                placeholder="120"
                value={form.bpm}
                onChange={(e) => handleChange('bpm', e.target.value)}
              />
            </div>
            <div>
              <label className="text-xs text-white/50 mb-1.5 block">N° CCLI</label>
              <Input
                placeholder="7065764"
                value={form.ccli_number}
                onChange={(e) => handleChange('ccli_number', e.target.value)}
              />
            </div>
          </div>
          <div>
            <label className="text-xs text-white/50 mb-1.5 block">Étiquettes (séparées par virgule)</label>
            <Input
              placeholder="louange, adoration, contemporain..."
              value={form.tags}
              onChange={(e) => handleChange('tags', e.target.value)}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-white/50 mb-1.5 block">Paroles</label>
              <Textarea
                placeholder="Paroles du chant..."
                value={form.lyrics}
                onChange={(e) => handleChange('lyrics', e.target.value)}
                className="min-h-[120px]"
              />
            </div>
            <div>
              <label className="text-xs text-white/50 mb-1.5 block">Accords</label>
              <Textarea
                placeholder="G D Em C..."
                value={form.chords}
                onChange={(e) => handleChange('chords', e.target.value)}
                className="min-h-[120px]"
              />
            </div>
          </div>
        </div>
      </DialogContent>
      <DialogFooter>
        <Button variant="ghost" onClick={onClose}>Annuler</Button>
        <Button onClick={handleSubmit} disabled={createSong.isPending}>
          {createSong.isPending ? 'Ajout...' : 'Ajouter le chant'}
        </Button>
      </DialogFooter>
    </Dialog>
  );
}

// ─── Create Sermon Dialog ─────────────────────────────────────────────────────

function CreateSermonDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const createSermon = useCreateSermon();
  const [form, setForm] = useState({
    title: '',
    speaker: '',
    date: '',
    series: '',
    scripture_reference: '',
    notes: '',
    audio_url: '',
    video_url: '',
  });

  function handleChange(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit() {
    if (!form.title || !form.date) {
      toast({ type: 'error', title: 'Champs requis', description: 'Titre et date sont obligatoires.' });
      return;
    }
    try {
      await createSermon.mutateAsync(form);
      toast({ type: 'success', title: 'Prédication créée', description: `"${form.title}" a été ajoutée.` });
      onClose();
      setForm({ title: '', speaker: '', date: '', series: '', scripture_reference: '', notes: '', audio_url: '', video_url: '' });
    } catch {
      toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer la prédication.' });
    }
  }

  return (
    <Dialog open={open} onClose={onClose} className="max-w-2xl">
      <DialogHeader>
        <DialogTitle>Nouvelle prédication</DialogTitle>
        <DialogDescription>Enregistrer une nouvelle prédication</DialogDescription>
        <DialogClose onClose={onClose} />
      </DialogHeader>
      <DialogContent>
        <div className="space-y-4">
          <div>
            <label className="text-xs text-white/50 mb-1.5 block">Titre *</label>
            <Input
              placeholder="La grâce suffisante..."
              value={form.title}
              onChange={(e) => handleChange('title', e.target.value)}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-white/50 mb-1.5 block">Prédicateur</label>
              <Input
                placeholder="Pasteur Jean..."
                value={form.speaker}
                onChange={(e) => handleChange('speaker', e.target.value)}
              />
            </div>
            <div>
              <label className="text-xs text-white/50 mb-1.5 block">Date *</label>
              <Input
                type="date"
                value={form.date}
                onChange={(e) => handleChange('date', e.target.value)}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-white/50 mb-1.5 block">Série</label>
              <Input
                placeholder="Série sur la foi..."
                value={form.series}
                onChange={(e) => handleChange('series', e.target.value)}
              />
            </div>
            <div>
              <label className="text-xs text-white/50 mb-1.5 block">Référence scripturaire</label>
              <Input
                placeholder="Jean 3:16, Romains 8:28..."
                value={form.scripture_reference}
                onChange={(e) => handleChange('scripture_reference', e.target.value)}
              />
            </div>
          </div>
          <div>
            <label className="text-xs text-white/50 mb-1.5 block">Notes</label>
            <Textarea
              placeholder="Notes ou résumé de la prédication..."
              value={form.notes}
              onChange={(e) => handleChange('notes', e.target.value)}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-white/50 mb-1.5 block">URL audio</label>
              <Input
                type="url"
                placeholder="https://..."
                value={form.audio_url}
                onChange={(e) => handleChange('audio_url', e.target.value)}
              />
            </div>
            <div>
              <label className="text-xs text-white/50 mb-1.5 block">URL vidéo</label>
              <Input
                type="url"
                placeholder="https://youtube.com/..."
                value={form.video_url}
                onChange={(e) => handleChange('video_url', e.target.value)}
              />
            </div>
          </div>
        </div>
      </DialogContent>
      <DialogFooter>
        <Button variant="ghost" onClick={onClose}>Annuler</Button>
        <Button onClick={handleSubmit} disabled={createSermon.isPending}>
          {createSermon.isPending ? 'Création...' : 'Créer la prédication'}
        </Button>
      </DialogFooter>
    </Dialog>
  );
}

// ─── Create Setlist Dialog ────────────────────────────────────────────────────

function CreateSetlistDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const createSetlist = useCreateSetlist();
  const [form, setForm] = useState({ name: '', service_date: '', notes: '' });

  function handleChange(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit() {
    if (!form.name) {
      toast({ type: 'error', title: 'Champ requis', description: 'Le nom du setlist est obligatoire.' });
      return;
    }
    try {
      await createSetlist.mutateAsync(form);
      toast({ type: 'success', title: 'Setlist créée', description: `"${form.name}" a été créée.` });
      onClose();
      setForm({ name: '', service_date: '', notes: '' });
    } catch {
      toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer le setlist.' });
    }
  }

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogHeader>
        <DialogTitle>Nouveau setlist</DialogTitle>
        <DialogDescription>Créer une liste de chants pour un service</DialogDescription>
        <DialogClose onClose={onClose} />
      </DialogHeader>
      <DialogContent>
        <div className="space-y-4">
          <div>
            <label className="text-xs text-white/50 mb-1.5 block">Nom *</label>
            <Input
              placeholder="Culte 9h — 2 mars..."
              value={form.name}
              onChange={(e) => handleChange('name', e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs text-white/50 mb-1.5 block">Date du service</label>
            <Input
              type="date"
              value={form.service_date}
              onChange={(e) => handleChange('service_date', e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs text-white/50 mb-1.5 block">Notes</label>
            <Textarea
              placeholder="Notes sur le setlist..."
              value={form.notes}
              onChange={(e) => handleChange('notes', e.target.value)}
            />
          </div>
        </div>
      </DialogContent>
      <DialogFooter>
        <Button variant="ghost" onClick={onClose}>Annuler</Button>
        <Button onClick={handleSubmit} disabled={createSetlist.isPending}>
          {createSetlist.isPending ? 'Création...' : 'Créer le setlist'}
        </Button>
      </DialogFooter>
    </Dialog>
  );
}

// ─── Create Rehearsal Dialog ──────────────────────────────────────────────────

function CreateRehearsalDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const createRehearsal = useCreateRehearsal();
  const [form, setForm] = useState({ date: '', time: '', location: '', notes: '' });

  function handleChange(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit() {
    if (!form.date) {
      toast({ type: 'error', title: 'Champ requis', description: 'La date de répétition est obligatoire.' });
      return;
    }
    try {
      await createRehearsal.mutateAsync(form);
      toast({ type: 'success', title: 'Répétition créée', description: 'La répétition a été planifiée.' });
      onClose();
      setForm({ date: '', time: '', location: '', notes: '' });
    } catch {
      toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer la répétition.' });
    }
  }

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogHeader>
        <DialogTitle>Nouvelle répétition</DialogTitle>
        <DialogDescription>Planifier une répétition pour l&apos;équipe de culte</DialogDescription>
        <DialogClose onClose={onClose} />
      </DialogHeader>
      <DialogContent>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-white/50 mb-1.5 block">Date *</label>
              <Input
                type="date"
                value={form.date}
                onChange={(e) => handleChange('date', e.target.value)}
              />
            </div>
            <div>
              <label className="text-xs text-white/50 mb-1.5 block">Heure</label>
              <Input
                type="time"
                value={form.time}
                onChange={(e) => handleChange('time', e.target.value)}
              />
            </div>
          </div>
          <div>
            <label className="text-xs text-white/50 mb-1.5 block">Lieu</label>
            <Input
              placeholder="Salle de musique, église principale..."
              value={form.location}
              onChange={(e) => handleChange('location', e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs text-white/50 mb-1.5 block">Notes</label>
            <Textarea
              placeholder="Instructions pour la répétition..."
              value={form.notes}
              onChange={(e) => handleChange('notes', e.target.value)}
            />
          </div>
        </div>
      </DialogContent>
      <DialogFooter>
        <Button variant="ghost" onClick={onClose}>Annuler</Button>
        <Button onClick={handleSubmit} disabled={createRehearsal.isPending}>
          {createRehearsal.isPending ? 'Création...' : 'Créer la répétition'}
        </Button>
      </DialogFooter>
    </Dialog>
  );
}

// ─── Sermon Detail Dialog ─────────────────────────────────────────────────────

function SermonDetailDialog({
  sermon,
  onClose,
}: {
  sermon: SermonRecord | null;
  onClose: () => void;
}) {
  if (!sermon) return null;
  return (
    <Dialog open={!!sermon} onClose={onClose} className="max-w-xl">
      <DialogHeader>
        <DialogTitle>{sermon.title}</DialogTitle>
        <DialogDescription>
          {sermon.speaker && `${sermon.speaker} · `}{formatDate(sermon.date)}
        </DialogDescription>
        <DialogClose onClose={onClose} />
      </DialogHeader>
      <DialogContent>
        <div className="space-y-4">
          {!!sermon.series && (
            <div>
              <p className="text-xs text-white/40 mb-1">Série</p>
              <p className="text-sm text-white/80">{sermon.series}</p>
            </div>
          )}
          {!!sermon.scripture_reference && (
            <div>
              <p className="text-xs text-white/40 mb-1">Référence scripturaire</p>
              <p className="text-sm text-white/80 font-medium">{sermon.scripture_reference}</p>
            </div>
          )}
          {!!sermon.notes && (
            <div>
              <p className="text-xs text-white/40 mb-1">Notes</p>
              <p className="text-sm text-white/70 whitespace-pre-wrap">{sermon.notes}</p>
            </div>
          )}
          {(sermon.audio_url || sermon.video_url) && (
            <div className="flex gap-2 pt-2">
              {!!sermon.audio_url && (
                <a href={sermon.audio_url} target="_blank" rel="noreferrer">
                  <Button variant="secondary" size="sm">
                    <Play className="h-4 w-4 mr-1.5" />
                    Écouter
                  </Button>
                </a>
              )}
              {!!sermon.video_url && (
                <a href={sermon.video_url} target="_blank" rel="noreferrer">
                  <Button variant="outline" size="sm">
                    <Play className="h-4 w-4 mr-1.5" />
                    Visionner
                  </Button>
                </a>
              )}
            </div>
          )}
        </div>
      </DialogContent>
      <DialogFooter>
        <Button variant="ghost" onClick={onClose}>Fermer</Button>
      </DialogFooter>
    </Dialog>
  );
}

// ─── Services Tab ─────────────────────────────────────────────────────────────

function ServicesTab() {
  const [showCreate, setShowCreate] = useState(false);
  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteWorshipServices();
  const results = (data?.pages.flatMap((p) => p.results) ?? []) as ServiceRecord[];
  const totalCount = data?.pages[0]?.count;

  const serviceTypeLabel = (type: string) =>
    SERVICE_TYPES.find((t) => t.value === type)?.label ?? type;

  const columns: Column<ServiceRecord>[] = [
    {
      key: 'title',
      header: 'Service',
      render: (item) => (
        <div>
          <p className="font-medium text-white/90">{item.title}</p>
        </div>
      ),
    },
    {
      key: 'date',
      header: 'Date',
      render: (item) => formatDate(item.date),
    },
    {
      key: 'service_type',
      header: 'Type',
      render: (item) => (
        <Badge variant="secondary">{serviceTypeLabel(item.service_type)}</Badge>
      ),
    },
    {
      key: 'sections_count',
      header: 'Sections',
      render: (item) => (
        <span className="text-white/60">{item.sections_count ?? 0}</span>
      ),
    },
    {
      key: 'confirmation_rate',
      header: 'Confirmations',
      render: (item) => {
        const rate = item.confirmation_rate ?? 0;
        const color = rate >= 80 ? 'text-emerald-400' : rate >= 50 ? 'text-amber-400' : 'text-white/50';
        return <span className={color}>{rate}%</span>;
      },
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-white/50">
          {totalCount ?? 0} service{(totalCount ?? 0) !== 1 ? 's' : ''}
        </p>
        <Button size="sm" onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4 mr-1.5" />
          Nouveau service
        </Button>
      </div>

      <InfiniteScrollTable
        columns={columns}
        data={results}
        totalCount={totalCount}
        isLoading={isLoading}
        fetchNextPage={fetchNextPage}
        hasNextPage={hasNextPage}
        isFetchingNextPage={isFetchingNextPage}
        error={error}
        emptyMessage="Aucun service planifié"
      />

      <CreateServiceDialog open={showCreate} onClose={() => setShowCreate(false)} />
    </div>
  );
}

// ─── Chants Tab ───────────────────────────────────────────────────────────────

function SongCard({ song }: { song: SongRecord }) {
  return (
    <div className="rounded-2xl bg-white/[0.05] backdrop-blur-xl border border-white/[0.08] shadow-[0_8px_32px_rgba(0,0,0,0.2)] p-4 hover:border-purple-500/30 hover:bg-white/[0.07] transition-all duration-200">
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-white/90 truncate">{song.title}</p>
          {song.artist && <p className="text-xs text-white/50 mt-0.5 truncate">{song.artist}</p>}
        </div>
        {!!song.key && (
          <Badge variant="default" className="shrink-0">{song.key}</Badge>
        )}
      </div>

      <div className="flex items-center gap-3 text-xs text-white/40 mb-3">
        {!!song.bpm && (
          <span className="flex items-center gap-1">
            <Gauge className="h-3 w-3" />
            {song.bpm} BPM
          </span>
        )}
        {!!song.ccli_number && (
          <span className="flex items-center gap-1">
            <Hash className="h-3 w-3" />
            {song.ccli_number}
          </span>
        )}
      </div>

      {song.tags && song.tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {song.tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] bg-white/[0.06] text-white/50 border border-white/[0.06]"
            >
              <Tag className="h-2.5 w-2.5" />
              {tag}
            </span>
          ))}
          {song.tags.length > 3 && (
            <span className="text-[10px] text-white/30">+{song.tags.length - 3}</span>
          )}
        </div>
      )}
    </div>
  );
}

function SongsTab() {
  const [search, setSearch] = useState('');
  const [keyFilter, setKeyFilter] = useState('');
  const [showCreate, setShowCreate] = useState(false);

  const params = new URLSearchParams();
  if (search) params.set('search', search);
  if (keyFilter) params.set('key', keyFilter);

  const { data, isLoading } = useSongs(params.toString());
  const songs = (data?.results ?? []) as SongRecord[];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
          <Input
            placeholder="Rechercher un chant..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="w-40">
          <Select value={keyFilter} onChange={(e) => setKeyFilter(e.target.value)}>
            <option value="">Toutes les tonalités</option>
            {MUSICAL_KEYS.map((k) => (
              <option key={k} value={k}>{k}</option>
            ))}
          </Select>
        </div>
        <div className="ml-auto">
          <Button size="sm" onClick={() => setShowCreate(true)}>
            <Plus className="h-4 w-4 mr-1.5" />
            Nouveau chant
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-2xl" />
          ))}
        </div>
      ) : songs.length === 0 ? (
        <div className="rounded-2xl bg-white/[0.05] backdrop-blur-xl border border-white/[0.08] p-12 text-center">
          <Music className="h-10 w-10 text-white/20 mx-auto mb-3" />
          <p className="text-white/40">Aucun chant trouvé</p>
          <p className="text-xs text-white/25 mt-1">Ajoutez des chants à la bibliothèque musicale</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {songs.map((song) => (
            <SongCard key={song.id} song={song} />
          ))}
        </div>
      )}

      <CreateSongDialog open={showCreate} onClose={() => setShowCreate(false)} />
    </div>
  );
}

// ─── Prédications Tab ─────────────────────────────────────────────────────────

function SermonsTab() {
  const [showCreate, setShowCreate] = useState(false);
  const [selectedSermon, setSelectedSermon] = useState<SermonRecord | null>(null);

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteSermons();
  const results = (data?.pages.flatMap((p) => p.results) ?? []) as SermonRecord[];
  const totalCount = data?.pages[0]?.count;

  const columns: Column<SermonRecord>[] = [
    {
      key: 'title',
      header: 'Titre',
      render: (item) => (
        <div>
          <p className="font-medium text-white/90">{item.title}</p>
          {item.series && <p className="text-xs text-white/40 mt-0.5">{item.series}</p>}
        </div>
      ),
    },
    {
      key: 'speaker',
      header: 'Prédicateur',
      render: (item) => <span className="text-white/70">{item.speaker || '—'}</span>,
    },
    {
      key: 'date',
      header: 'Date',
      render: (item) => formatDate(item.date),
    },
    {
      key: 'scripture_reference',
      header: 'Référence',
      render: (item) => (
        <span className="text-purple-300/80 text-sm">{item.scripture_reference || '—'}</span>
      ),
    },
    {
      key: 'media',
      header: 'Médias',
      render: (item) => (
        <div className="flex gap-1.5">
          {!!item.audio_url && (
            <span className="w-5 h-5 flex items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400">
              <Play className="h-2.5 w-2.5" />
            </span>
          )}
          {!!item.video_url && (
            <span className="w-5 h-5 flex items-center justify-center rounded-full bg-purple-500/20 text-purple-400">
              <Play className="h-2.5 w-2.5" />
            </span>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-white/50">
          {totalCount ?? 0} prédication{(totalCount ?? 0) !== 1 ? 's' : ''}
        </p>
        <Button size="sm" onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4 mr-1.5" />
          Nouvelle prédication
        </Button>
      </div>

      <InfiniteScrollTable
        columns={columns}
        data={results}
        totalCount={totalCount}
        isLoading={isLoading}
        fetchNextPage={fetchNextPage}
        hasNextPage={hasNextPage}
        isFetchingNextPage={isFetchingNextPage}
        error={error}
        emptyMessage="Aucune prédication enregistrée"
        onRowClick={(item) => setSelectedSermon(item)}
      />

      <CreateSermonDialog open={showCreate} onClose={() => setShowCreate(false)} />
      <SermonDetailDialog sermon={selectedSermon} onClose={() => setSelectedSermon(null)} />
    </div>
  );
}

// ─── Setlists Tab ─────────────────────────────────────────────────────────────

function SetlistCard({ setlist }: { setlist: SetlistRecord }) {
  const totalDuration = setlist.total_duration_seconds ?? 0;
  const songs = setlist.songs ?? [];

  return (
    <div className="rounded-2xl bg-white/[0.05] backdrop-blur-xl border border-white/[0.08] shadow-[0_8px_32px_rgba(0,0,0,0.2)] p-5">
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="font-semibold text-white/90">{setlist.name}</p>
          {!!setlist.service_date && (
            <p className="text-xs text-white/40 mt-0.5 flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {formatDate(setlist.service_date)}
            </p>
          )}
        </div>
        {totalDuration > 0 && (
          <span className="text-xs text-white/40 flex items-center gap-1 shrink-0">
            <Clock className="h-3 w-3" />
            {formatDuration(totalDuration)}
          </span>
        )}
      </div>

      {songs.length > 0 ? (
        <div className="space-y-1.5">
          {songs.map((song, i) => (
            <div key={i} className="flex items-center justify-between gap-2 py-1 border-b border-white/[0.04] last:border-0">
              <div className="flex items-center gap-2 min-w-0">
                <span className="text-xs text-white/25 w-4 shrink-0">{i + 1}</span>
                <span className="text-sm text-white/70 truncate">{song.title}</span>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {song.key && <Badge variant="secondary" className="text-[10px] py-0">{song.key}</Badge>}
                {!!song.duration_seconds && (
                  <span className="text-xs text-white/30">{formatDuration(song.duration_seconds)}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-xs text-white/30 italic">Aucun chant assigné</p>
      )}
    </div>
  );
}

function SetlistsTab() {
  const [showCreate, setShowCreate] = useState(false);
  const { data, isLoading } = useSetlists();
  const setlists = (data?.results ?? []) as SetlistRecord[];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-white/50">
          {data?.count ?? 0} setlist{(data?.count ?? 0) !== 1 ? 's' : ''}
        </p>
        <Button size="sm" onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4 mr-1.5" />
          Nouveau setlist
        </Button>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-40 rounded-2xl" />)}
        </div>
      ) : setlists.length === 0 ? (
        <div className="rounded-2xl bg-white/[0.05] backdrop-blur-xl border border-white/[0.08] p-12 text-center">
          <ListMusic className="h-10 w-10 text-white/20 mx-auto mb-3" />
          <p className="text-white/40">Aucun setlist créé</p>
          <p className="text-xs text-white/25 mt-1">Créez des setlists pour vos services de culte</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {setlists.map((s) => (
            <SetlistCard key={s.id} setlist={s} />
          ))}
        </div>
      )}

      <CreateSetlistDialog open={showCreate} onClose={() => setShowCreate(false)} />
    </div>
  );
}

// ─── Assignments Tab ──────────────────────────────────────────────────────────

function AssignmentsTab() {
  const { toast } = useToast();

  const {
    data: allData,
    isLoading: allLoading,
    fetchNextPage: allFetchNextPage,
    hasNextPage: allHasNextPage,
    isFetchingNextPage: allIsFetchingNextPage,
    error: allError,
  } = useInfiniteAssignments();
  const { data: myData, isLoading: myLoading } = useMyAssignments();

  const confirmMutation = useConfirmAssignment();
  const declineMutation = useDeclineAssignment();

  const myAssignments = (myData?.results ?? []) as AssignmentRecord[];
  const allAssignments = (allData?.pages.flatMap((p) => p.results) ?? []) as AssignmentRecord[];
  const allTotalCount = allData?.pages[0]?.count;

  async function handleConfirm(id: string) {
    try {
      await confirmMutation.mutateAsync(id);
      toast({ type: 'success', title: 'Assignment confirmé', description: 'Vous avez confirmé votre participation.' });
    } catch {
      toast({ type: 'error', title: 'Erreur', description: 'Impossible de confirmer l\'assignment.' });
    }
  }

  async function handleDecline(id: string) {
    try {
      await declineMutation.mutateAsync({ id });
      toast({ type: 'warning', title: 'Assignment refusé', description: 'Vous avez refusé cet assignment.' });
    } catch {
      toast({ type: 'error', title: 'Erreur', description: 'Impossible de refuser l\'assignment.' });
    }
  }

  const allColumns: Column<AssignmentRecord>[] = [
    {
      key: 'member_name',
      header: 'Membre',
      render: (item) => <span className="text-white/80">{item.member_name || '—'}</span>,
    },
    {
      key: 'position',
      header: 'Rôle',
      render: (item) => <span className="text-white/70">{item.position || '—'}</span>,
    },
    {
      key: 'service_title',
      header: 'Service',
      render: (item) => <span className="text-white/70 truncate max-w-[160px] block">{item.service_title || '—'}</span>,
    },
    {
      key: 'service_date',
      header: 'Date',
      render: (item) => formatDate(item.service_date ?? ''),
    },
    {
      key: 'status',
      header: 'Statut',
      render: (item) => (
        <Badge variant={statusBadgeVariant(item.status)}>
          {statusLabel(item.status)}
        </Badge>
      ),
    },
  ];

  return (
    <div className="space-y-8">
      {/* My assignments */}
      <div>
        <h3 className="text-sm font-medium text-white/60 uppercase tracking-wide mb-3">
          Mes assignments
        </h3>
        {myLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-32 rounded-2xl" />)}
          </div>
        ) : myAssignments.length === 0 ? (
          <div className="rounded-2xl bg-white/[0.05] backdrop-blur-xl border border-white/[0.08] p-8 text-center">
            <UserCheck className="h-8 w-8 text-white/20 mx-auto mb-2" />
            <p className="text-white/40 text-sm">Aucun assignment à venir</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {myAssignments.map((assignment) => (
              <div
                key={assignment.id}
                className="rounded-2xl bg-white/[0.05] backdrop-blur-xl border border-white/[0.08] shadow-[0_8px_32px_rgba(0,0,0,0.2)] p-4"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <p className="font-medium text-white/90 text-sm">{assignment.service_title || 'Service'}</p>
                    <p className="text-xs text-white/40 mt-0.5">{formatDate(assignment.service_date ?? '')}</p>
                  </div>
                  <Badge variant={statusBadgeVariant(assignment.status)}>
                    {statusLabel(assignment.status)}
                  </Badge>
                </div>
                {!!assignment.position && (
                  <p className="text-xs text-purple-300/70 mb-3">{assignment.position}</p>
                )}
                {assignment.status === 'assigned' && (
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="success"
                      className="flex-1 h-8 text-xs"
                      onClick={() => handleConfirm(assignment.id)}
                      disabled={confirmMutation.isPending}
                    >
                      <Check className="h-3 w-3 mr-1" />
                      Confirmer
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      className="flex-1 h-8 text-xs"
                      onClick={() => handleDecline(assignment.id)}
                      disabled={declineMutation.isPending}
                    >
                      <X className="h-3 w-3 mr-1" />
                      Refuser
                    </Button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* All assignments */}
      <div>
        <h3 className="text-sm font-medium text-white/60 uppercase tracking-wide mb-3">
          Tous les assignments
        </h3>
        <InfiniteScrollTable
          columns={allColumns}
          data={allAssignments}
          totalCount={allTotalCount}
          isLoading={allLoading}
          fetchNextPage={allFetchNextPage}
          hasNextPage={allHasNextPage}
          isFetchingNextPage={allIsFetchingNextPage}
          error={allError}
          emptyMessage="Aucun assignment trouvé"
        />
      </div>
    </div>
  );
}

// ─── Répétitions Tab ──────────────────────────────────────────────────────────

function RehearsalsTab() {
  const { toast } = useToast();
  const [showCreate, setShowCreate] = useState(false);
  const rehearsalRSVP = useRehearsalRSVP();

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteRehearsals();
  const results = (data?.pages.flatMap((p) => p.results) ?? []) as RehearsalRecord[];
  const totalCount = data?.pages[0]?.count;

  async function handleRSVP(id: string) {
    try {
      await rehearsalRSVP.mutateAsync(id);
      toast({ type: 'success', title: 'RSVP confirmé', description: 'Votre présence à la répétition a été enregistrée.' });
    } catch {
      toast({ type: 'error', title: 'Erreur', description: 'Impossible d\'enregistrer votre RSVP.' });
    }
  }

  const columns: Column<RehearsalRecord>[] = [
    {
      key: 'date',
      header: 'Date',
      render: (item) => (
        <div className="flex items-center gap-1.5">
          <Calendar className="h-3.5 w-3.5 text-white/30" />
          <span>{formatDate(item.date)}</span>
        </div>
      ),
    },
    {
      key: 'time',
      header: 'Heure',
      render: (item) => (
        <div className="flex items-center gap-1.5">
          <Clock className="h-3.5 w-3.5 text-white/30" />
          <span>{item.time || '—'}</span>
        </div>
      ),
    },
    {
      key: 'location',
      header: 'Lieu',
      render: (item) => (
        <div className="flex items-center gap-1.5">
          <MapPin className="h-3.5 w-3.5 text-white/30" />
          <span>{item.location || '—'}</span>
        </div>
      ),
    },
    {
      key: 'attendees_count',
      header: 'Participants',
      render: (item) => (
        <div className="flex items-center gap-1.5">
          <Users className="h-3.5 w-3.5 text-white/30" />
          <span>{item.attendees_count ?? 0}</span>
        </div>
      ),
    },
    {
      key: 'rsvp',
      header: 'RSVP',
      render: (item) => (
        <Button
          size="sm"
          variant="outline"
          className="h-7 text-xs"
          onClick={(e) => { e.stopPropagation(); handleRSVP(item.id); }}
          disabled={rehearsalRSVP.isPending}
        >
          <Check className="h-3 w-3 mr-1" />
          {rehearsalRSVP.isPending ? 'Enregistrement...' : 'Je serai présent'}
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-white/50">
          {totalCount ?? 0} répétition{(totalCount ?? 0) !== 1 ? 's' : ''}
        </p>
        <Button size="sm" onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4 mr-1.5" />
          Nouvelle répétition
        </Button>
      </div>

      <InfiniteScrollTable
        columns={columns}
        data={results}
        totalCount={totalCount}
        isLoading={isLoading}
        fetchNextPage={fetchNextPage}
        hasNextPage={hasNextPage}
        isFetchingNextPage={isFetchingNextPage}
        error={error}
        emptyMessage="Aucune répétition planifiée"
      />

      <CreateRehearsalDialog open={showCreate} onClose={() => setShowCreate(false)} />
    </div>
  );
}

// ─── Song Requests Tab ──────────────────────────────────────────────────────

function SongRequestsTab() {
  const { toast } = useToast();
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ song_title: '', requested_by_name: '', notes: '' });
  const createRequest = useCreateSongRequest();

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteSongRequests();
  const results = (data?.pages.flatMap((p) => p.results) ?? []) as (Record<string, unknown> & { id: string })[];
  const totalCount = data?.pages[0]?.count;

  async function handleSubmit() {
    if (!form.song_title) {
      toast({ type: 'error', title: 'Champ requis', description: 'Le titre du chant est obligatoire.' });
      return;
    }
    try {
      await createRequest.mutateAsync(form);
      toast({ type: 'success', title: 'Demande envoyée', description: `Demande pour "${form.song_title}" créée.` });
      setShowCreate(false);
      setForm({ song_title: '', requested_by_name: '', notes: '' });
    } catch {
      toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer la demande.' });
    }
  }

  const columns: Column<Record<string, unknown> & { id: string }>[] = [
    {
      key: 'song_title',
      header: 'Chant demandé',
      render: (item) => <span className="font-medium text-white/90">{String(item.song_title ?? '')}</span>,
    },
    {
      key: 'requested_by_name',
      header: 'Demandé par',
      render: (item) => <span className="text-white/70">{String(item.requested_by_name ?? item.requested_by ?? '—')}</span>,
    },
    {
      key: 'status',
      header: 'Statut',
      render: (item) => {
        const s = String(item.status ?? 'pending');
        const v = s === 'approved' ? 'success' : s === 'rejected' ? 'destructive' : 'warning';
        const l = s === 'approved' ? 'Approuvée' : s === 'rejected' ? 'Rejetée' : 'En attente';
        return <Badge variant={v}>{l}</Badge>;
      },
    },
    {
      key: 'created_at',
      header: 'Date',
      render: (item) => <span className="text-white/50">{formatDate(String(item.created_at ?? ''))}</span>,
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-white/50">{totalCount ?? 0} demande{(totalCount ?? 0) !== 1 ? 's' : ''}</p>
        <Button size="sm" onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4 mr-1.5" />
          Nouvelle demande
        </Button>
      </div>
      <InfiniteScrollTable columns={columns} data={results} totalCount={totalCount} isLoading={isLoading} fetchNextPage={fetchNextPage} hasNextPage={hasNextPage} isFetchingNextPage={isFetchingNextPage} error={error} emptyMessage="Aucune demande de chant" />
      <Dialog open={showCreate} onClose={() => setShowCreate(false)}>
        <DialogHeader>
          <DialogTitle>Nouvelle demande de chant</DialogTitle>
          <DialogDescription>Demandez qu&apos;un chant soit ajouté à un service</DialogDescription>
          <DialogClose onClose={() => setShowCreate(false)} />
        </DialogHeader>
        <DialogContent>
          <div className="space-y-4">
            <div>
              <label className="text-xs text-white/50 mb-1.5 block">Titre du chant *</label>
              <Input placeholder="Nom du chant..." value={form.song_title} onChange={(e) => setForm((f) => ({ ...f, song_title: e.target.value }))} />
            </div>
            <div>
              <label className="text-xs text-white/50 mb-1.5 block">Demandé par</label>
              <Input placeholder="Votre nom..." value={form.requested_by_name} onChange={(e) => setForm((f) => ({ ...f, requested_by_name: e.target.value }))} />
            </div>
            <div>
              <label className="text-xs text-white/50 mb-1.5 block">Notes</label>
              <Textarea placeholder="Raison de la demande..." value={form.notes} onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))} />
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setShowCreate(false)}>Annuler</Button>
          <Button onClick={handleSubmit} disabled={createRequest.isPending}>{createRequest.isPending ? 'Envoi...' : 'Envoyer la demande'}</Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Live Streams Tab ────────────────────────────────────────────────────────

function LiveStreamsTab() {
  const { toast } = useToast();
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ title: '', url: '', platform: 'youtube', scheduled_start: '' });
  const createStream = useCreateLiveStream();

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteLiveStreams();
  const results = (data?.pages.flatMap((p) => p.results) ?? []) as (Record<string, unknown> & { id: string })[];
  const totalCount = data?.pages[0]?.count;

  async function handleSubmit() {
    if (!form.title) {
      toast({ type: 'error', title: 'Champ requis', description: 'Le titre est obligatoire.' });
      return;
    }
    try {
      await createStream.mutateAsync(form);
      toast({ type: 'success', title: 'Diffusion créée', description: `"${form.title}" a été ajoutée.` });
      setShowCreate(false);
      setForm({ title: '', url: '', platform: 'youtube', scheduled_start: '' });
    } catch {
      toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer la diffusion.' });
    }
  }

  const columns: Column<Record<string, unknown> & { id: string }>[] = [
    {
      key: 'title',
      header: 'Titre',
      render: (item) => <span className="font-medium text-white/90">{String(item.title ?? '')}</span>,
    },
    {
      key: 'platform',
      header: 'Plateforme',
      render: (item) => <Badge variant="secondary">{String(item.platform ?? 'youtube')}</Badge>,
    },
    {
      key: 'status',
      header: 'Statut',
      render: (item) => {
        const s = String(item.status ?? 'scheduled');
        const v = s === 'live' ? 'success' : s === 'ended' ? 'secondary' : 'warning';
        const l = s === 'live' ? 'En direct' : s === 'ended' ? 'Terminé' : 'Planifié';
        return <Badge variant={v}>{l}</Badge>;
      },
    },
    {
      key: 'scheduled_start',
      header: 'Début prévu',
      render: (item) => <span className="text-white/50">{formatDate(String(item.scheduled_start ?? ''))}</span>,
    },
    {
      key: 'viewers_count',
      header: 'Spectateurs',
      render: (item) => <span className="text-white/60">{String(item.viewers_count ?? 0)}</span>,
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-white/50">{totalCount ?? 0} diffusion{(totalCount ?? 0) !== 1 ? 's' : ''}</p>
        <Button size="sm" onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4 mr-1.5" />
          Nouvelle diffusion
        </Button>
      </div>
      <InfiniteScrollTable columns={columns} data={results} totalCount={totalCount} isLoading={isLoading} fetchNextPage={fetchNextPage} hasNextPage={hasNextPage} isFetchingNextPage={isFetchingNextPage} error={error} emptyMessage="Aucune diffusion en direct" />
      <Dialog open={showCreate} onClose={() => setShowCreate(false)}>
        <DialogHeader>
          <DialogTitle>Nouvelle diffusion en direct</DialogTitle>
          <DialogDescription>Planifier une diffusion en direct</DialogDescription>
          <DialogClose onClose={() => setShowCreate(false)} />
        </DialogHeader>
        <DialogContent>
          <div className="space-y-4">
            <div>
              <label className="text-xs text-white/50 mb-1.5 block">Titre *</label>
              <Input placeholder="Culte du dimanche en direct..." value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} />
            </div>
            <div>
              <label className="text-xs text-white/50 mb-1.5 block">URL de diffusion</label>
              <Input type="url" placeholder="https://youtube.com/live/..." value={form.url} onChange={(e) => setForm((f) => ({ ...f, url: e.target.value }))} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-white/50 mb-1.5 block">Plateforme</label>
                <Select value={form.platform} onChange={(e) => setForm((f) => ({ ...f, platform: e.target.value }))}>
                  <option value="youtube">YouTube</option>
                  <option value="facebook">Facebook</option>
                  <option value="instagram">Instagram</option>
                  <option value="other">Autre</option>
                </Select>
              </div>
              <div>
                <label className="text-xs text-white/50 mb-1.5 block">Début prévu</label>
                <Input type="datetime-local" value={form.scheduled_start} onChange={(e) => setForm((f) => ({ ...f, scheduled_start: e.target.value }))} />
              </div>
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setShowCreate(false)}>Annuler</Button>
          <Button onClick={handleSubmit} disabled={createStream.isPending}>{createStream.isPending ? 'Création...' : 'Créer la diffusion'}</Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Sermon Series Tab ───────────────────────────────────────────────────────

function SermonSeriesTab() {
  const { toast } = useToast();
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ title: '', description: '', start_date: '' });
  const createSeries = useCreateSermonSeries();

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error,
  } = useInfiniteSermonSeries();
  const results = (data?.pages.flatMap((p) => p.results) ?? []) as (Record<string, unknown> & { id: string })[];
  const totalCount = data?.pages[0]?.count;

  async function handleSubmit() {
    if (!form.title) {
      toast({ type: 'error', title: 'Champ requis', description: 'Le titre est obligatoire.' });
      return;
    }
    try {
      await createSeries.mutateAsync(form);
      toast({ type: 'success', title: 'Série créée', description: `"${form.title}" a été créée.` });
      setShowCreate(false);
      setForm({ title: '', description: '', start_date: '' });
    } catch {
      toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer la série.' });
    }
  }

  const columns: Column<Record<string, unknown> & { id: string }>[] = [
    {
      key: 'title',
      header: 'Série',
      render: (item) => (
        <div>
          <p className="font-medium text-white/90">{String(item.title ?? '')}</p>
          {!!item.description && <p className="text-xs text-white/40 mt-0.5 truncate max-w-[250px]">{String(item.description)}</p>}
        </div>
      ),
    },
    {
      key: 'sermons_count',
      header: 'Prédications',
      render: (item) => <span className="text-white/60">{String(item.sermons_count ?? 0)}</span>,
    },
    {
      key: 'start_date',
      header: 'Début',
      render: (item) => <span className="text-white/50">{item.start_date ? formatDate(String(item.start_date)) : '—'}</span>,
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

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-white/50">{totalCount ?? 0} série{(totalCount ?? 0) !== 1 ? 's' : ''}</p>
        <Button size="sm" onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4 mr-1.5" />
          Nouvelle série
        </Button>
      </div>
      <InfiniteScrollTable columns={columns} data={results} totalCount={totalCount} isLoading={isLoading} fetchNextPage={fetchNextPage} hasNextPage={hasNextPage} isFetchingNextPage={isFetchingNextPage} error={error} emptyMessage="Aucune série de prédications" />
      <Dialog open={showCreate} onClose={() => setShowCreate(false)}>
        <DialogHeader>
          <DialogTitle>Nouvelle série de prédications</DialogTitle>
          <DialogDescription>Créer une série thématique de prédications</DialogDescription>
          <DialogClose onClose={() => setShowCreate(false)} />
        </DialogHeader>
        <DialogContent>
          <div className="space-y-4">
            <div>
              <label className="text-xs text-white/50 mb-1.5 block">Titre *</label>
              <Input placeholder="La foi en action..." value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} />
            </div>
            <div>
              <label className="text-xs text-white/50 mb-1.5 block">Description</label>
              <Textarea placeholder="Thème de la série..." value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} />
            </div>
            <div>
              <label className="text-xs text-white/50 mb-1.5 block">Date de début</label>
              <Input type="date" value={form.start_date} onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value }))} />
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setShowCreate(false)}>Annuler</Button>
          <Button onClick={handleSubmit} disabled={createSeries.isPending}>{createSeries.isPending ? 'Création...' : 'Créer la série'}</Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ─── Stats ────────────────────────────────────────────────────────────────────

function WorshipStats() {
  const now = new Date();
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0];
  const monthEnd = new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().split('T')[0];

  const monthParams = new URLSearchParams({ date_after: monthStart, date_before: monthEnd });
  const { data: servicesData, isLoading: servicesLoading } = useWorshipServices(monthParams.toString());
  const { data: songsData, isLoading: songsLoading } = useSongs();
  const { data: myData, isLoading: myLoading } = useMyAssignments();

  const upcomingParams = new URLSearchParams({ date_after: now.toISOString().split('T')[0] });
  const { data: rehearsalsData, isLoading: rehearsalsLoading } = useRehearsals(upcomingParams.toString());

  const activeAssignments = ((myData?.results ?? []) as AssignmentRecord[]).filter(
    (a) => a.status === 'assigned' || a.status === 'confirmed'
  ).length;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        icon={Calendar}
        label="Services ce mois"
        value={servicesData?.count ?? 0}
        isLoading={servicesLoading}
        accent="bg-purple-500/20 text-purple-400"
      />
      <StatCard
        icon={Music}
        label="Chants en bibliothèque"
        value={songsData?.count ?? 0}
        isLoading={songsLoading}
        accent="bg-blue-500/20 text-blue-400"
      />
      <StatCard
        icon={UserCheck}
        label="Assignments actifs"
        value={activeAssignments}
        isLoading={myLoading}
        accent="bg-emerald-500/20 text-emerald-400"
      />
      <StatCard
        icon={Clock}
        label="Répétitions à venir"
        value={rehearsalsData?.count ?? 0}
        isLoading={rehearsalsLoading}
        accent="bg-amber-500/20 text-amber-400"
      />
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function WorshipPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Culte</h1>
        <p className="text-white/50 text-sm mt-1">
          Services, chants, prédications, setlists et équipe de louange
        </p>
      </div>

      {/* Stats */}
      <WorshipStats />

      {/* Tabs */}
      <Tabs defaultValue="services">
        <div className="overflow-x-auto">
          <TabsList className="w-max min-w-full sm:w-auto">
            <TabsTrigger value="services">
              <Calendar className="h-4 w-4 mr-1.5 inline-block" />
              Services
            </TabsTrigger>
            <TabsTrigger value="chants">
              <Music className="h-4 w-4 mr-1.5 inline-block" />
              Chants
            </TabsTrigger>
            <TabsTrigger value="predications">
              <BookOpen className="h-4 w-4 mr-1.5 inline-block" />
              Prédications
            </TabsTrigger>
            <TabsTrigger value="setlists">
              <ListMusic className="h-4 w-4 mr-1.5 inline-block" />
              Setlists
            </TabsTrigger>
            <TabsTrigger value="assignments">
              <UserCheck className="h-4 w-4 mr-1.5 inline-block" />
              Assignments
            </TabsTrigger>
            <TabsTrigger value="repetitions">
              <Mic2 className="h-4 w-4 mr-1.5 inline-block" />
              Répétitions
            </TabsTrigger>
            <TabsTrigger value="demandes">
              <HandMetal className="h-4 w-4 mr-1.5 inline-block" />
              Demandes
            </TabsTrigger>
            <TabsTrigger value="diffusion">
              <Radio className="h-4 w-4 mr-1.5 inline-block" />
              Diffusion
            </TabsTrigger>
            <TabsTrigger value="series">
              <Library className="h-4 w-4 mr-1.5 inline-block" />
              Séries
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="services">
          <ServicesTab />
        </TabsContent>

        <TabsContent value="chants">
          <SongsTab />
        </TabsContent>

        <TabsContent value="predications">
          <SermonsTab />
        </TabsContent>

        <TabsContent value="setlists">
          <SetlistsTab />
        </TabsContent>

        <TabsContent value="assignments">
          <AssignmentsTab />
        </TabsContent>

        <TabsContent value="repetitions">
          <RehearsalsTab />
        </TabsContent>

        <TabsContent value="demandes">
          <SongRequestsTab />
        </TabsContent>

        <TabsContent value="diffusion">
          <LiveStreamsTab />
        </TabsContent>

        <TabsContent value="series">
          <SermonSeriesTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
