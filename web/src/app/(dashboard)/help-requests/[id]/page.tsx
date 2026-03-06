'use client';

import { use, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  Edit,
  CheckCircle2,
  AlertCircle,
  Clock,
  User,
  MessageSquare,
  Calendar,
  Tag,
  Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/components/ui/toast';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { formatDate } from '@egliseconnect/utils';

// ─── Types ───────────────────────────────────────────────────────────────────

interface HelpRequest {
  id: string;
  subject: string;
  description: string;
  status: string;
  priority: string;
  category?: { id: string; name: string };
  member?: { id: string; full_name: string };
  assigned_to?: { id: string; full_name: string };
  notes: string;
  created_at: string;
  updated_at: string;
}

// ─── Status & priority helpers ───────────────────────────────────────────────

const STATUS_LABELS: Record<string, string> = {
  new: 'Nouvelle',
  in_progress: 'En cours',
  resolved: 'Résolue',
  closed: 'Fermée',
};

const STATUS_VARIANTS: Record<string, 'default' | 'warning' | 'success' | 'secondary'> = {
  new: 'default',
  in_progress: 'warning',
  resolved: 'success',
  closed: 'secondary',
};

const PRIORITY_LABELS: Record<string, string> = {
  low: 'Basse',
  medium: 'Moyenne',
  high: 'Haute',
  urgent: 'Urgente',
};

const PRIORITY_VARIANTS: Record<string, 'default' | 'warning' | 'destructive' | 'secondary'> = {
  low: 'secondary',
  medium: 'default',
  high: 'warning',
  urgent: 'destructive',
};

// ─── Info item ───────────────────────────────────────────────────────────────

function InfoItem({
  icon: Icon,
  label,
  children,
}: {
  icon: React.ElementType;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-3">
      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/[0.06]">
        <Icon className="h-4 w-4 text-white/50" />
      </div>
      <div className="min-w-0">
        <p className="text-xs text-white/40">{label}</p>
        <div className="mt-0.5 text-sm text-white/80">{children}</div>
      </div>
    </div>
  );
}

// ─── Skeleton ────────────────────────────────────────────────────────────────

function DetailSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Skeleton className="h-9 w-9 rounded-xl" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-6 w-64" />
          <Skeleton className="h-4 w-32" />
        </div>
      </div>
      <Skeleton className="h-32 rounded-2xl" />
      <div className="grid gap-4 md:grid-cols-2">
        <Skeleton className="h-40 rounded-2xl" />
        <Skeleton className="h-40 rounded-2xl" />
      </div>
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function HelpRequestDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: request, isLoading } = useQuery<HelpRequest>({
    queryKey: ['help-requests', id],
    queryFn: () => api.helpRequests.get(id) as Promise<HelpRequest>,
    enabled: !!id,
  });

  const [comment, setComment] = useState('');

  const { mutate: addComment, isPending: commentPending } = useMutation({
    mutationFn: (text: string) => api.helpRequests.comment(id, { text }),
    onSuccess: () => {
      setComment('');
      queryClient.invalidateQueries({ queryKey: ['help-requests', id] });
      toast({ type: 'success', title: 'Commentaire ajouté' });
    },
  });

  const { mutate: resolve, isPending: resolvePending } = useMutation({
    mutationFn: () => api.helpRequests.resolve(id, { resolution_notes: 'Résolu' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['help-requests', id] });
      queryClient.invalidateQueries({ queryKey: ['help-requests'] });
      toast({ type: 'success', title: 'Demande résolue', description: 'La demande a été marquée comme résolue.' });
    },
  });

  if (isLoading) return <DetailSkeleton />;

  if (!request) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-white/[0.05]">
          <AlertCircle className="h-8 w-8 text-white/30" />
        </div>
        <p className="text-lg font-medium text-white/70">Demande introuvable</p>
        <Link href="/help-requests">
          <Button variant="outline" className="mt-6">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Retour aux demandes
          </Button>
        </Link>
      </div>
    );
  }

  const canResolve = request.status === 'new' || request.status === 'in_progress';

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-wrap items-center gap-3">
        <Link href="/help-requests">
          <Button variant="ghost" size="icon" className="shrink-0">
            <ArrowLeft className="h-5 w-5" />
          </Button>
        </Link>
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-xl font-bold text-white/90">{request.subject}</h1>
            <Badge variant={STATUS_VARIANTS[request.status] ?? 'secondary'}>
              {STATUS_LABELS[request.status] ?? request.status}
            </Badge>
            <Badge variant={PRIORITY_VARIANTS[request.priority] ?? 'secondary'}>
              {PRIORITY_LABELS[request.priority] ?? request.priority}
            </Badge>
          </div>
          <p className="mt-0.5 text-sm text-white/40">
            Créée le {formatDate(request.created_at, { year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>
        {canResolve && (
          <Button
            onClick={() => resolve()}
            disabled={resolvePending}
            className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/30"
          >
            {resolvePending ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <CheckCircle2 className="h-4 w-4 mr-2" />
            )}
            Marquer comme résolue
          </Button>
        )}
      </div>

      {/* ── Description ── */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Description</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-white/70 whitespace-pre-wrap leading-relaxed">
            {request.description || 'Aucune description fournie.'}
          </p>
        </CardContent>
      </Card>

      {/* ── Info grid ── */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <User className="h-4 w-4 text-white/50" />
              Personnes
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <InfoItem icon={User} label="Demandeur">
              {request.member ? (
                <Link
                  href={`/members/${request.member.id}`}
                  className="text-purple-400 hover:text-purple-300 transition-colors"
                >
                  {request.member.full_name}
                </Link>
              ) : (
                <span className="text-white/40">Non assigné</span>
              )}
            </InfoItem>
            <InfoItem icon={User} label="Assigné à">
              {request.assigned_to ? (
                <span>{request.assigned_to.full_name}</span>
              ) : (
                <span className="text-white/40">Non assigné</span>
              )}
            </InfoItem>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Tag className="h-4 w-4 text-white/50" />
              Détails
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <InfoItem icon={Tag} label="Catégorie">
              {request.category?.name ?? 'Non catégorisée'}
            </InfoItem>
            <InfoItem icon={Calendar} label="Dernière mise à jour">
              {formatDate(request.updated_at, { year: 'numeric', month: 'long', day: 'numeric' })}
            </InfoItem>
            <InfoItem icon={Clock} label="Statut">
              <Badge variant={STATUS_VARIANTS[request.status] ?? 'secondary'}>
                {STATUS_LABELS[request.status] ?? request.status}
              </Badge>
            </InfoItem>
          </CardContent>
        </Card>
      </div>

      {/* ── Notes ── */}
      {request.notes && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-white/70 whitespace-pre-wrap">{request.notes}</p>
          </CardContent>
        </Card>
      )}

      {/* ── Add comment ── */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <MessageSquare className="h-4 w-4 text-white/50" />
            Ajouter un commentaire
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Écrivez un commentaire..."
            rows={3}
          />
          <Button
            className="mt-3"
            onClick={() => comment.trim() && addComment(comment.trim())}
            disabled={!comment.trim() || commentPending}
          >
            {commentPending ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <MessageSquare className="h-4 w-4 mr-2" />
            )}
            Envoyer
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
