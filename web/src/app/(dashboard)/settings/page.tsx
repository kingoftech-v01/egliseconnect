'use client';

import { useState, useEffect, type ReactNode } from 'react';
import {
  Church,
  User,
  Shield,
  Bell,
  Key,
  Globe,
  Lock,
  Smartphone,
  Mail,
  Plus,
  Trash2,
  Eye,
  EyeOff,
  Copy,
  Upload,
  Monitor,
  RefreshCw,
  CheckCircle,
  XCircle,
  Loader2,
  Building,
  ScrollText,
  LogIn,
  MapPin,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Avatar } from '@/components/ui/avatar';
import { Skeleton } from '@/components/ui/skeleton';
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
import { useAuthStore } from '@/stores/auth';
import {
  useChurchBranding,
  useUpdateChurchBranding,
  useCreateChurchBranding,
  useUpdateProfile,
  useChangePassword,
  useNotificationPreferences,
  useUpdateNotificationPreferences,
  useWebhooks,
  useCreateWebhook,
  useDeleteWebhook,
  useCampuses,
  useCreateCampus,
  useDeleteCampus,
  useAuditLogs,
  useLoginAudits,
} from '@/hooks/use-settings';
import type { Campus, AuditLog, LoginAudit } from '@/hooks/use-settings';

// ---------------------------------------------------------------------------
// Toggle Switch component
// ---------------------------------------------------------------------------

function Toggle({
  enabled,
  onChange,
}: {
  enabled: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onChange(!enabled)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary/50 ${
        enabled ? 'bg-primary' : 'bg-white/[0.12]'
      }`}
    >
      <span
        className={`inline-block h-4 w-4 rounded-full bg-white shadow-md transform transition-transform duration-200 ${
          enabled ? 'translate-x-6' : 'translate-x-1'
        }`}
      />
    </button>
  );
}

// ---------------------------------------------------------------------------
// Section label helper
// ---------------------------------------------------------------------------

function FieldLabel({ children }: { children: ReactNode }) {
  return (
    <label className="block text-xs font-medium text-white/50 uppercase tracking-wide mb-1.5">
      {children}
    </label>
  );
}

// ---------------------------------------------------------------------------
// Glass card wrapper
// ---------------------------------------------------------------------------

function GlassCard({
  children,
  className = '',
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`bg-white/[0.05] backdrop-blur-xl border border-white/[0.08] rounded-2xl shadow-[0_8px_32px_rgba(0,0,0,0.2)] ${className}`}
    >
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Église Tab
// ---------------------------------------------------------------------------

function EgliseTab() {
  const { toast } = useToast();
  const { data: brandingData, isLoading } = useChurchBranding();
  const updateBranding = useUpdateChurchBranding();
  const createBranding = useCreateChurchBranding();

  const branding = brandingData?.results?.[0];

  const [form, setForm] = useState({
    church_name: '',
    address: '',
    phone: '',
    email: '',
    website: '',
    primary_color: '#7c3aed',
  });

  useEffect(() => {
    if (branding) {
      setForm({
        church_name: branding.church_name || '',
        address: branding.address || '',
        phone: branding.phone || '',
        email: branding.email || '',
        website: branding.website || '',
        primary_color: branding.primary_color || '#7c3aed',
      });
    }
  }, [branding]);

  const set = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [key]: e.target.value }));

  const handleSave = () => {
    if (branding) {
      updateBranding.mutate(
        { id: branding.id, data: form },
        {
          onSuccess: () => toast({ type: 'success', title: 'Paramètres sauvegardés', description: "Les informations de l'église ont été mises à jour." }),
          onError: () => toast({ type: 'error', title: 'Erreur', description: 'Impossible de sauvegarder les modifications.' }),
        },
      );
    } else {
      createBranding.mutate(form, {
        onSuccess: () => toast({ type: 'success', title: 'Paramètres créés', description: "Les informations de l'église ont été enregistrées." }),
        onError: () => toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer les paramètres.' }),
      });
    }
  };

  const saving = updateBranding.isPending || createBranding.isPending;

  return (
    <div className="space-y-6">
      {/* Informations générales */}
      <GlassCard className="p-6">
        <h3 className="text-base font-semibold text-white/90 mb-5 flex items-center gap-2">
          <Church className="h-4 w-4 text-purple-400" />
          Informations générales
        </h3>
        {isLoading ? (
          <div className="grid gap-5 md:grid-cols-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i}><Skeleton className="h-4 w-20 mb-2" /><Skeleton className="h-10 w-full" /></div>
            ))}
          </div>
        ) : (
          <div className="grid gap-5 md:grid-cols-2">
            <div>
              <FieldLabel>Nom de l'église</FieldLabel>
              <Input value={form.church_name} onChange={set('church_name')} placeholder="Nom de l'église" />
            </div>
            <div>
              <FieldLabel>Site web</FieldLabel>
              <Input value={form.website} onChange={set('website')} placeholder="https://..." />
            </div>
            <div className="md:col-span-2">
              <FieldLabel>Adresse</FieldLabel>
              <Input value={form.address} onChange={set('address')} placeholder="Adresse complète" />
            </div>
            <div>
              <FieldLabel>Téléphone</FieldLabel>
              <Input value={form.phone} onChange={set('phone')} placeholder="+1 (514) 555-0000" />
            </div>
            <div>
              <FieldLabel>Courriel</FieldLabel>
              <Input value={form.email} onChange={set('email')} type="email" placeholder="contact@eglise.ca" />
            </div>
          </div>
        )}
      </GlassCard>

      {/* Logo & Apparence */}
      <GlassCard className="p-6">
        <h3 className="text-base font-semibold text-white/90 mb-5 flex items-center gap-2">
          <Globe className="h-4 w-4 text-purple-400" />
          Logo & Apparence
        </h3>
        <div className="grid gap-6 md:grid-cols-2">
          {/* Logo upload */}
          <div>
            <FieldLabel>Logo de l'église</FieldLabel>
            <div className="mt-1 flex flex-col items-center justify-center border-2 border-dashed border-white/[0.12] rounded-xl p-8 bg-white/[0.03] hover:bg-white/[0.05] transition-colors cursor-pointer group">
              <Upload className="h-8 w-8 text-white/30 group-hover:text-purple-400 transition-colors mb-2" />
              <p className="text-sm text-white/50 group-hover:text-white/70 transition-colors text-center">
                Glissez votre logo ici ou{' '}
                <span className="text-purple-400 underline">parcourir</span>
              </p>
              <p className="text-xs text-white/30 mt-1">PNG, JPG jusqu'à 2 Mo</p>
            </div>
          </div>

          {/* Color */}
          <div className="space-y-5">
            <div>
              <FieldLabel>Couleur principale</FieldLabel>
              <div className="flex items-center gap-3 mt-1">
                <div
                  className="h-10 w-10 rounded-xl border border-white/[0.1] shrink-0 cursor-pointer"
                  style={{ backgroundColor: form.primary_color }}
                  title="Cliquez pour choisir"
                />
                <Input
                  value={form.primary_color}
                  onChange={set('primary_color')}
                  placeholder="#7c3aed"
                  className="font-mono"
                  maxLength={7}
                />
              </div>
            </div>
          </div>
        </div>
      </GlassCard>

      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={saving}>
          {saving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
          Sauvegarder les modifications
        </Button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Profil Tab
// ---------------------------------------------------------------------------

function ProfilTab() {
  const { toast } = useToast();
  const member = useAuthStore((s) => s.member);
  const updateProfile = useUpdateProfile();

  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    phone: '',
  });

  useEffect(() => {
    if (member) {
      setForm({
        first_name: member.first_name || '',
        last_name: member.last_name || '',
        phone: member.phone || '',
      });
    }
  }, [member]);

  const set = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [key]: e.target.value }));

  const handleSave = () => {
    updateProfile.mutate(form, {
      onSuccess: () => toast({ type: 'success', title: 'Profil mis à jour', description: 'Vos informations personnelles ont été sauvegardées.' }),
      onError: () => toast({ type: 'error', title: 'Erreur', description: 'Impossible de mettre à jour le profil.' }),
    });
  };

  return (
    <div className="space-y-6">
      <GlassCard className="p-6">
        <h3 className="text-base font-semibold text-white/90 mb-5 flex items-center gap-2">
          <User className="h-4 w-4 text-purple-400" />
          Photo de profil
        </h3>
        <div className="flex items-center gap-6">
          <Avatar fallback={member?.full_name ?? ''} src={member?.photo} size="lg" className="h-20 w-20 text-xl" />
          <div className="space-y-2">
            <p className="text-sm text-white/60">
              Formats acceptés : JPG, PNG. Taille maximale : 1 Mo.
            </p>
            <div className="flex gap-2">
              <Button variant="outline" size="sm">
                <Upload className="h-3.5 w-3.5 mr-1.5" />
                Changer la photo
              </Button>
              <Button variant="ghost" size="sm" className="text-rose-400 hover:text-rose-300">
                <Trash2 className="h-3.5 w-3.5 mr-1.5" />
                Supprimer
              </Button>
            </div>
          </div>
        </div>
      </GlassCard>

      <GlassCard className="p-6">
        <h3 className="text-base font-semibold text-white/90 mb-5">Informations personnelles</h3>
        <div className="grid gap-5 md:grid-cols-2">
          <div>
            <FieldLabel>Prénom</FieldLabel>
            <Input value={form.first_name} onChange={set('first_name')} placeholder="Prénom" />
          </div>
          <div>
            <FieldLabel>Nom de famille</FieldLabel>
            <Input value={form.last_name} onChange={set('last_name')} placeholder="Nom de famille" />
          </div>
          <div>
            <FieldLabel>Adresse courriel</FieldLabel>
            <Input value={member?.email ?? ''} disabled type="email" placeholder="courriel@exemple.ca" />
          </div>
          <div>
            <FieldLabel>Téléphone</FieldLabel>
            <Input value={form.phone} onChange={set('phone')} placeholder="+1 (514) 555-0000" />
          </div>
        </div>
      </GlassCard>

      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={updateProfile.isPending}>
          {updateProfile.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
          Sauvegarder le profil
        </Button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sécurité Tab
// ---------------------------------------------------------------------------

function SecuriteTab() {
  const { toast } = useToast();
  const changePassword = useChangePassword();
  const [passwords, setPasswords] = useState({ current: '', newPwd: '', confirm: '' });
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [twoFAEnabled, setTwoFAEnabled] = useState(false);

  const handleChangePassword = () => {
    if (!passwords.current || !passwords.newPwd || !passwords.confirm) {
      toast({ type: 'error', title: 'Champs requis', description: 'Veuillez remplir tous les champs.' });
      return;
    }
    if (passwords.newPwd !== passwords.confirm) {
      toast({ type: 'error', title: 'Mots de passe différents', description: 'Le nouveau mot de passe et la confirmation ne correspondent pas.' });
      return;
    }
    changePassword.mutate(
      {
        current_password: passwords.current,
        new_password: passwords.newPwd,
        new_password_confirm: passwords.confirm,
      },
      {
        onSuccess: () => {
          setPasswords({ current: '', newPwd: '', confirm: '' });
          toast({ type: 'success', title: 'Mot de passe modifié', description: 'Votre mot de passe a été mis à jour avec succès.' });
        },
        onError: (err) => {
          const message = (err as { message?: string })?.message || 'Impossible de modifier le mot de passe.';
          toast({ type: 'error', title: 'Erreur', description: message });
        },
      },
    );
  };

  return (
    <div className="space-y-6">
      {/* Change password */}
      <GlassCard className="p-6">
        <h3 className="text-base font-semibold text-white/90 mb-5 flex items-center gap-2">
          <Lock className="h-4 w-4 text-purple-400" />
          Changer le mot de passe
        </h3>
        <div className="space-y-4 max-w-md">
          <div>
            <FieldLabel>Mot de passe actuel</FieldLabel>
            <div className="relative">
              <Input
                type={showCurrent ? 'text' : 'password'}
                value={passwords.current}
                onChange={(e) => setPasswords((p) => ({ ...p, current: e.target.value }))}
                placeholder="••••••••"
                className="pr-10"
              />
              <button
                type="button"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 transition-colors"
                onClick={() => setShowCurrent((v) => !v)}
              >
                {showCurrent ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>
          <div>
            <FieldLabel>Nouveau mot de passe</FieldLabel>
            <div className="relative">
              <Input
                type={showNew ? 'text' : 'password'}
                value={passwords.newPwd}
                onChange={(e) => setPasswords((p) => ({ ...p, newPwd: e.target.value }))}
                placeholder="••••••••"
                className="pr-10"
              />
              <button
                type="button"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 transition-colors"
                onClick={() => setShowNew((v) => !v)}
              >
                {showNew ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>
          <div>
            <FieldLabel>Confirmer le nouveau mot de passe</FieldLabel>
            <div className="relative">
              <Input
                type={showConfirm ? 'text' : 'password'}
                value={passwords.confirm}
                onChange={(e) => setPasswords((p) => ({ ...p, confirm: e.target.value }))}
                placeholder="••••••••"
                className="pr-10"
              />
              <button
                type="button"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 transition-colors"
                onClick={() => setShowConfirm((v) => !v)}
              >
                {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>
          <Button onClick={handleChangePassword} disabled={changePassword.isPending} className="mt-1">
            {changePassword.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            Modifier le mot de passe
          </Button>
        </div>
      </GlassCard>

      {/* 2FA */}
      <GlassCard className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-purple-500/10 flex items-center justify-center">
              <Smartphone className="h-5 w-5 text-purple-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-white/90">Authentification à deux facteurs (2FA)</p>
              <p className="text-xs text-white/50 mt-0.5">
                Sécurisez votre compte avec une application d'authentification.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant={twoFAEnabled ? 'success' : 'secondary'}>
              {twoFAEnabled ? 'Activé' : 'Désactivé'}
            </Badge>
            <Toggle enabled={twoFAEnabled} onChange={setTwoFAEnabled} />
          </div>
        </div>
        {twoFAEnabled && (
          <div className="mt-4 pt-4 border-t border-white/[0.06] flex items-start gap-3">
            <CheckCircle className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
            <p className="text-xs text-white/50">
              La 2FA est activée. Vous devrez entrer un code depuis votre application d'authentification à chaque connexion.
            </p>
          </div>
        )}
      </GlassCard>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Notifications Tab
// ---------------------------------------------------------------------------

function NotificationsTab() {
  const { toast } = useToast();
  const { data: prefs, isLoading } = useNotificationPreferences();
  const updatePrefs = useUpdateNotificationPreferences();

  const [notifs, setNotifs] = useState({
    email_newsletter: true,
    email_events: true,
    push_enabled: false,
    sms_enabled: false,
  });

  useEffect(() => {
    if (prefs) {
      setNotifs({
        email_newsletter: prefs.email_newsletter ?? true,
        email_events: prefs.email_events ?? true,
        push_enabled: prefs.push_enabled ?? false,
        sms_enabled: prefs.sms_enabled ?? false,
      });
    }
  }, [prefs]);

  const toggle = (key: keyof typeof notifs) => (v: boolean) => {
    setNotifs((n) => ({ ...n, [key]: v }));
  };

  const handleSave = () => {
    updatePrefs.mutate(notifs, {
      onSuccess: () => toast({ type: 'success', title: 'Préférences sauvegardées', description: 'Vos paramètres de notification ont été mis à jour.' }),
      onError: () => toast({ type: 'error', title: 'Erreur', description: 'Impossible de sauvegarder les préférences.' }),
    });
  };

  const notifItems = [
    {
      key: 'email_newsletter' as const,
      icon: Mail,
      label: 'Infolettre par courriel',
      description: 'Récapitulatifs hebdomadaires et nouvelles de la communauté.',
    },
    {
      key: 'email_events' as const,
      icon: Mail,
      label: 'Notifications d\'événements',
      description: 'Recevez des mises à jour par courriel pour les événements.',
    },
    {
      key: 'push_enabled' as const,
      icon: Bell,
      label: 'Notifications push',
      description: 'Notifications en temps réel dans le navigateur.',
    },
    {
      key: 'sms_enabled' as const,
      icon: Smartphone,
      label: 'Notifications SMS',
      description: 'Alertes urgentes envoyées par message texte.',
    },
  ];

  return (
    <div className="space-y-6">
      <GlassCard className="p-6">
        <h3 className="text-base font-semibold text-white/90 mb-5 flex items-center gap-2">
          <Bell className="h-4 w-4 text-purple-400" />
          Canaux de notification
        </h3>
        {isLoading ? (
          <div className="space-y-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full rounded-xl" />
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {notifItems.map(({ key, icon: Icon, label, description }) => (
              <div
                key={key}
                className="flex items-center justify-between p-4 rounded-xl bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.05] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="h-9 w-9 rounded-lg bg-purple-500/10 flex items-center justify-center shrink-0">
                    <Icon className="h-4 w-4 text-purple-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white/80">{label}</p>
                    <p className="text-xs text-white/40 mt-0.5">{description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 shrink-0 ml-4">
                  <Badge variant={notifs[key] ? 'success' : 'secondary'}>
                    {notifs[key] ? 'Activé' : 'Désactivé'}
                  </Badge>
                  <Toggle enabled={notifs[key]} onChange={toggle(key)} />
                </div>
              </div>
            ))}
          </div>
        )}
      </GlassCard>

      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={updatePrefs.isPending}>
          {updatePrefs.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
          Sauvegarder les préférences
        </Button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// API Tab
// ---------------------------------------------------------------------------

function ApiTab() {
  const { toast } = useToast();
  const { data: webhookData, isLoading: webhooksLoading } = useWebhooks();
  const createWebhook = useCreateWebhook();
  const deleteWebhookMutation = useDeleteWebhook();

  const webhooks = webhookData?.results ?? [];

  const [webhookDialog, setWebhookDialog] = useState(false);
  const [newWebhook, setNewWebhook] = useState({ name: '', url: '', events: '' });

  const addWebhook = () => {
    if (!newWebhook.url.trim()) {
      toast({ type: 'error', title: 'URL requise', description: "Veuillez entrer l'URL du webhook." });
      return;
    }
    createWebhook.mutate(
      {
        name: newWebhook.name.trim() || 'Webhook',
        url: newWebhook.url.trim(),
        events: newWebhook.events.split(',').map((e) => e.trim()).filter(Boolean),
        is_active: true,
      },
      {
        onSuccess: () => {
          setNewWebhook({ name: '', url: '', events: '' });
          setWebhookDialog(false);
          toast({ type: 'success', title: 'Webhook ajouté', description: 'Le webhook a été enregistré.' });
        },
        onError: () => toast({ type: 'error', title: 'Erreur', description: "Impossible d'ajouter le webhook." }),
      },
    );
  };

  const handleDeleteWebhook = (id: string) => {
    deleteWebhookMutation.mutate(id, {
      onSuccess: () => toast({ type: 'info', title: 'Webhook supprimé' }),
      onError: () => toast({ type: 'error', title: 'Erreur', description: 'Impossible de supprimer le webhook.' }),
    });
  };

  return (
    <div className="space-y-6">
      {/* Webhooks */}
      <GlassCard className="p-6">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-base font-semibold text-white/90 flex items-center gap-2">
            <Globe className="h-4 w-4 text-purple-400" />
            Webhooks
          </h3>
          <Button size="sm" onClick={() => setWebhookDialog(true)}>
            <Plus className="h-3.5 w-3.5 mr-1.5" />
            Ajouter un endpoint
          </Button>
        </div>

        {webhooksLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 2 }).map((_, i) => (
              <Skeleton key={i} className="h-20 w-full rounded-xl" />
            ))}
          </div>
        ) : webhooks.length === 0 ? (
          <p className="text-sm text-white/40 text-center py-6">Aucun webhook configuré.</p>
        ) : (
          <div className="space-y-3">
            {webhooks.map((wh) => (
              <div
                key={wh.id}
                className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.05] transition-colors"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="text-sm font-medium text-white/80">{wh.name}</p>
                    <Badge variant={wh.is_active ? 'success' : 'secondary'}>
                      {wh.is_active ? 'Actif' : 'Inactif'}
                    </Badge>
                  </div>
                  <p className="text-xs font-mono text-white/50 truncate max-w-xs mt-0.5">{wh.url}</p>
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {wh.events.map((ev) => (
                      <span
                        key={ev}
                        className="inline-block text-[10px] font-mono px-2 py-0.5 rounded-md bg-purple-500/10 text-purple-300 border border-purple-500/20"
                      >
                        {ev}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleDeleteWebhook(wh.id)}
                    disabled={deleteWebhookMutation.isPending}
                  >
                    <Trash2 className="h-3.5 w-3.5 mr-1.5" />
                    Supprimer
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </GlassCard>

      {/* Add webhook dialog */}
      <Dialog open={webhookDialog} onClose={() => setWebhookDialog(false)}>
        <DialogHeader>
          <DialogTitle>Ajouter un endpoint webhook</DialogTitle>
          <DialogDescription>
            Configurez une URL pour recevoir des notifications d'événements.
          </DialogDescription>
        </DialogHeader>
        <DialogClose onClose={() => setWebhookDialog(false)} />
        <DialogContent>
          <div className="space-y-4">
            <div>
              <FieldLabel>Nom</FieldLabel>
              <Input
                value={newWebhook.name}
                onChange={(e) => setNewWebhook((w) => ({ ...w, name: e.target.value }))}
                placeholder="Ex. : Intégration site web"
                autoFocus
              />
            </div>
            <div>
              <FieldLabel>URL de l'endpoint</FieldLabel>
              <Input
                value={newWebhook.url}
                onChange={(e) => setNewWebhook((w) => ({ ...w, url: e.target.value }))}
                placeholder="https://monapp.ca/webhook"
              />
            </div>
            <div>
              <FieldLabel>Événements (séparés par des virgules)</FieldLabel>
              <Input
                value={newWebhook.events}
                onChange={(e) => setNewWebhook((w) => ({ ...w, events: e.target.value }))}
                placeholder="member.created, donation.received"
              />
              <p className="text-xs text-white/40 mt-1.5">
                Exemples : member.created, event.created, donation.received
              </p>
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="outline" onClick={() => setWebhookDialog(false)}>
            Annuler
          </Button>
          <Button onClick={addWebhook} disabled={createWebhook.isPending}>
            {createWebhook.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            <Globe className="h-3.5 w-3.5 mr-1.5" />
            Enregistrer
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Campus Tab
// ---------------------------------------------------------------------------

function CampusTab() {
  const { toast } = useToast();
  const { data: campusData, isLoading } = useCampuses();
  const createCampus = useCreateCampus();
  const deleteCampusMutation = useDeleteCampus();

  const campuses = (campusData?.results ?? []) as Campus[];

  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    name: '',
    address: '',
    city: '',
    province: 'QC',
    postal_code: '',
    phone: '',
    email: '',
    is_main: false,
  });

  const handleCreate = () => {
    if (!form.name) {
      toast({ type: 'error', title: 'Champ requis', description: 'Le nom du campus est obligatoire.' });
      return;
    }
    createCampus.mutate(form, {
      onSuccess: () => {
        toast({ type: 'success', title: 'Campus créé', description: `"${form.name}" a été ajouté.` });
        setShowCreate(false);
        setForm({ name: '', address: '', city: '', province: 'QC', postal_code: '', phone: '', email: '', is_main: false });
      },
      onError: () => toast({ type: 'error', title: 'Erreur', description: 'Impossible de créer le campus.' }),
    });
  };

  const handleDelete = (id: string, name: string) => {
    deleteCampusMutation.mutate(id, {
      onSuccess: () => toast({ type: 'info', title: 'Campus supprimé', description: `"${name}" a été retiré.` }),
      onError: () => toast({ type: 'error', title: 'Erreur', description: 'Impossible de supprimer le campus.' }),
    });
  };

  return (
    <div className="space-y-6">
      <GlassCard className="p-6">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-base font-semibold text-white/90 flex items-center gap-2">
            <Building className="h-4 w-4 text-purple-400" />
            Campus & Emplacements
          </h3>
          <Button size="sm" onClick={() => setShowCreate(true)}>
            <Plus className="h-3.5 w-3.5 mr-1.5" />
            Ajouter un campus
          </Button>
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 2 }).map((_, i) => (
              <Skeleton key={i} className="h-24 w-full rounded-xl" />
            ))}
          </div>
        ) : campuses.length === 0 ? (
          <p className="text-sm text-white/40 text-center py-8">Aucun campus configuré.</p>
        ) : (
          <div className="space-y-3">
            {campuses.map((campus) => (
              <div
                key={campus.id}
                className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.05] transition-colors"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="text-sm font-medium text-white/80">{campus.name}</p>
                    {campus.is_main && <Badge variant="default">Principal</Badge>}
                    <Badge variant={campus.is_active ? 'success' : 'secondary'}>
                      {campus.is_active ? 'Actif' : 'Inactif'}
                    </Badge>
                  </div>
                  {campus.address && (
                    <p className="text-xs text-white/50 mt-0.5 flex items-center gap-1">
                      <MapPin className="h-3 w-3" />
                      {campus.address}{campus.city ? `, ${campus.city}` : ''}{campus.province ? ` ${campus.province}` : ''} {campus.postal_code}
                    </p>
                  )}
                  <div className="flex gap-4 mt-1 text-xs text-white/40">
                    {campus.phone && <span>{campus.phone}</span>}
                    {campus.email && <span>{campus.email}</span>}
                  </div>
                </div>
                <Button
                  variant="destructive"
                  size="sm"
                  className="shrink-0"
                  onClick={() => handleDelete(campus.id, campus.name)}
                  disabled={deleteCampusMutation.isPending}
                >
                  <Trash2 className="h-3.5 w-3.5 mr-1.5" />
                  Supprimer
                </Button>
              </div>
            ))}
          </div>
        )}
      </GlassCard>

      <Dialog open={showCreate} onClose={() => setShowCreate(false)}>
        <DialogHeader>
          <DialogTitle>Ajouter un campus</DialogTitle>
          <DialogDescription>Enregistrer un nouvel emplacement pour votre église.</DialogDescription>
          <DialogClose onClose={() => setShowCreate(false)} />
        </DialogHeader>
        <DialogContent>
          <div className="space-y-4">
            <div>
              <FieldLabel>Nom du campus *</FieldLabel>
              <Input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} placeholder="Campus Nord..." />
            </div>
            <div>
              <FieldLabel>Adresse</FieldLabel>
              <Input value={form.address} onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))} placeholder="123 rue de l'Église" />
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <FieldLabel>Ville</FieldLabel>
                <Input value={form.city} onChange={(e) => setForm((f) => ({ ...f, city: e.target.value }))} placeholder="Montréal" />
              </div>
              <div>
                <FieldLabel>Province</FieldLabel>
                <Select value={form.province} onChange={(e) => setForm((f) => ({ ...f, province: e.target.value }))}>
                  <option value="QC">Québec</option>
                  <option value="ON">Ontario</option>
                  <option value="AB">Alberta</option>
                  <option value="BC">Colombie-Britannique</option>
                  <option value="NB">Nouveau-Brunswick</option>
                  <option value="NS">Nouvelle-Écosse</option>
                </Select>
              </div>
              <div>
                <FieldLabel>Code postal</FieldLabel>
                <Input value={form.postal_code} onChange={(e) => setForm((f) => ({ ...f, postal_code: e.target.value }))} placeholder="H1A 1A1" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <FieldLabel>Téléphone</FieldLabel>
                <Input value={form.phone} onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))} placeholder="514-000-0000" />
              </div>
              <div>
                <FieldLabel>Courriel</FieldLabel>
                <Input value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} type="email" placeholder="campus@eglise.ca" />
              </div>
            </div>
          </div>
        </DialogContent>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setShowCreate(false)}>Annuler</Button>
          <Button onClick={handleCreate} disabled={createCampus.isPending}>
            {createCampus.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            Ajouter le campus
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Audit Logs Tab
// ---------------------------------------------------------------------------

function AuditTab() {
  const [actionFilter, setActionFilter] = useState('');
  const [page, setPage] = useState(1);

  const params = new URLSearchParams({ page: String(page), page_size: '20' });
  if (actionFilter) params.set('action', actionFilter);

  const { data, isLoading } = useAuditLogs(params.toString());
  const logs = (data?.results ?? []) as AuditLog[];
  const totalCount = data?.count ?? 0;

  const actionLabels: Record<string, string> = {
    create: 'Création',
    update: 'Modification',
    delete: 'Suppression',
  };
  const actionColors: Record<string, string> = {
    create: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    update: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    delete: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
  };

  return (
    <div className="space-y-6">
      <GlassCard className="p-6">
        <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
          <h3 className="text-base font-semibold text-white/90 flex items-center gap-2">
            <ScrollText className="h-4 w-4 text-purple-400" />
            Journal d&apos;audit — {totalCount} entrée{totalCount !== 1 ? 's' : ''}
          </h3>
          <div className="flex items-center gap-2">
            <Select value={actionFilter} onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}>
              <option value="">Toutes les actions</option>
              <option value="create">Création</option>
              <option value="update">Modification</option>
              <option value="delete">Suppression</option>
            </Select>
          </div>
        </div>

        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-14 w-full rounded-xl" />)}
          </div>
        ) : logs.length === 0 ? (
          <p className="text-sm text-white/40 text-center py-8">Aucune entrée de journal trouvée.</p>
        ) : (
          <div className="space-y-2">
            {logs.map((log) => (
              <div
                key={log.id}
                className="flex items-start gap-3 p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]"
              >
                <Badge className={`border shrink-0 mt-0.5 ${actionColors[log.action] ?? 'bg-white/10 text-white/60 border-white/10'}`}>
                  {actionLabels[log.action] ?? log.action_display ?? log.action}
                </Badge>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white/80">
                    <span className="font-medium">{log.username || 'Système'}</span>
                    {' — '}
                    <span className="text-white/60">{log.model_name}</span>
                    {log.object_repr && (
                      <span className="text-white/50"> · {log.object_repr}</span>
                    )}
                  </p>
                  <p className="text-xs text-white/40 mt-0.5">
                    {new Date(log.created_at).toLocaleString('fr-CA')}
                    {log.ip_address && ` · ${log.ip_address}`}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}

        {totalCount > 20 && (
          <div className="flex items-center justify-center gap-2 mt-4 pt-4 border-t border-white/[0.06]">
            <Button variant="ghost" size="sm" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>Précédent</Button>
            <span className="text-xs text-white/40">Page {page} / {Math.ceil(totalCount / 20)}</span>
            <Button variant="ghost" size="sm" disabled={page * 20 >= totalCount} onClick={() => setPage((p) => p + 1)}>Suivant</Button>
          </div>
        )}
      </GlassCard>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Login Audits Tab
// ---------------------------------------------------------------------------

function LoginAuditsTab() {
  const [successFilter, setSuccessFilter] = useState('');
  const [page, setPage] = useState(1);

  const params = new URLSearchParams({ page: String(page), page_size: '20' });
  if (successFilter) params.set('success', successFilter);

  const { data, isLoading } = useLoginAudits(params.toString());
  const audits = (data?.results ?? []) as LoginAudit[];
  const totalCount = data?.count ?? 0;

  return (
    <div className="space-y-6">
      <GlassCard className="p-6">
        <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
          <h3 className="text-base font-semibold text-white/90 flex items-center gap-2">
            <LogIn className="h-4 w-4 text-purple-400" />
            Historique des connexions — {totalCount} entrée{totalCount !== 1 ? 's' : ''}
          </h3>
          <Select value={successFilter} onChange={(e) => { setSuccessFilter(e.target.value); setPage(1); }}>
            <option value="">Toutes</option>
            <option value="true">Réussies</option>
            <option value="false">Échouées</option>
          </Select>
        </div>

        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-14 w-full rounded-xl" />)}
          </div>
        ) : audits.length === 0 ? (
          <p className="text-sm text-white/40 text-center py-8">Aucune connexion enregistrée.</p>
        ) : (
          <div className="space-y-2">
            {audits.map((audit) => (
              <div
                key={audit.id}
                className="flex items-start gap-3 p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]"
              >
                <div className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 ${
                  audit.success ? 'bg-emerald-500/20' : 'bg-rose-500/20'
                }`}>
                  {audit.success
                    ? <CheckCircle className="h-4 w-4 text-emerald-400" />
                    : <XCircle className="h-4 w-4 text-rose-400" />
                  }
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="text-sm font-medium text-white/80">
                      {audit.email_attempted || audit.username || 'Inconnu'}
                    </p>
                    <Badge variant={audit.success ? 'success' : 'destructive'}>
                      {audit.success ? 'Réussi' : 'Échoué'}
                    </Badge>
                    {audit.method && (
                      <Badge variant="outline" className="text-[10px]">{audit.method}</Badge>
                    )}
                  </div>
                  <p className="text-xs text-white/40 mt-0.5">
                    {new Date(audit.created_at).toLocaleString('fr-CA')}
                    {audit.ip_address && ` · IP: ${audit.ip_address}`}
                  </p>
                  {!audit.success && audit.failure_reason && (
                    <p className="text-xs text-rose-400/70 mt-0.5">{audit.failure_reason}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {totalCount > 20 && (
          <div className="flex items-center justify-center gap-2 mt-4 pt-4 border-t border-white/[0.06]">
            <Button variant="ghost" size="sm" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>Précédent</Button>
            <span className="text-xs text-white/40">Page {page} / {Math.ceil(totalCount / 20)}</span>
            <Button variant="ghost" size="sm" disabled={page * 20 >= totalCount} onClick={() => setPage((p) => p + 1)}>Suivant</Button>
          </div>
        )}
      </GlassCard>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

const TABS = [
  { value: 'eglise', label: 'Église', icon: Church },
  { value: 'campus', label: 'Campus', icon: Building },
  { value: 'profil', label: 'Profil', icon: User },
  { value: 'securite', label: 'Sécurité', icon: Shield },
  { value: 'notifications', label: 'Notifications', icon: Bell },
  { value: 'api', label: 'API', icon: Key },
  { value: 'audit', label: 'Journal', icon: ScrollText },
  { value: 'connexions', label: 'Connexions', icon: LogIn },
] as const;

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-white/90">Paramètres</h1>
        <p className="text-sm text-white/50 mt-1">
          Gérez les paramètres de votre église, votre profil et vos préférences.
        </p>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="eglise">
        <TabsList className="flex-wrap h-auto">
          {TABS.map(({ value, label, icon: Icon }) => (
            <TabsTrigger key={value} value={value}>
              <Icon className="h-3.5 w-3.5 mr-1.5 inline-block" />
              {label}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="eglise">
          <EgliseTab />
        </TabsContent>

        <TabsContent value="profil">
          <ProfilTab />
        </TabsContent>

        <TabsContent value="securite">
          <SecuriteTab />
        </TabsContent>

        <TabsContent value="notifications">
          <NotificationsTab />
        </TabsContent>

        <TabsContent value="api">
          <ApiTab />
        </TabsContent>

        <TabsContent value="campus">
          <CampusTab />
        </TabsContent>

        <TabsContent value="audit">
          <AuditTab />
        </TabsContent>

        <TabsContent value="connexions">
          <LoginAuditsTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
