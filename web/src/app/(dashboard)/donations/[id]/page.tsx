'use client';

import { use, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  Edit,
  Trash2,
  Printer,
  Download,
  DollarSign,
  Receipt,
  User,
  CreditCard,
  Calendar,
  FileText,
  AlertTriangle,
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
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/components/ui/toast';
import { useDonation, useUpdateDonation, useDeleteDonation } from '@/hooks/use-donations';
import {
  DONATION_TYPE_LABELS,
  type DonationTypeValue,
  type PaymentMethodType,
} from '@egliseconnect/types';
import { formatCurrency, formatDate } from '@egliseconnect/utils';

// ─── Payment method labels ────────────────────────────────────────────────────

const PAYMENT_METHOD_LABELS: Record<PaymentMethodType, string> = {
  cash: 'Espèces',
  check: 'Chèque',
  card: 'Carte',
  bank_transfer: 'Virement bancaire',
  online: 'En ligne',
  other: 'Autre',
};

const PAYMENT_METHOD_COLORS: Record<PaymentMethodType, string> = {
  cash: 'success',
  check: 'warning',
  card: 'default',
  bank_transfer: 'secondary',
  online: 'default',
  other: 'secondary',
} as const;

const DONATION_TYPE_COLORS: Record<DonationTypeValue, string> = {
  tithe: 'default',
  offering: 'success',
  special: 'warning',
  campaign: 'default',
  building: 'warning',
  missions: 'secondary',
  other: 'secondary',
} as const;

// ─── Skeleton loader ─────────────────────────────────────────────────────────

function DonationDetailSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Skeleton className="h-9 w-9 rounded-xl" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>
        <Skeleton className="h-9 w-24" />
        <Skeleton className="h-9 w-24" />
      </div>

      {/* Amount hero */}
      <Skeleton className="h-32 w-full rounded-2xl" />

      {/* Info cards grid */}
      <div className="grid gap-4 md:grid-cols-2">
        <Skeleton className="h-40 rounded-2xl" />
        <Skeleton className="h-40 rounded-2xl" />
        <Skeleton className="h-40 rounded-2xl" />
        <Skeleton className="h-32 rounded-2xl" />
      </div>
    </div>
  );
}

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

// ─── Edit dialog ─────────────────────────────────────────────────────────────

interface EditDialogProps {
  open: boolean;
  onClose: () => void;
  donationId: string;
  initialAmount: string;
  initialType: DonationTypeValue;
  initialNotes: string;
}

function EditDialog({
  open,
  onClose,
  donationId,
  initialAmount,
  initialType,
  initialNotes,
}: EditDialogProps) {
  const { toast } = useToast();
  const { mutate: updateDonation, isPending } = useUpdateDonation(donationId);

  const [amount, setAmount] = useState(initialAmount);
  const [donationType, setDonationType] = useState<DonationTypeValue>(initialType);
  const [notes, setNotes] = useState(initialNotes);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const parsed = parseFloat(amount);
    if (isNaN(parsed) || parsed <= 0) {
      toast({ type: 'error', title: 'Montant invalide', description: 'Veuillez entrer un montant valide.' });
      return;
    }
    updateDonation(
      { amount, donation_type: donationType, notes },
      {
        onSuccess: () => {
          toast({ type: 'success', title: 'Don mis à jour', description: 'Les modifications ont été enregistrées.' });
          onClose();
        },
        onError: (err) => {
          toast({
            type: 'error',
            title: 'Erreur',
            description: err instanceof Error ? err.message : 'Une erreur est survenue.',
          });
        },
      },
    );
  }

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogClose onClose={onClose} />
      <DialogHeader>
        <DialogTitle>Modifier le don</DialogTitle>
        <DialogDescription>Modifiez les détails de ce don.</DialogDescription>
      </DialogHeader>
      <form onSubmit={handleSubmit}>
        <DialogContent className="space-y-4">
          {/* Amount */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-white/70">Montant (CAD) *</label>
            <div className="relative">
              <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm text-white/40">
                $
              </span>
              <Input
                type="number"
                step="0.01"
                min="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="pl-7"
                required
              />
            </div>
          </div>

          {/* Type */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-white/70">Type de don *</label>
            <select
              value={donationType}
              onChange={(e) => setDonationType(e.target.value as DonationTypeValue)}
              className="flex h-10 w-full rounded-xl bg-white/[0.06] border border-white/[0.08] px-3 py-2 text-sm text-white/90 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/30 transition-all duration-200"
              required
            >
              {Object.entries(DONATION_TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value} className="bg-[#1a1145] text-white">
                  {label}
                </option>
              ))}
            </select>
          </div>

          {/* Notes */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-white/70">Notes</label>
            <Textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Notes optionnelles..."
              rows={3}
            />
          </div>
        </DialogContent>
        <DialogFooter>
          <Button type="button" variant="ghost" onClick={onClose} disabled={isPending}>
            Annuler
          </Button>
          <Button type="submit" disabled={isPending}>
            {isPending ? 'Enregistrement...' : 'Enregistrer'}
          </Button>
        </DialogFooter>
      </form>
    </Dialog>
  );
}

// ─── Delete confirmation dialog ───────────────────────────────────────────────

interface DeleteDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  isPending: boolean;
  donationNumber: string;
}

function DeleteDialog({ open, onClose, onConfirm, isPending, donationNumber }: DeleteDialogProps) {
  return (
    <Dialog open={open} onClose={onClose} className="max-w-md">
      <DialogClose onClose={onClose} />
      <DialogHeader>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-rose-500/20">
            <AlertTriangle className="h-5 w-5 text-rose-400" />
          </div>
          <div>
            <DialogTitle>Supprimer le don</DialogTitle>
            <DialogDescription>Cette action est irréversible.</DialogDescription>
          </div>
        </div>
      </DialogHeader>
      <DialogContent>
        <p className="text-sm text-white/60">
          Voulez-vous vraiment supprimer le don{' '}
          <span className="font-semibold text-white/90">{donationNumber}</span> ? Cette action ne
          peut pas être annulée.
        </p>
      </DialogContent>
      <DialogFooter>
        <Button type="button" variant="ghost" onClick={onClose} disabled={isPending}>
          Annuler
        </Button>
        <Button
          type="button"
          className="bg-rose-500/20 text-rose-400 border border-rose-500/30 hover:bg-rose-500/30"
          onClick={onConfirm}
          disabled={isPending}
        >
          {isPending ? 'Suppression...' : 'Supprimer'}
        </Button>
      </DialogFooter>
    </Dialog>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function DonationDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const { toast } = useToast();

  const { data: donation, isLoading, isError } = useDonation(id);
  const { mutate: deleteDonation, isPending: isDeleting } = useDeleteDonation();

  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  function handleDelete() {
    deleteDonation(id, {
      onSuccess: () => {
        toast({ type: 'success', title: 'Don supprimé', description: 'Le don a été supprimé avec succès.' });
        router.push('/donations');
      },
      onError: (err) => {
        toast({
          type: 'error',
          title: 'Erreur de suppression',
          description: err instanceof Error ? err.message : 'Une erreur est survenue.',
        });
        setDeleteOpen(false);
      },
    });
  }

  function handlePrint() {
    window.print();
  }

  // ── Loading state ──────────────────────────────────────────────────────────
  if (isLoading) {
    return <DonationDetailSkeleton />;
  }

  // ── Error / not found ──────────────────────────────────────────────────────
  if (isError || !donation) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-white/[0.05]">
          <DollarSign className="h-8 w-8 text-white/30" />
        </div>
        <p className="text-lg font-medium text-white/70">Don introuvable</p>
        <p className="mt-1 text-sm text-white/40">
          Ce don n&apos;existe pas ou a été supprimé.
        </p>
        <Link href="/donations">
          <Button variant="outline" className="mt-6">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Retour aux dons
          </Button>
        </Link>
      </div>
    );
  }

  const donorName = donation.is_anonymous
    ? 'Anonyme'
    : donation.member?.full_name ?? 'Inconnu';

  const donorInitials = donation.is_anonymous
    ? 'AN'
    : (donation.member?.full_name ?? 'IN');

  const donationTypeLabel =
    DONATION_TYPE_LABELS[donation.donation_type] ?? donation.donation_type;

  const paymentMethodLabel =
    PAYMENT_METHOD_LABELS[donation.payment_method] ?? donation.payment_method;

  return (
    <>
      <div className="space-y-6">
        {/* ── Header ──────────────────────────────────────────────────────── */}
        <div className="flex flex-wrap items-center gap-3">
          <Link href="/donations">
            <Button variant="ghost" size="icon" className="shrink-0">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>

          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-xl font-bold text-white/90">Détail du don</h1>
              <Badge variant="secondary" className="font-mono text-xs">
                {donation.donation_number}
              </Badge>
              {!!donation.is_anonymous && (
                <Badge variant="warning">Anonyme</Badge>
              )}
              {!!donation.is_recurring && (
                <Badge variant="default">Récurrent</Badge>
              )}
            </div>
            <p className="mt-0.5 text-sm text-white/40">
              Enregistré le {formatDate(donation.created_at, { year: 'numeric', month: 'long', day: 'numeric' })}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={handlePrint}
              title="Imprimer"
              className="text-white/60 hover:text-white/90"
            >
              <Printer className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setEditOpen(true)}
            >
              <Edit className="mr-2 h-4 w-4" />
              Modifier
            </Button>
            <Button
              size="sm"
              className="bg-rose-500/20 text-rose-400 border border-rose-500/30 hover:bg-rose-500/30"
              onClick={() => setDeleteOpen(true)}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Supprimer
            </Button>
          </div>
        </div>

        {/* ── Amount hero ──────────────────────────────────────────────────── */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-purple-600/20 via-purple-800/10 to-transparent border border-purple-500/20 p-6 shadow-[0_8px_32px_rgba(0,0,0,0.2)]">
          {/* Background decoration */}
          <div className="pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full bg-purple-500/10 blur-2xl" />
          <div className="pointer-events-none absolute -bottom-4 right-16 h-20 w-20 rounded-full bg-violet-500/10 blur-xl" />

          <div className="relative flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-white/50">Montant du don</p>
              <p className="mt-1 text-4xl font-bold tracking-tight text-white">
                {formatCurrency(donation.amount)}
              </p>
              <p className="mt-2 text-sm text-white/40">
                <Calendar className="mr-1.5 inline-block h-3.5 w-3.5 align-middle" />
                {formatDate(donation.date, { year: 'numeric', month: 'long', day: 'numeric' })}
              </p>
            </div>
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-purple-500/20 ring-2 ring-purple-500/30">
              <DollarSign className="h-8 w-8 text-purple-300" />
            </div>
          </div>
        </div>

        {/* ── Info cards grid ───────────────────────────────────────────────── */}
        <div className="grid gap-4 md:grid-cols-2">
          {/* Donor info */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <User className="h-4 w-4 text-white/50" />
                Informations du donateur
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3">
                <Avatar
                  fallback={donorInitials}
                  size="lg"
                  className="ring-2 ring-purple-500/20"
                />
                <div>
                  <p className="font-medium text-white/90">{donorName}</p>
                  {donation.is_anonymous ? (
                    <p className="text-xs text-white/40">Don anonyme — identité masquée</p>
                  ) : donation.member ? (
                    <Link
                      href={`/members/${donation.member.id}`}
                      className="text-xs text-purple-400 hover:text-purple-300 transition-colors"
                    >
                      Voir le profil membre
                    </Link>
                  ) : (
                    <p className="text-xs text-white/40">Aucun profil lié</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Payment info */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <CreditCard className="h-4 w-4 text-white/50" />
                Informations de paiement
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <InfoItem icon={DollarSign} label="Type de don">
                <Badge
                  variant={(DONATION_TYPE_COLORS[donation.donation_type] as 'default' | 'success' | 'warning' | 'secondary') ?? 'secondary'}
                >
                  {donationTypeLabel}
                </Badge>
              </InfoItem>
              <InfoItem icon={CreditCard} label="Méthode de paiement">
                <Badge
                  variant={(PAYMENT_METHOD_COLORS[donation.payment_method] as 'default' | 'success' | 'warning' | 'secondary') ?? 'secondary'}
                >
                  {paymentMethodLabel}
                </Badge>
              </InfoItem>
              {!!donation.campaign && (
                <InfoItem icon={FileText} label="Campagne">
                  <span className="font-medium text-purple-300">{donation.campaign.name}</span>
                </InfoItem>
              )}
            </CardContent>
          </Card>

          {/* Tax receipt */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Receipt className="h-4 w-4 text-white/50" />
                Reçu fiscal
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <InfoItem icon={Receipt} label="Numéro de reçu">
                {donation.receipt_number ? (
                  <span className="font-mono text-white/90">{donation.receipt_number}</span>
                ) : (
                  <span className="text-white/40">Non attribué</span>
                )}
              </InfoItem>
              <InfoItem icon={Calendar} label="Statut du reçu">
                {donation.receipt_issued ? (
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="success">Émis</Badge>
                    {!!donation.receipt_issued_date && (
                      <span className="text-xs text-white/40">
                        le{' '}
                        {formatDate(donation.receipt_issued_date, {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                        })}
                      </span>
                    )}
                  </div>
                ) : (
                  <Badge variant="secondary">Non émis</Badge>
                )}
              </InfoItem>

              {!!donation.receipt_issued && (
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-2 w-full"
                  onClick={() =>
                    toast({
                      type: 'info',
                      title: 'Téléchargement',
                      description: 'La génération du reçu PDF sera disponible prochainement.',
                    })
                  }
                >
                  <Download className="mr-2 h-4 w-4" />
                  Télécharger le reçu PDF
                </Button>
              )}
            </CardContent>
          </Card>

          {/* Notes */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <FileText className="h-4 w-4 text-white/50" />
                Notes
              </CardTitle>
            </CardHeader>
            <CardContent>
              {donation.notes ? (
                <p className="whitespace-pre-wrap text-sm leading-relaxed text-white/70">
                  {donation.notes}
                </p>
              ) : (
                <p className="text-sm italic text-white/30">Aucune note associée à ce don.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* ── Dialogs ─────────────────────────────────────────────────────────── */}
      <EditDialog
        open={editOpen}
        onClose={() => setEditOpen(false)}
        donationId={id}
        initialAmount={donation.amount}
        initialType={donation.donation_type}
        initialNotes={donation.notes ?? ''}
      />

      <DeleteDialog
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        onConfirm={handleDelete}
        isPending={isDeleting}
        donationNumber={donation.donation_number}
      />
    </>
  );
}
