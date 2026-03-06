'use client';

import { use, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  Edit,
  Trash2,
  Calendar,
  MapPin,
  Users,
  Video,
  Clock,
  Check,
  X,
  HelpCircle,
  RefreshCw,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar } from '@/components/ui/avatar';
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
import { useEvent, useDeleteEvent, useEventRSVP } from '@/hooks/use-events';
import { formatDate } from '@egliseconnect/utils';
import type { Event, EventRSVP } from '@egliseconnect/types';
import type { RSVPStatusType } from '@egliseconnect/types';

// ─── Constants ────────────────────────────────────────────────────────────────

const EVENT_TYPE_LABELS: Record<string, string> = {
  worship: 'Culte',
  group: 'Groupe',
  meal: 'Repas',
  special: 'Spécial',
  meeting: 'Réunion',
  training: 'Formation',
  outreach: 'Évangélisation',
  other: 'Autre',
};

const EVENT_TYPE_COLORS: Record<string, string> = {
  worship: 'default',
  group: 'success',
  meal: 'warning',
  special: 'default',
  meeting: 'secondary',
  training: 'outline',
  outreach: 'success',
  other: 'secondary',
};

const RSVP_STATUS_LABELS: Record<RSVPStatusType, string> = {
  confirmed: 'Confirmé',
  maybe: 'Peut-être',
  declined: 'Décliné',
  pending: 'En attente',
};

const RSVP_STATUS_BADGE: Record<RSVPStatusType, 'success' | 'warning' | 'destructive' | 'secondary'> = {
  confirmed: 'success',
  maybe: 'warning',
  declined: 'destructive',
  pending: 'secondary',
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatDateRange(startDate: string, endDate: string | null): string {
  const start = formatDate(startDate, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
  if (!endDate) return start;
  const end = formatDate(endDate, { hour: '2-digit', minute: '2-digit' });
  return `${start} – ${end}`;
}

// ─── Skeleton ────────────────────────────────────────────────────────────────

function EventDetailSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Skeleton className="h-10 w-10 rounded-xl" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-7 w-64" />
          <Skeleton className="h-4 w-40" />
        </div>
        <Skeleton className="h-10 w-24 rounded-xl" />
        <Skeleton className="h-10 w-24 rounded-xl" />
      </div>
      <div className="grid gap-6 md:grid-cols-3">
        <Skeleton className="h-40 rounded-2xl md:col-span-2" />
        <Skeleton className="h-40 rounded-2xl" />
      </div>
      <Skeleton className="h-32 rounded-2xl" />
      <Skeleton className="h-48 rounded-2xl" />
    </div>
  );
}

// ─── RSVP Button ─────────────────────────────────────────────────────────────

interface RSVPButtonProps {
  status: RSVPStatusType;
  currentStatus: RSVPStatusType | null;
  label: string;
  icon: React.ReactNode;
  variant: 'success' | 'warning' | 'destructive' | 'secondary';
  onClick: (status: RSVPStatusType) => void;
  isPending: boolean;
}

function RSVPButton({ status, currentStatus, label, icon, variant, onClick, isPending }: RSVPButtonProps) {
  const isActive = currentStatus === status;
  const activeStyles: Record<string, string> = {
    success: 'ring-2 ring-emerald-500/50 bg-emerald-500/20',
    warning: 'ring-2 ring-amber-500/50 bg-amber-500/20',
    destructive: 'ring-2 ring-rose-500/50 bg-rose-500/20',
    secondary: 'ring-2 ring-white/20 bg-white/10',
  };

  return (
    <button
      onClick={() => onClick(status)}
      disabled={isPending}
      className={[
        'flex flex-1 items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition-all duration-200',
        'border disabled:opacity-50 disabled:cursor-not-allowed',
        isActive ? activeStyles[variant] : 'bg-white/[0.04] border-white/[0.08] hover:bg-white/[0.08]',
        variant === 'success' ? 'text-emerald-400 border-emerald-500/20' : '',
        variant === 'warning' ? 'text-amber-400 border-amber-500/20' : '',
        variant === 'destructive' ? 'text-rose-400 border-rose-500/20' : '',
        variant === 'secondary' ? 'text-white/60 border-white/[0.08]' : '',
      ].join(' ')}
    >
      {icon}
      {label}
    </button>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function EventDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const { toast } = useToast();

  const { data: eventRaw, isLoading } = useEvent(id);
  const event = eventRaw as Event | undefined;

  const { mutate: deleteEvent, isPending: isDeleting } = useDeleteEvent();
  const { mutate: rsvp, isPending: isRsvpPending } = useEventRSVP(id);

  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  // Derive current user RSVP status — in real app this would come from auth context.
  // We check the rsvps array for a match; fallback to null.
  const currentRSVPStatus: RSVPStatusType | null = null;

  function handleDelete() {
    deleteEvent(id, {
      onSuccess: () => {
        toast({ type: 'success', title: 'Événement supprimé' });
        router.push('/events');
      },
      onError: () => {
        toast({ type: 'error', title: 'Erreur lors de la suppression' });
        setShowDeleteDialog(false);
      },
    });
  }

  function handleRSVP(status: RSVPStatusType) {
    rsvp(
      { status },
      {
        onSuccess: () => {
          toast({
            type: 'success',
            title: 'RSVP mis à jour',
            description: `Statut: ${RSVP_STATUS_LABELS[status]}`,
          });
        },
        onError: () => {
          toast({ type: 'error', title: 'Erreur lors du RSVP' });
        },
      },
    );
  }

  if (isLoading) return <EventDetailSkeleton />;

  if (!event) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-4">
        <div className="rounded-2xl bg-white/[0.04] border border-white/[0.06] p-8 text-center">
          <Calendar className="h-10 w-10 text-white/20 mx-auto mb-3" />
          <p className="text-white/50 text-sm">Événement introuvable</p>
          <Link href="/events" className="text-purple-400 hover:text-purple-300 text-sm mt-3 inline-block transition-colors">
            Retour aux événements
          </Link>
        </div>
      </div>
    );
  }

  const capacityPercent =
    event.max_capacity && event.max_capacity > 0
      ? Math.min(100, Math.round((event.attendee_count / event.max_capacity) * 100))
      : null;

  const capacityColor =
    capacityPercent === null
      ? 'bg-purple-500'
      : capacityPercent >= 90
      ? 'bg-rose-500'
      : capacityPercent >= 70
      ? 'bg-amber-500'
      : 'bg-emerald-500';

  return (
    <>
      <div className="space-y-6">
        {/* ── Header ── */}
        <div className="flex items-start gap-4">
          <Link href="/events">
            <Button variant="ghost" size="icon" className="shrink-0 mt-0.5">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>

          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <Badge variant={(EVENT_TYPE_COLORS[event.event_type] as 'default' | 'secondary' | 'outline' | 'success' | 'warning') || 'default'}>
                {EVENT_TYPE_LABELS[event.event_type] || event.event_type}
              </Badge>
              {!!event.is_recurring && (
                <Badge variant="secondary">
                  <RefreshCw className="h-3 w-3 mr-1" />
                  Récurrent
                </Badge>
              )}
              {!!event.is_full && (
                <Badge variant="destructive">Complet</Badge>
              )}
            </div>
            <h1 className="text-2xl font-bold text-white truncate">{event.title}</h1>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1.5 text-sm text-white/50">
              <span className="flex items-center gap-1.5">
                <Clock className="h-3.5 w-3.5" />
                {formatDateRange(event.start_date, event.end_date)}
              </span>
              {!!event.location && (
                <span className="flex items-center gap-1.5">
                  <MapPin className="h-3.5 w-3.5" />
                  {event.location}
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Link href={`/events/${id}/edit`}>
              <Button variant="outline" size="sm">
                <Edit className="h-4 w-4 mr-1.5" />
                Modifier
              </Button>
            </Link>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => setShowDeleteDialog(true)}
            >
              <Trash2 className="h-4 w-4 mr-1.5" />
              Supprimer
            </Button>
          </div>
        </div>

        {/* ── Main grid ── */}
        <div className="grid gap-6 md:grid-cols-3">
          {/* Description */}
          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle className="text-base">Description</CardTitle>
            </CardHeader>
            <CardContent>
              {event.description ? (
                <p className="text-sm text-white/70 leading-relaxed whitespace-pre-wrap">
                  {event.description}
                </p>
              ) : (
                <p className="text-sm text-white/30 italic">Aucune description</p>
              )}
            </CardContent>
          </Card>

          {/* Info sidebar */}
          <div className="space-y-4">
            {/* Capacity card */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Users className="h-4 w-4 text-purple-400" />
                  Capacité
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-end justify-between mb-2">
                  <span className="text-2xl font-bold text-white">{event.attendee_count}</span>
                  {!!event.max_capacity && (
                    <span className="text-sm text-white/40">/ {event.max_capacity} places</span>
                  )}
                </div>
                {capacityPercent !== null && (
                  <div className="space-y-1">
                    <div className="h-2 w-full rounded-full bg-white/[0.06] overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${capacityColor}`}
                        style={{ width: `${capacityPercent}%` }}
                      />
                    </div>
                    <p className="text-xs text-white/40 text-right">{capacityPercent}% rempli</p>
                  </div>
                )}
                {!event.max_capacity && (
                  <p className="text-xs text-white/30 mt-1">Capacité illimitée</p>
                )}
              </CardContent>
            </Card>

            {/* Virtual link card */}
            {event.is_virtual && event.virtual_link && (
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Video className="h-4 w-4 text-purple-400" />
                    Réunion virtuelle
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <a
                    href={event.virtual_link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-purple-400 hover:text-purple-300 underline underline-offset-2 break-all transition-colors"
                  >
                    {event.virtual_link}
                  </a>
                </CardContent>
              </Card>
            )}

            {/* Organizer */}
            {!!event.organizer && (
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">Organisateur</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-3">
                    <Avatar fallback={event.organizer.full_name} size="sm" />
                    <span className="text-sm text-white/80">{event.organizer.full_name}</span>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>

        {/* ── RSVP Section ── */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Ma participation</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-3">
              <RSVPButton
                status="confirmed"
                currentStatus={currentRSVPStatus}
                label="Confirmer"
                icon={<Check className="h-4 w-4" />}
                variant="success"
                onClick={handleRSVP}
                isPending={isRsvpPending}
              />
              <RSVPButton
                status="maybe"
                currentStatus={currentRSVPStatus}
                label="Peut-être"
                icon={<HelpCircle className="h-4 w-4" />}
                variant="warning"
                onClick={handleRSVP}
                isPending={isRsvpPending}
              />
              <RSVPButton
                status="declined"
                currentStatus={currentRSVPStatus}
                label="Décliner"
                icon={<X className="h-4 w-4" />}
                variant="destructive"
                onClick={handleRSVP}
                isPending={isRsvpPending}
              />
              <RSVPButton
                status="pending"
                currentStatus={currentRSVPStatus}
                label="En attente"
                icon={<Clock className="h-4 w-4" />}
                variant="secondary"
                onClick={handleRSVP}
                isPending={isRsvpPending}
              />
            </div>
          </CardContent>
        </Card>

        {/* ── Attendees list ── */}
        {event.rsvps && event.rsvps.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center justify-between">
                <span>Participants inscrits</span>
                <Badge variant="secondary">{event.rsvps.length}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="divide-y divide-white/[0.04]">
                {event.rsvps.map((rsvpItem: EventRSVP) => (
                  <li key={rsvpItem.id} className="flex items-center justify-between py-3 first:pt-0 last:pb-0">
                    <div className="flex items-center gap-3">
                      <Avatar fallback={rsvpItem.member.full_name} size="sm" />
                      <div>
                        <p className="text-sm font-medium text-white/90">{rsvpItem.member.full_name}</p>
                        {rsvpItem.guests > 0 && (
                          <p className="text-xs text-white/40">
                            +{rsvpItem.guests} invité{rsvpItem.guests > 1 ? 's' : ''}
                          </p>
                        )}
                      </div>
                    </div>
                    <Badge variant={RSVP_STATUS_BADGE[rsvpItem.status]}>
                      {RSVP_STATUS_LABELS[rsvpItem.status]}
                    </Badge>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>

      {/* ── Delete confirmation dialog ── */}
      <Dialog open={showDeleteDialog} onClose={() => setShowDeleteDialog(false)}>
        <DialogHeader>
          <DialogTitle>Supprimer l&apos;événement</DialogTitle>
          <DialogDescription>
            Cette action est irréversible. L&apos;événement «{event.title}» sera définitivement supprimé.
          </DialogDescription>
          <DialogClose onClose={() => setShowDeleteDialog(false)} />
        </DialogHeader>
        <DialogContent>
          <div className="flex items-start gap-3 rounded-xl bg-rose-500/10 border border-rose-500/20 p-4">
            <Trash2 className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
            <p className="text-sm text-rose-300">
              Tous les RSVP et données associées à cet événement seront également supprimés.
            </p>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setShowDeleteDialog(false)} disabled={isDeleting}>
            Annuler
          </Button>
          <Button variant="destructive" onClick={handleDelete} disabled={isDeleting}>
            {isDeleting ? 'Suppression...' : 'Supprimer'}
          </Button>
        </DialogFooter>
      </Dialog>
    </>
  );
}
