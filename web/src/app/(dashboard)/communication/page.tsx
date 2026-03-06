'use client';

import { useState } from 'react';
import {
  Mail,
  Bell,
  MessageSquare,
  Phone,
  FileText,
  Zap,
  Plus,
  Search,
  Send,
  CheckCheck,
  Clock,
  Users,
  TrendingUp,
  Eye,
  MessagesSquare,
  FlaskConical,
  Trophy,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { InfiniteScrollTable } from '@/components/ui/infinite-scroll-table';
import { InfiniteScrollList } from '@/components/ui/infinite-scroll-list';
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
import { useToast } from '@/components/ui/toast';
import {
  useCreateNewsletter,
  useSendNewsletter,
  useUnreadCount,
  useMarkNotificationRead,
  useCreateDirectMessage,
  useSendSms,
  useCreateEmailTemplate,
  useCreateAutomation,
  useInfiniteNewsletters,
  useInfiniteNotifications,
  useInfiniteDirectMessages,
  useInfiniteSmsMessages,
  useInfiniteEmailTemplates,
  useInfiniteAutomations,
  useInfiniteGroupChats,
  useCreateGroupChat,
  useInfiniteABTests,
  useCreateABTest,
  usePickABTestWinner,
} from '@/hooks/use-communication';

// ─── Type definitions ────────────────────────────────────────────────────────

interface Newsletter extends Record<string, unknown> {
  id: string;
  subject: string;
  status: string;
  recipients_count: number;
  opened_count: number;
  created_at: string;
  sent_at?: string;
}

interface Notification extends Record<string, unknown> {
  id: string;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  created_at: string;
}

interface DirectMessage extends Record<string, unknown> {
  id: string;
  sender_name: string;
  recipient_name: string;
  subject: string;
  body: string;
  is_read: boolean;
  created_at: string;
}

interface SmsMessage extends Record<string, unknown> {
  id: string;
  phone_number: string;
  message: string;
  status: string;
  created_at: string;
}

interface EmailTemplate extends Record<string, unknown> {
  id: string;
  name: string;
  subject: string;
  template_type: string;
  created_at: string;
}

interface Automation extends Record<string, unknown> {
  id: string;
  name: string;
  trigger_type: string;
  status: string;
  enrollment_count: number;
  created_at: string;
}

// ─── Status helpers ──────────────────────────────────────────────────────────

const newsletterStatusLabels: Record<string, string> = {
  draft: 'Brouillon',
  scheduled: 'Planifiée',
  sent: 'Envoyée',
  sending: 'En cours',
};

const newsletterStatusVariant: Record<string, 'secondary' | 'warning' | 'success' | 'default'> = {
  draft: 'secondary',
  scheduled: 'warning',
  sent: 'success',
  sending: 'default',
};

const notifTypeLabels: Record<string, string> = {
  info: 'Info',
  warning: 'Avertissement',
  success: 'Succès',
  error: 'Erreur',
  reminder: 'Rappel',
  announcement: 'Annonce',
};

const notifTypeVariant: Record<string, 'default' | 'warning' | 'success' | 'destructive' | 'outline'> = {
  info: 'default',
  warning: 'warning',
  success: 'success',
  error: 'destructive',
  reminder: 'outline',
  announcement: 'outline',
};

const smsStatusVariant: Record<string, 'success' | 'warning' | 'destructive' | 'secondary'> = {
  delivered: 'success',
  pending: 'warning',
  failed: 'destructive',
  sent: 'secondary',
};

const smsStatusLabels: Record<string, string> = {
  delivered: 'Livré',
  pending: 'En attente',
  failed: 'Échoué',
  sent: 'Envoyé',
};

const automationStatusVariant: Record<string, 'success' | 'secondary'> = {
  active: 'success',
  paused: 'secondary',
};

const automationStatusLabels: Record<string, string> = {
  active: 'Actif',
  paused: 'En pause',
};

const triggerTypeLabels: Record<string, string> = {
  new_member: 'Nouveau membre',
  birthday: 'Anniversaire',
  event_registration: 'Inscription événement',
  donation: 'Don reçu',
  absence: 'Absence prolongée',
  manual: 'Manuel',
};

const templateTypeLabels: Record<string, string> = {
  newsletter: 'Infolettre',
  welcome: 'Bienvenue',
  reminder: 'Rappel',
  notification: 'Notification',
  custom: 'Personnalisé',
};

// ─── Formatters ──────────────────────────────────────────────────────────────

function formatDate(dateStr: string) {
  if (!dateStr) return '—';
  return new Intl.DateTimeFormat('fr-CA', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(new Date(dateStr));
}

// ─── Stat Card ───────────────────────────────────────────────────────────────

function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  gradient,
}: {
  title: string;
  value: string | number;
  subtitle: string;
  icon: React.ElementType;
  gradient: string;
}) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-sm text-white/50">{title}</p>
            <p className="text-2xl font-bold text-white">{value}</p>
            <p className="text-xs text-white/40">{subtitle}</p>
          </div>
          <div className={`p-3 rounded-xl ${gradient}`}>
            <Icon className="h-6 w-6 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Create Newsletter Dialog ─────────────────────────────────────────────────

function CreateNewsletterDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const createNewsletter = useCreateNewsletter();
  const [form, setForm] = useState({
    subject: '',
    content: '',
    target_groups: 'all',
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    createNewsletter.mutate(
      { ...form },
      {
        onSuccess: () => {
          toast({ type: 'success', title: 'Infolettre créée', description: 'Le brouillon a été enregistré.' });
          setForm({ subject: '', content: '', target_groups: 'all' });
          onClose();
        },
        onError: () => {
          toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer l\'infolettre.' });
        },
      },
    );
  }

  return (
    <Dialog open={open} onClose={onClose} className="max-w-2xl">
      <DialogClose onClose={onClose} />
      <DialogHeader>
        <DialogTitle>Nouvelle infolettre</DialogTitle>
        <DialogDescription>Créer un brouillon d&apos;infolettre à envoyer à vos membres.</DialogDescription>
      </DialogHeader>
      <form onSubmit={handleSubmit}>
        <DialogContent className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-white/70">Sujet *</label>
            <Input
              placeholder="Objet de l'infolettre..."
              value={form.subject}
              onChange={(e) => setForm((p) => ({ ...p, subject: e.target.value }))}
              required
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-white/70">Destinataires</label>
            <Select
              value={form.target_groups}
              onChange={(e) => setForm((p) => ({ ...p, target_groups: e.target.value }))}
            >
              <option value="all">Tous les membres</option>
              <option value="active">Membres actifs</option>
              <option value="volunteers">Bénévoles</option>
              <option value="leaders">Responsables</option>
              <option value="new_members">Nouveaux membres</option>
            </Select>
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-white/70">Contenu *</label>
            <Textarea
              placeholder="Rédigez le contenu de votre infolettre ici..."
              className="min-h-[160px]"
              value={form.content}
              onChange={(e) => setForm((p) => ({ ...p, content: e.target.value }))}
              required
            />
          </div>
        </DialogContent>
        <DialogFooter>
          <Button type="button" variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button type="submit" disabled={createNewsletter.isPending}>
            {createNewsletter.isPending ? 'Enregistrement…' : 'Enregistrer le brouillon'}
          </Button>
        </DialogFooter>
      </form>
    </Dialog>
  );
}

// ─── Compose Message Dialog ───────────────────────────────────────────────────

function ComposeMessageDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const createMessage = useCreateDirectMessage();
  const [form, setForm] = useState({ recipient: '', subject: '', body: '' });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    createMessage.mutate(
      { ...form },
      {
        onSuccess: () => {
          toast({ type: 'success', title: 'Message envoyé', description: 'Votre message a été envoyé.' });
          setForm({ recipient: '', subject: '', body: '' });
          onClose();
        },
        onError: () => {
          toast({ type: 'error', title: 'Erreur', description: 'Impossible d\'envoyer le message.' });
        },
      },
    );
  }

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogClose onClose={onClose} />
      <DialogHeader>
        <DialogTitle>Nouveau message</DialogTitle>
        <DialogDescription>Envoyer un message direct à un membre.</DialogDescription>
      </DialogHeader>
      <form onSubmit={handleSubmit}>
        <DialogContent className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-white/70">Destinataire *</label>
            <Input
              placeholder="Nom ou courriel du destinataire..."
              value={form.recipient}
              onChange={(e) => setForm((p) => ({ ...p, recipient: e.target.value }))}
              required
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-white/70">Sujet *</label>
            <Input
              placeholder="Sujet du message..."
              value={form.subject}
              onChange={(e) => setForm((p) => ({ ...p, subject: e.target.value }))}
              required
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-white/70">Message *</label>
            <Textarea
              placeholder="Votre message..."
              className="min-h-[120px]"
              value={form.body}
              onChange={(e) => setForm((p) => ({ ...p, body: e.target.value }))}
              required
            />
          </div>
        </DialogContent>
        <DialogFooter>
          <Button type="button" variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button type="submit" disabled={createMessage.isPending}>
            <Send className="h-4 w-4 mr-2" />
            {createMessage.isPending ? 'Envoi…' : 'Envoyer'}
          </Button>
        </DialogFooter>
      </form>
    </Dialog>
  );
}

// ─── Compose SMS Dialog ───────────────────────────────────────────────────────

function ComposeSmsDialog({
  open,
  onClose,
  templates,
}: {
  open: boolean;
  onClose: () => void;
  templates: EmailTemplate[];
}) {
  const { toast } = useToast();
  const sendSms = useSendSms();
  const [form, setForm] = useState({ phone_number: '', message: '', template_id: '' });

  function handleTemplateChange(templateId: string) {
    const tpl = templates.find((t) => t.id === templateId);
    setForm((p) => ({
      ...p,
      template_id: templateId,
      message: tpl ? (tpl.subject as string) : p.message,
    }));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    sendSms.mutate(
      { phone_number: form.phone_number, message: form.message },
      {
        onSuccess: () => {
          toast({ type: 'success', title: 'SMS envoyé', description: 'Votre SMS a été envoyé.' });
          setForm({ phone_number: '', message: '', template_id: '' });
          onClose();
        },
        onError: () => {
          toast({ type: 'error', title: 'Erreur', description: 'Impossible d\'envoyer le SMS.' });
        },
      },
    );
  }

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogClose onClose={onClose} />
      <DialogHeader>
        <DialogTitle>Nouveau SMS</DialogTitle>
        <DialogDescription>Envoyer un message texte à un numéro de téléphone.</DialogDescription>
      </DialogHeader>
      <form onSubmit={handleSubmit}>
        <DialogContent className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-white/70">Numéro de téléphone *</label>
            <Input
              placeholder="+1 (514) 000-0000"
              value={form.phone_number}
              onChange={(e) => setForm((p) => ({ ...p, phone_number: e.target.value }))}
              required
            />
          </div>
          {templates.length > 0 && (
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-white/70">Modèle (optionnel)</label>
              <Select
                value={form.template_id}
                onChange={(e) => handleTemplateChange(e.target.value)}
              >
                <option value="">Aucun modèle</option>
                {templates.map((t) => (
                  <option key={t.id} value={t.id}>{t.name as string}</option>
                ))}
              </Select>
            </div>
          )}
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-white/70">Message *</label>
            <Textarea
              placeholder="Votre message SMS (max. 160 caractères)..."
              className="min-h-[100px]"
              maxLength={160}
              value={form.message}
              onChange={(e) => setForm((p) => ({ ...p, message: e.target.value }))}
              required
            />
            <p className="text-xs text-white/30 text-right">{form.message.length}/160</p>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button type="button" variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button type="submit" disabled={sendSms.isPending}>
            <Phone className="h-4 w-4 mr-2" />
            {sendSms.isPending ? 'Envoi…' : 'Envoyer SMS'}
          </Button>
        </DialogFooter>
      </form>
    </Dialog>
  );
}

// ─── Create Template Dialog ───────────────────────────────────────────────────

function CreateTemplateDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const createTemplate = useCreateEmailTemplate();
  const [form, setForm] = useState({
    name: '',
    subject: '',
    template_type: 'newsletter',
    body: '',
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    createTemplate.mutate(
      { ...form },
      {
        onSuccess: () => {
          toast({ type: 'success', title: 'Modèle créé', description: 'Le modèle a été enregistré.' });
          setForm({ name: '', subject: '', template_type: 'newsletter', body: '' });
          onClose();
        },
        onError: () => {
          toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer le modèle.' });
        },
      },
    );
  }

  return (
    <Dialog open={open} onClose={onClose} className="max-w-2xl">
      <DialogClose onClose={onClose} />
      <DialogHeader>
        <DialogTitle>Nouveau modèle</DialogTitle>
        <DialogDescription>Créer un modèle de courriel réutilisable.</DialogDescription>
      </DialogHeader>
      <form onSubmit={handleSubmit}>
        <DialogContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-white/70">Nom du modèle *</label>
              <Input
                placeholder="Ex: Bienvenue nouveau membre"
                value={form.name}
                onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
                required
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-white/70">Type</label>
              <Select
                value={form.template_type}
                onChange={(e) => setForm((p) => ({ ...p, template_type: e.target.value }))}
              >
                <option value="newsletter">Infolettre</option>
                <option value="welcome">Bienvenue</option>
                <option value="reminder">Rappel</option>
                <option value="notification">Notification</option>
                <option value="custom">Personnalisé</option>
              </Select>
            </div>
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-white/70">Sujet *</label>
            <Input
              placeholder="Sujet du courriel..."
              value={form.subject}
              onChange={(e) => setForm((p) => ({ ...p, subject: e.target.value }))}
              required
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-white/70">Corps du message *</label>
            <Textarea
              placeholder="Contenu du modèle. Utilisez {{nom}} pour personnaliser..."
              className="min-h-[160px]"
              value={form.body}
              onChange={(e) => setForm((p) => ({ ...p, body: e.target.value }))}
              required
            />
          </div>
        </DialogContent>
        <DialogFooter>
          <Button type="button" variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button type="submit" disabled={createTemplate.isPending}>
            {createTemplate.isPending ? 'Enregistrement…' : 'Créer le modèle'}
          </Button>
        </DialogFooter>
      </form>
    </Dialog>
  );
}

// ─── Create Automation Dialog ─────────────────────────────────────────────────

function CreateAutomationDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const createAutomation = useCreateAutomation();
  const [form, setForm] = useState({
    name: '',
    trigger_type: 'new_member',
    delay_days: '0',
    message_template: '',
    channel: 'email',
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    createAutomation.mutate(
      {
        ...form,
        delay_days: parseInt(form.delay_days, 10),
      },
      {
        onSuccess: () => {
          toast({ type: 'success', title: 'Automatisation créée', description: 'L\'automatisation est maintenant active.' });
          setForm({ name: '', trigger_type: 'new_member', delay_days: '0', message_template: '', channel: 'email' });
          onClose();
        },
        onError: () => {
          toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer l\'automatisation.' });
        },
      },
    );
  }

  return (
    <Dialog open={open} onClose={onClose} className="max-w-2xl">
      <DialogClose onClose={onClose} />
      <DialogHeader>
        <DialogTitle>Nouvelle automatisation</DialogTitle>
        <DialogDescription>Configurer un envoi automatique déclenché par un événement.</DialogDescription>
      </DialogHeader>
      <form onSubmit={handleSubmit}>
        <DialogContent className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-white/70">Nom de l&apos;automatisation *</label>
            <Input
              placeholder="Ex: Courriel de bienvenue nouveau membre"
              value={form.name}
              onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-white/70">Déclencheur</label>
              <Select
                value={form.trigger_type}
                onChange={(e) => setForm((p) => ({ ...p, trigger_type: e.target.value }))}
              >
                <option value="new_member">Nouveau membre</option>
                <option value="birthday">Anniversaire</option>
                <option value="event_registration">Inscription événement</option>
                <option value="donation">Don reçu</option>
                <option value="absence">Absence prolongée</option>
                <option value="manual">Manuel</option>
              </Select>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-white/70">Canal</label>
              <Select
                value={form.channel}
                onChange={(e) => setForm((p) => ({ ...p, channel: e.target.value }))}
              >
                <option value="email">Courriel</option>
                <option value="sms">SMS</option>
                <option value="push">Notification push</option>
              </Select>
            </div>
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-white/70">Délai après déclenchement (jours)</label>
            <Input
              type="number"
              min="0"
              max="365"
              placeholder="0"
              value={form.delay_days}
              onChange={(e) => setForm((p) => ({ ...p, delay_days: e.target.value }))}
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-white/70">Message *</label>
            <Textarea
              placeholder="Message à envoyer automatiquement..."
              className="min-h-[120px]"
              value={form.message_template}
              onChange={(e) => setForm((p) => ({ ...p, message_template: e.target.value }))}
              required
            />
          </div>
        </DialogContent>
        <DialogFooter>
          <Button type="button" variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button type="submit" disabled={createAutomation.isPending}>
            <Zap className="h-4 w-4 mr-2" />
            {createAutomation.isPending ? 'Création…' : 'Créer l\'automatisation'}
          </Button>
        </DialogFooter>
      </form>
    </Dialog>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function CommunicationPage() {
  const { toast } = useToast();

  // Search states
  const [newsletterSearch, setNewsletterSearch] = useState('');
  const [messageSearch, setMessageSearch] = useState('');
  const [smsSearch, setSmsSearch] = useState('');
  const [templateSearch, setTemplateSearch] = useState('');
  const [automationSearch, setAutomationSearch] = useState('');
  const [groupChatSearch, setGroupChatSearch] = useState('');
  const [abTestSearch, setAbTestSearch] = useState('');

  // Dialog states
  const [showCreateNewsletter, setShowCreateNewsletter] = useState(false);
  const [showComposeMessage, setShowComposeMessage] = useState(false);
  const [showComposeSms, setShowComposeSms] = useState(false);
  const [showCreateTemplate, setShowCreateTemplate] = useState(false);
  const [showCreateAutomation, setShowCreateAutomation] = useState(false);

  // Infinite scroll data fetching
  const newslettersQuery = useInfiniteNewsletters(newsletterSearch);
  const notifsQuery = useInfiniteNotifications();
  const { data: unreadData } = useUnreadCount();
  const messagesQuery = useInfiniteDirectMessages(messageSearch);
  const smsQuery = useInfiniteSmsMessages(smsSearch);
  const templatesQuery = useInfiniteEmailTemplates(templateSearch);
  const automationsQuery = useInfiniteAutomations(automationSearch);
  const groupChatsQuery = useInfiniteGroupChats(groupChatSearch);
  const abTestsQuery = useInfiniteABTests(abTestSearch);

  // Mutations
  const sendNewsletter = useSendNewsletter();
  const markRead = useMarkNotificationRead();
  const pickWinner = usePickABTestWinner();

  // Flatten data
  const newsletters = (newslettersQuery.data?.pages.flatMap((p) => p.results) ?? []) as Newsletter[];
  const notifications = (notifsQuery.data?.pages.flatMap((p) => p.results) ?? []) as Notification[];
  const messages = (messagesQuery.data?.pages.flatMap((p) => p.results) ?? []) as DirectMessage[];
  const smsMessages = (smsQuery.data?.pages.flatMap((p) => p.results) ?? []) as SmsMessage[];
  const templates = (templatesQuery.data?.pages.flatMap((p) => p.results) ?? []) as EmailTemplate[];
  const automations = (automationsQuery.data?.pages.flatMap((p) => p.results) ?? []) as Automation[];
  const groupChats = (groupChatsQuery.data?.pages.flatMap((p) => p.results) ?? []) as Record<string, unknown>[];
  const abTests = (abTestsQuery.data?.pages.flatMap((p) => p.results) ?? []) as Record<string, unknown>[];

  // Computed stats
  const sentNewsletters = newsletters.filter((n) => n.status === 'sent').length;
  const unreadCount = unreadData?.count ?? 0;
  const activeAutomations = automations.filter((a) => a.status === 'active').length;

  // ── Newsletter columns ──
  const newsletterColumns: Column<Newsletter>[] = [
    {
      key: 'subject',
      header: 'Sujet',
      render: (item) => (
        <div>
          <p className="font-medium text-white/90">{item.subject}</p>
          <p className="text-xs text-white/40">{formatDate(item.created_at)}</p>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Statut',
      render: (item) => (
        <Badge variant={newsletterStatusVariant[item.status] ?? 'secondary'}>
          {newsletterStatusLabels[item.status] ?? item.status}
        </Badge>
      ),
    },
    {
      key: 'recipients_count',
      header: 'Destinataires',
      render: (item) => (
        <div className="flex items-center gap-1.5 text-white/70">
          <Users className="h-3.5 w-3.5 text-white/30" />
          {item.recipients_count ?? 0}
        </div>
      ),
    },
    {
      key: 'opened_count',
      header: 'Ouvertures',
      render: (item) => (
        <div className="flex items-center gap-1.5 text-white/70">
          <Eye className="h-3.5 w-3.5 text-white/30" />
          {item.opened_count ?? 0}
        </div>
      ),
    },
    {
      key: 'sent_at',
      header: 'Envoyée le',
      render: (item) => item.sent_at ? formatDate(item.sent_at) : '—',
    },
    {
      key: 'actions',
      header: '',
      render: (item) =>
        item.status === 'draft' ? (
          <Button
            size="sm"
            variant="outline"
            onClick={(e) => {
              e.stopPropagation();
              sendNewsletter.mutate(item.id, {
                onSuccess: () =>
                  toast({ type: 'success', title: 'Infolettre envoyée', description: `"${item.subject}" a été envoyée.` }),
                onError: () =>
                  toast({ type: 'error', title: 'Erreur', description: 'Impossible d\'envoyer l\'infolettre.' }),
              });
            }}
          >
            <Send className="h-3.5 w-3.5 mr-1.5" />
            Envoyer
          </Button>
        ) : null,
    },
  ];

  // ── SMS columns ──
  const smsColumns: Column<SmsMessage>[] = [
    {
      key: 'phone_number',
      header: 'Téléphone',
      render: (item) => (
        <div className="flex items-center gap-2">
          <Phone className="h-3.5 w-3.5 text-white/30" />
          <span className="font-mono text-sm">{item.phone_number}</span>
        </div>
      ),
    },
    {
      key: 'message',
      header: 'Message',
      render: (item) => (
        <p className="text-white/70 truncate max-w-xs">{item.message}</p>
      ),
    },
    {
      key: 'status',
      header: 'Statut',
      render: (item) => (
        <Badge variant={smsStatusVariant[item.status] ?? 'secondary'}>
          {smsStatusLabels[item.status] ?? item.status}
        </Badge>
      ),
    },
    {
      key: 'created_at',
      header: 'Date',
      render: (item) => formatDate(item.created_at),
    },
  ];

  // ── Template columns ──
  const templateColumns: Column<EmailTemplate>[] = [
    {
      key: 'name',
      header: 'Nom',
      render: (item) => (
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-purple-400" />
          <span className="font-medium text-white/90">{item.name as string}</span>
        </div>
      ),
    },
    {
      key: 'subject',
      header: 'Sujet',
      render: (item) => <span className="text-white/60">{item.subject as string}</span>,
    },
    {
      key: 'template_type',
      header: 'Type',
      render: (item) => (
        <Badge variant="outline">
          {templateTypeLabels[item.template_type] ?? (item.template_type as string)}
        </Badge>
      ),
    },
    {
      key: 'created_at',
      header: 'Créé le',
      render: (item) => formatDate(item.created_at),
    },
  ];

  // ── Automation columns ──
  const automationColumns: Column<Automation>[] = [
    {
      key: 'name',
      header: 'Automatisation',
      render: (item) => (
        <div className="flex items-center gap-2">
          <Zap className="h-4 w-4 text-amber-400" />
          <span className="font-medium text-white/90">{item.name as string}</span>
        </div>
      ),
    },
    {
      key: 'trigger_type',
      header: 'Déclencheur',
      render: (item) => (
        <Badge variant="outline">
          {triggerTypeLabels[item.trigger_type] ?? (item.trigger_type as string)}
        </Badge>
      ),
    },
    {
      key: 'status',
      header: 'Statut',
      render: (item) => (
        <Badge variant={automationStatusVariant[item.status] ?? 'secondary'}>
          {automationStatusLabels[item.status] ?? (item.status as string)}
        </Badge>
      ),
    },
    {
      key: 'enrollment_count',
      header: 'Inscrits',
      render: (item) => (
        <div className="flex items-center gap-1.5 text-white/70">
          <TrendingUp className="h-3.5 w-3.5 text-white/30" />
          {item.enrollment_count ?? 0}
        </div>
      ),
    },
    {
      key: 'created_at',
      header: 'Créée le',
      render: (item) => formatDate(item.created_at),
    },
  ];

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Communication</h1>
          <p className="text-white/50">Infolettres, notifications, messages et automatisations</p>
        </div>
      </div>

      {/* ── Stat Cards ── */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Infolettres envoyées"
          value={newslettersQuery.data?.pages[0]?.count ?? '—'}
          subtitle={`${sentNewsletters} envoyées chargées`}
          icon={Mail}
          gradient="bg-purple-600/70"
        />
        <StatCard
          title="Notifications non lues"
          value={unreadCount}
          subtitle="Mis à jour toutes les 30 s"
          icon={Bell}
          gradient="bg-amber-600/70"
        />
        <StatCard
          title="SMS envoyés"
          value={smsQuery.data?.pages[0]?.count ?? '—'}
          subtitle="Total dans le système"
          icon={Phone}
          gradient="bg-blue-600/70"
        />
        <StatCard
          title="Automatisations actives"
          value={activeAutomations}
          subtitle={`sur ${automationsQuery.data?.pages[0]?.count ?? 0} au total`}
          icon={Zap}
          gradient="bg-emerald-600/70"
        />
      </div>

      {/* ── Tabs ── */}
      <Tabs defaultValue="newsletters">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <TabsList>
            <TabsTrigger value="newsletters">
              <Mail className="h-4 w-4 mr-2 inline-block" />
              Infolettres
            </TabsTrigger>
            <TabsTrigger value="notifications">
              <Bell className="h-4 w-4 mr-2 inline-block" />
              Notifications
              {unreadCount > 0 && (
                <span className="ml-1.5 inline-flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-purple-500/70 px-1 text-[10px] font-bold text-white">
                  {unreadCount > 99 ? '99+' : unreadCount}
                </span>
              )}
            </TabsTrigger>
            <TabsTrigger value="messages">
              <MessageSquare className="h-4 w-4 mr-2 inline-block" />
              Messages
            </TabsTrigger>
            <TabsTrigger value="sms">
              <Phone className="h-4 w-4 mr-2 inline-block" />
              SMS
            </TabsTrigger>
            <TabsTrigger value="templates">
              <FileText className="h-4 w-4 mr-2 inline-block" />
              Modèles
            </TabsTrigger>
            <TabsTrigger value="automations">
              <Zap className="h-4 w-4 mr-2 inline-block" />
              Automatisations
            </TabsTrigger>
            <TabsTrigger value="group-chats">
              <MessagesSquare className="h-4 w-4 mr-2 inline-block" />
              Groupes
            </TabsTrigger>
            <TabsTrigger value="ab-tests">
              <FlaskConical className="h-4 w-4 mr-2 inline-block" />
              Tests A/B
            </TabsTrigger>
          </TabsList>
        </div>

        {/* ────────────── Newsletters Tab ────────────── */}
        <TabsContent value="newsletters">
          <div className="space-y-4">
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
                <Input
                  placeholder="Rechercher une infolettre..."
                  className="pl-9"
                  value={newsletterSearch}
                  onChange={(e) => setNewsletterSearch(e.target.value)}
                />
              </div>
              <Button onClick={() => setShowCreateNewsletter(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Nouvelle infolettre
              </Button>
            </div>
            <InfiniteScrollTable
              columns={newsletterColumns}
              data={newsletters}
              totalCount={newslettersQuery.data?.pages[0]?.count}
              isLoading={newslettersQuery.isLoading}
              fetchNextPage={newslettersQuery.fetchNextPage}
              hasNextPage={newslettersQuery.hasNextPage}
              isFetchingNextPage={newslettersQuery.isFetchingNextPage}
              error={newslettersQuery.error}
              emptyMessage="Aucune infolettre trouvée"
            />
          </div>
        </TabsContent>

        {/* ────────────── Notifications Tab ────────────── */}
        <TabsContent value="notifications">
          <InfiniteScrollList
            items={notifications}
            totalCount={notifsQuery.data?.pages[0]?.count}
            isLoading={notifsQuery.isLoading}
            fetchNextPage={notifsQuery.fetchNextPage}
            hasNextPage={notifsQuery.hasNextPage}
            isFetchingNextPage={notifsQuery.isFetchingNextPage}
            error={notifsQuery.error}
            emptyMessage="Aucune notification"
            renderItem={(notif) => (
              <div
                key={notif.id}
                className={`rounded-2xl border px-5 py-4 flex items-start justify-between gap-4 transition-all ${
                  notif.is_read
                    ? 'bg-white/[0.03] border-white/[0.06]'
                    : 'bg-white/[0.06] border-purple-500/20 shadow-[0_0_20px_rgba(124,58,237,0.06)]'
                }`}
              >
                <div className="flex items-start gap-3 min-w-0">
                  <div
                    className={`mt-0.5 h-2 w-2 rounded-full shrink-0 ${
                      notif.is_read ? 'bg-white/20' : 'bg-purple-400'
                    }`}
                  />
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-sm text-white/90">{notif.title}</span>
                      <Badge variant={notifTypeVariant[notif.notification_type] ?? 'outline'}>
                        {notifTypeLabels[notif.notification_type] ?? notif.notification_type}
                      </Badge>
                    </div>
                    <p className="text-sm text-white/50 mt-0.5 truncate">{notif.message}</p>
                    <p className="text-xs text-white/30 mt-1 flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatDate(notif.created_at)}
                    </p>
                  </div>
                </div>
                {!notif.is_read && (
                  <Button
                    size="sm"
                    variant="ghost"
                    className="shrink-0"
                    onClick={() =>
                      markRead.mutate(notif.id, {
                        onSuccess: () =>
                          toast({ type: 'success', title: 'Marqué comme lu' }),
                        onError: () =>
                          toast({ type: 'error', title: 'Erreur', description: 'Impossible de marquer comme lu.' }),
                      })
                    }
                  >
                    <CheckCheck className="h-4 w-4 mr-1.5" />
                    Marquer lu
                  </Button>
                )}
              </div>
            )}
          />
        </TabsContent>

        {/* ────────────── Messages Tab ────────────── */}
        <TabsContent value="messages">
          <div className="space-y-4">
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
                <Input
                  placeholder="Rechercher un message..."
                  className="pl-9"
                  value={messageSearch}
                  onChange={(e) => setMessageSearch(e.target.value)}
                />
              </div>
              <Button onClick={() => setShowComposeMessage(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Nouveau message
              </Button>
            </div>
            <InfiniteScrollList
              items={messages}
              totalCount={messagesQuery.data?.pages[0]?.count}
              isLoading={messagesQuery.isLoading}
              fetchNextPage={messagesQuery.fetchNextPage}
              hasNextPage={messagesQuery.hasNextPage}
              isFetchingNextPage={messagesQuery.isFetchingNextPage}
              error={messagesQuery.error}
              emptyMessage="Aucun message trouvé"
              renderItem={(msg) => (
                <div
                  key={msg.id}
                  className={`rounded-2xl border px-5 py-4 transition-all cursor-pointer hover:bg-white/[0.07] ${
                    msg.is_read
                      ? 'bg-white/[0.03] border-white/[0.06]'
                      : 'bg-white/[0.06] border-purple-500/20'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        {!msg.is_read && (
                          <span className="h-2 w-2 rounded-full bg-purple-400 shrink-0" />
                        )}
                        <span className="font-medium text-sm text-white/90 truncate">{msg.subject}</span>
                      </div>
                      <div className="flex items-center gap-2 mt-1 text-xs text-white/40">
                        <span>De: {msg.sender_name}</span>
                        <span>·</span>
                        <span>À: {msg.recipient_name}</span>
                      </div>
                      <p className="text-sm text-white/50 mt-1 truncate">{msg.body}</p>
                    </div>
                    <p className="text-xs text-white/30 shrink-0">{formatDate(msg.created_at)}</p>
                  </div>
                </div>
              )}
            />
          </div>
        </TabsContent>

        {/* ────────────── SMS Tab ────────────── */}
        <TabsContent value="sms">
          <div className="space-y-4">
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
                <Input
                  placeholder="Rechercher un SMS..."
                  className="pl-9"
                  value={smsSearch}
                  onChange={(e) => setSmsSearch(e.target.value)}
                />
              </div>
              <Button onClick={() => setShowComposeSms(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Nouveau SMS
              </Button>
            </div>
            <InfiniteScrollTable
              columns={smsColumns}
              data={smsMessages}
              totalCount={smsQuery.data?.pages[0]?.count}
              isLoading={smsQuery.isLoading}
              fetchNextPage={smsQuery.fetchNextPage}
              hasNextPage={smsQuery.hasNextPage}
              isFetchingNextPage={smsQuery.isFetchingNextPage}
              error={smsQuery.error}
              emptyMessage="Aucun SMS trouvé"
            />
          </div>
        </TabsContent>

        {/* ────────────── Templates Tab ────────────── */}
        <TabsContent value="templates">
          <div className="space-y-4">
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
                <Input
                  placeholder="Rechercher un modèle..."
                  className="pl-9"
                  value={templateSearch}
                  onChange={(e) => setTemplateSearch(e.target.value)}
                />
              </div>
              <Button onClick={() => setShowCreateTemplate(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Nouveau modèle
              </Button>
            </div>
            <InfiniteScrollTable
              columns={templateColumns}
              data={templates}
              totalCount={templatesQuery.data?.pages[0]?.count}
              isLoading={templatesQuery.isLoading}
              fetchNextPage={templatesQuery.fetchNextPage}
              hasNextPage={templatesQuery.hasNextPage}
              isFetchingNextPage={templatesQuery.isFetchingNextPage}
              error={templatesQuery.error}
              emptyMessage="Aucun modèle trouvé"
            />
          </div>
        </TabsContent>

        {/* ────────────── Automations Tab ────────────── */}
        <TabsContent value="automations">
          <div className="space-y-4">
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
                <Input
                  placeholder="Rechercher une automatisation..."
                  className="pl-9"
                  value={automationSearch}
                  onChange={(e) => setAutomationSearch(e.target.value)}
                />
              </div>
              <Button onClick={() => setShowCreateAutomation(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Nouvelle automatisation
              </Button>
            </div>
            <InfiniteScrollTable
              columns={automationColumns}
              data={automations}
              totalCount={automationsQuery.data?.pages[0]?.count}
              isLoading={automationsQuery.isLoading}
              fetchNextPage={automationsQuery.fetchNextPage}
              hasNextPage={automationsQuery.hasNextPage}
              isFetchingNextPage={automationsQuery.isFetchingNextPage}
              error={automationsQuery.error}
              emptyMessage="Aucune automatisation trouvée"
            />
          </div>
        </TabsContent>

        {/* ────────────── Group Chats Tab ────────────── */}
        <TabsContent value="group-chats">
          <div className="space-y-4">
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
                <Input placeholder="Rechercher un groupe..." className="pl-9" value={groupChatSearch} onChange={(e) => setGroupChatSearch(e.target.value)} />
              </div>
            </div>
            <InfiniteScrollTable
              columns={[
                { key: 'name', header: 'Nom du groupe', render: (item: Record<string, unknown>) => (
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-purple-500/10"><MessagesSquare className="h-4 w-4 text-purple-400" /></div>
                    <span className="font-medium text-white/90">{String(item.name ?? '—')}</span>
                  </div>
                )},
                { key: 'members_count', header: 'Membres', render: (item: Record<string, unknown>) => (
                  <span className="text-white/70">{String(item.members_count ?? 0)}</span>
                )},
                { key: 'last_message_at', header: 'Dernier message', render: (item: Record<string, unknown>) =>
                  item.last_message_at ? new Date(item.last_message_at as string).toLocaleDateString('fr-CA', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'
                },
                { key: 'is_active', header: 'Statut', render: (item: Record<string, unknown>) => (
                  <Badge variant={item.is_active !== false ? 'success' : 'secondary'}>{item.is_active !== false ? 'Actif' : 'Inactif'}</Badge>
                )},
              ]}
              data={groupChats}
              totalCount={groupChatsQuery.data?.pages[0]?.count}
              isLoading={groupChatsQuery.isLoading}
              fetchNextPage={groupChatsQuery.fetchNextPage}
              hasNextPage={groupChatsQuery.hasNextPage}
              isFetchingNextPage={groupChatsQuery.isFetchingNextPage}
              error={groupChatsQuery.error}
              emptyMessage="Aucun groupe de discussion trouvé"
            />
          </div>
        </TabsContent>

        {/* ────────────── A/B Tests Tab ────────────── */}
        <TabsContent value="ab-tests">
          <div className="space-y-4">
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
                <Input placeholder="Rechercher un test..." className="pl-9" value={abTestSearch} onChange={(e) => setAbTestSearch(e.target.value)} />
              </div>
            </div>
            <InfiniteScrollTable
              columns={[
                { key: 'name', header: 'Nom du test', render: (item: Record<string, unknown>) => (
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-amber-500/10"><FlaskConical className="h-4 w-4 text-amber-400" /></div>
                    <span className="font-medium text-white/90">{String(item.name ?? '—')}</span>
                  </div>
                )},
                { key: 'variant_a_opens', header: 'Variante A', render: (item: Record<string, unknown>) => (
                  <span className="text-white/70">{String(item.variant_a_open_rate ?? item.variant_a_opens ?? '—')}%</span>
                )},
                { key: 'variant_b_opens', header: 'Variante B', render: (item: Record<string, unknown>) => (
                  <span className="text-white/70">{String(item.variant_b_open_rate ?? item.variant_b_opens ?? '—')}%</span>
                )},
                { key: 'winner', header: 'Gagnant', render: (item: Record<string, unknown>) =>
                  item.winner
                    ? <Badge variant="success">{String(item.winner)}</Badge>
                    : <span className="text-white/30">En cours</span>
                },
                { key: 'actions', header: '', render: (item: Record<string, unknown>) =>
                  !item.winner ? (
                    <Button size="sm" variant="outline" onClick={(e) => {
                      e.stopPropagation();
                      pickWinner.mutate(item.id as string, {
                        onSuccess: () => toast({ type: 'success', title: 'Gagnant déterminé' }),
                        onError: () => toast({ type: 'error', title: 'Erreur' }),
                      });
                    }} disabled={pickWinner.isPending}>
                      <Trophy className="h-3.5 w-3.5 mr-1" />
                      Choisir gagnant
                    </Button>
                  ) : null
                },
              ]}
              data={abTests}
              totalCount={abTestsQuery.data?.pages[0]?.count}
              isLoading={abTestsQuery.isLoading}
              fetchNextPage={abTestsQuery.fetchNextPage}
              hasNextPage={abTestsQuery.hasNextPage}
              isFetchingNextPage={abTestsQuery.isFetchingNextPage}
              error={abTestsQuery.error}
              emptyMessage="Aucun test A/B trouvé"
            />
          </div>
        </TabsContent>
      </Tabs>

      {/* ── Dialogs ── */}
      <CreateNewsletterDialog
        open={showCreateNewsletter}
        onClose={() => setShowCreateNewsletter(false)}
      />
      <ComposeMessageDialog
        open={showComposeMessage}
        onClose={() => setShowComposeMessage(false)}
      />
      <ComposeSmsDialog
        open={showComposeSms}
        onClose={() => setShowComposeSms(false)}
        templates={templates}
      />
      <CreateTemplateDialog
        open={showCreateTemplate}
        onClose={() => setShowCreateTemplate(false)}
      />
      <CreateAutomationDialog
        open={showCreateAutomation}
        onClose={() => setShowCreateAutomation(false)}
      />
    </div>
  );
}
