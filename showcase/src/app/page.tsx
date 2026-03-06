import {
  Users,
  Heart,
  Calendar,
  HandCoins,
  Music,
  Bell,
  BarChart3,
  Shield,
  Smartphone,
  Globe,
  Zap,
  CheckCircle,
  ArrowRight,
  Church,
  MessageSquare,
  ClipboardList,
  UserPlus,
  CreditCard,
} from 'lucide-react';

const FEATURES = [
  {
    icon: Users,
    title: 'Gestion des membres',
    description:
      'Profils complets, familles, rôles, groupes, cycle de vie, champs personnalisés, fusions de doublons et importation en masse.',
  },
  {
    icon: HandCoins,
    title: 'Dons et finances',
    description:
      'Dons en ligne (Stripe), par SMS (Twilio), crypto (Coinbase), campagnes, promesses de dons, reçus fiscaux et rapports analytiques.',
  },
  {
    icon: Calendar,
    title: 'Événements',
    description:
      'Création d\'événements avec récurrence, inscriptions, listes d\'attente, gestion de salles, modèles et intégration calendrier.',
  },
  {
    icon: ClipboardList,
    title: 'Bénévoles',
    description:
      'Postes, horaires, disponibilités, échanges de quarts, heures de service, compétences, reconnaissance et vérification des antécédents.',
  },
  {
    icon: MessageSquare,
    title: 'Communication',
    description:
      'Infolettres, SMS, notifications push (VAPID), messages directs, clavardage de groupe, modèles, automatisations et tests A/B.',
  },
  {
    icon: Heart,
    title: 'Demandes d\'aide',
    description:
      'Requêtes de prières, soins pastoraux, équipes de soins, fonds de bienfaisance, trains de repas et protocoles de crise.',
  },
  {
    icon: Music,
    title: 'Culte et louange',
    description:
      'Services, sections, assignations, sermons, séries, chansons, setlists, répétitions, demandes de chants et diffusion en direct.',
  },
  {
    icon: UserPlus,
    title: 'Accueil et intégration',
    description:
      'Parcours d\'intégration, cours, entrevues, codes d\'invitation, mentorat, documents à signer, quiz et séquences de bienvenue.',
  },
  {
    icon: CheckCircle,
    title: 'Présences',
    description:
      'Sessions, check-in par QR/NFC, familles, enfants avec code de sécurité, visiteurs, géo-clôtures, alertes d\'absence et analytiques.',
  },
  {
    icon: CreditCard,
    title: 'Paiements',
    description:
      'Intégration Stripe, dons récurrents, campagnes de collecte, kiosques de don, relevés et objectifs de don personnels.',
  },
  {
    icon: BarChart3,
    title: 'Rapports',
    description:
      'Tableaux de bord visuels, rapports programmés, rapports sauvegardés, exportation CSV/PDF et analytiques prédictives.',
  },
  {
    icon: Shield,
    title: 'Sécurité',
    description:
      'JWT avec rotation, 2FA (TOTP), RBAC par rôle, journal d\'audit complet, audit de connexion, throttling et en-têtes HTTPS.',
  },
];

const STATS = [
  { value: '12', label: 'Modules' },
  { value: '153+', label: 'Modèles de données' },
  { value: '114+', label: 'Endpoints API' },
  { value: '1141', label: 'Tests automatisés' },
];

const PRICING = [
  {
    name: 'Essentiel',
    price: '0',
    period: '/mois',
    description: 'Pour les petites églises qui débutent',
    features: [
      'Jusqu\'à 100 membres',
      'Gestion des membres',
      'Événements de base',
      'Présences par QR',
      'Notifications in-app',
      'Support communautaire',
    ],
    cta: 'Commencer gratuitement',
    highlighted: false,
  },
  {
    name: 'Professionnel',
    price: '49',
    period: '/mois',
    description: 'Pour les églises en croissance',
    features: [
      'Membres illimités',
      'Tous les modules',
      'Dons en ligne (Stripe)',
      'SMS et push notifications',
      'Rapports avancés',
      'Multi-campus',
      'Support prioritaire',
    ],
    cta: 'Essai gratuit 30 jours',
    highlighted: true,
  },
  {
    name: 'Entreprise',
    price: 'Sur mesure',
    period: '',
    description: 'Pour les grandes organisations',
    features: [
      'Tout de Professionnel',
      'Déploiement dédié',
      'API personnalisée',
      'Intégrations sur mesure',
      'Formation sur site',
      'SLA garanti',
      'Gestionnaire de compte dédié',
    ],
    cta: 'Nous contacter',
    highlighted: false,
  },
];

export default function HomePage() {
  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="fixed top-0 z-50 w-full glass">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2">
            <Church className="h-8 w-8 text-primary" />
            <span className="text-xl font-bold">ÉgliseConnect</span>
          </div>
          <div className="hidden items-center gap-8 md:flex">
            <a href="#fonctionnalites" className="text-sm text-slate-300 hover:text-white transition-colors">
              Fonctionnalités
            </a>
            <a href="#tarifs" className="text-sm text-slate-300 hover:text-white transition-colors">
              Tarifs
            </a>
            <a href="#technologie" className="text-sm text-slate-300 hover:text-white transition-colors">
              Technologie
            </a>
            <a
              href="#contact"
              className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary-dark transition-colors"
            >
              Démo gratuite
            </a>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="hero-gradient relative flex min-h-screen items-center pt-20">
        <div className="mx-auto max-w-7xl px-6 py-24 text-center">
          <div className="mx-auto max-w-4xl">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-sm text-primary-light">
              <Zap className="h-4 w-4" />
              Propulsé par l&apos;intelligence artificielle
            </div>
            <h1 className="mb-6 text-5xl font-extrabold leading-tight tracking-tight md:text-7xl">
              Gérez votre église{' '}
              <span className="gradient-text">intelligemment</span>
            </h1>
            <p className="mx-auto mb-10 max-w-2xl text-lg text-slate-400 md:text-xl">
              La plateforme tout-en-un qui simplifie la gestion de votre communauté.
              Membres, dons, événements, communication — tout au même endroit,
              automatisé et sécurisé.
            </p>
            <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
              <a
                href="#tarifs"
                className="inline-flex items-center gap-2 rounded-xl bg-primary px-8 py-4 text-lg font-semibold text-white shadow-lg shadow-primary/25 hover:bg-primary-dark transition-all"
              >
                Commencer gratuitement
                <ArrowRight className="h-5 w-5" />
              </a>
              <a
                href="#fonctionnalites"
                className="inline-flex items-center gap-2 rounded-xl border border-slate-600 px-8 py-4 text-lg font-semibold text-slate-200 hover:border-slate-400 transition-all"
              >
                Découvrir les fonctionnalités
              </a>
            </div>
          </div>

          {/* Stats */}
          <div className="mt-20 grid grid-cols-2 gap-6 md:grid-cols-4">
            {STATS.map((stat) => (
              <div key={stat.label} className="glass rounded-2xl p-6">
                <div className="text-3xl font-bold gradient-text">{stat.value}</div>
                <div className="mt-1 text-sm text-slate-400">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="fonctionnalites" className="py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-16 text-center">
            <h2 className="mb-4 text-4xl font-bold md:text-5xl">
              Tout ce dont votre église a besoin
            </h2>
            <p className="mx-auto max-w-2xl text-lg text-slate-400">
              12 modules intégrés couvrant chaque aspect de la gestion d&apos;église,
              de l&apos;accueil des nouveaux membres aux rapports financiers.
            </p>
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((feature) => (
              <div
                key={feature.title}
                className="feature-card glass rounded-2xl p-6 transition-all duration-300"
              >
                <div className="mb-4 inline-flex rounded-xl bg-primary/15 p-3">
                  <feature.icon className="h-6 w-6 text-primary-light" />
                </div>
                <h3 className="mb-2 text-lg font-semibold">{feature.title}</h3>
                <p className="text-sm leading-relaxed text-slate-400">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Technology */}
      <section id="technologie" className="py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="grid items-center gap-12 lg:grid-cols-2">
            <div>
              <h2 className="mb-6 text-4xl font-bold md:text-5xl">
                Technologie <span className="gradient-text">moderne</span>
              </h2>
              <p className="mb-8 text-lg text-slate-400">
                Construit avec les meilleures technologies du marché pour offrir
                performance, sécurité et une expérience utilisateur exceptionnelle.
              </p>
              <div className="space-y-4">
                {[
                  {
                    icon: Globe,
                    title: 'Application web progressive (PWA)',
                    desc: 'Fonctionne sur mobile, tablette et ordinateur avec support hors-ligne.',
                  },
                  {
                    icon: Shield,
                    title: 'Sécurité entreprise',
                    desc: 'JWT, 2FA, chiffrement, RBAC, audit complet et conformité PIPEDA.',
                  },
                  {
                    icon: Bell,
                    title: 'Notifications multicanal',
                    desc: 'Push (VAPID), email (SMTP), SMS (Twilio), in-app — tout automatisé.',
                  },
                  {
                    icon: Smartphone,
                    title: 'API REST complète',
                    desc: '114+ endpoints documentés avec OpenAPI/Swagger pour intégrations tierces.',
                  },
                ].map((item) => (
                  <div key={item.title} className="flex gap-4">
                    <div className="shrink-0 rounded-xl bg-primary/15 p-3">
                      <item.icon className="h-5 w-5 text-primary-light" />
                    </div>
                    <div>
                      <h4 className="font-semibold">{item.title}</h4>
                      <p className="text-sm text-slate-400">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="glass animate-float rounded-3xl p-8">
              <div className="space-y-4 font-mono text-sm">
                <div className="text-slate-500">// Stack technologique</div>
                <div>
                  <span className="text-primary-light">backend</span>
                  <span className="text-slate-500">:</span>{' '}
                  <span className="text-cyan-400">Django 5.2 + DRF + Celery</span>
                </div>
                <div>
                  <span className="text-primary-light">frontend</span>
                  <span className="text-slate-500">:</span>{' '}
                  <span className="text-cyan-400">Next.js 15 + TypeScript</span>
                </div>
                <div>
                  <span className="text-primary-light">ui</span>
                  <span className="text-slate-500">:</span>{' '}
                  <span className="text-cyan-400">Tailwind v4 + Glassmorphism</span>
                </div>
                <div>
                  <span className="text-primary-light">state</span>
                  <span className="text-slate-500">:</span>{' '}
                  <span className="text-cyan-400">TanStack Query + Zustand</span>
                </div>
                <div>
                  <span className="text-primary-light">auth</span>
                  <span className="text-slate-500">:</span>{' '}
                  <span className="text-cyan-400">JWT + 2FA (TOTP)</span>
                </div>
                <div>
                  <span className="text-primary-light">payments</span>
                  <span className="text-slate-500">:</span>{' '}
                  <span className="text-cyan-400">Stripe + Twilio + Coinbase</span>
                </div>
                <div>
                  <span className="text-primary-light">realtime</span>
                  <span className="text-slate-500">:</span>{' '}
                  <span className="text-cyan-400">Django Channels + WebSocket</span>
                </div>
                <div>
                  <span className="text-primary-light">database</span>
                  <span className="text-slate-500">:</span>{' '}
                  <span className="text-cyan-400">PostgreSQL 16 + Redis</span>
                </div>
                <div>
                  <span className="text-primary-light">deploy</span>
                  <span className="text-slate-500">:</span>{' '}
                  <span className="text-cyan-400">Docker + Nginx + CI/CD</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="tarifs" className="py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-16 text-center">
            <h2 className="mb-4 text-4xl font-bold md:text-5xl">
              Tarifs <span className="gradient-text">simples</span>
            </h2>
            <p className="mx-auto max-w-2xl text-lg text-slate-400">
              Commencez gratuitement, évoluez selon vos besoins.
              Aucune carte de crédit requise pour l&apos;essai.
            </p>
          </div>
          <div className="grid gap-8 lg:grid-cols-3">
            {PRICING.map((plan) => (
              <div
                key={plan.name}
                className={`relative rounded-3xl p-8 transition-all ${
                  plan.highlighted
                    ? 'border-2 border-primary bg-primary/5 shadow-lg shadow-primary/10'
                    : 'glass'
                }`}
              >
                {plan.highlighted && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 rounded-full bg-primary px-4 py-1 text-xs font-semibold text-white">
                    Populaire
                  </div>
                )}
                <h3 className="mb-2 text-xl font-bold">{plan.name}</h3>
                <p className="mb-4 text-sm text-slate-400">{plan.description}</p>
                <div className="mb-6">
                  {plan.price === 'Sur mesure' ? (
                    <span className="text-3xl font-bold">Sur mesure</span>
                  ) : (
                    <>
                      <span className="text-5xl font-bold">{plan.price}$</span>
                      <span className="text-slate-400">{plan.period}</span>
                    </>
                  )}
                </div>
                <ul className="mb-8 space-y-3">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-sm">
                      <CheckCircle className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
                      <span className="text-slate-300">{f}</span>
                    </li>
                  ))}
                </ul>
                <a
                  href="#contact"
                  className={`block w-full rounded-xl py-3 text-center font-semibold transition-colors ${
                    plan.highlighted
                      ? 'bg-primary text-white hover:bg-primary-dark'
                      : 'border border-slate-600 text-slate-200 hover:border-slate-400'
                  }`}
                >
                  {plan.cta}
                </a>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA / Contact */}
      <section id="contact" className="py-24">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <div className="glass rounded-3xl p-12">
            <h2 className="mb-4 text-4xl font-bold">
              Prêt à transformer votre église?
            </h2>
            <p className="mx-auto mb-8 max-w-xl text-lg text-slate-400">
              Rejoignez les églises qui utilisent ÉgliseConnect pour simplifier
              leur gestion et se concentrer sur ce qui compte vraiment.
            </p>
            <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
              <a
                href="mailto:info@egliseconnect.ca"
                className="inline-flex items-center gap-2 rounded-xl bg-primary px-8 py-4 text-lg font-semibold text-white shadow-lg shadow-primary/25 hover:bg-primary-dark transition-all"
              >
                Demander une démo
                <ArrowRight className="h-5 w-5" />
              </a>
            </div>
            <p className="mt-6 text-sm text-slate-500">
              Déploiement en moins de 24h. Support en français.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-12">
        <div className="mx-auto max-w-7xl px-6">
          <div className="flex flex-col items-center justify-between gap-6 md:flex-row">
            <div className="flex items-center gap-2">
              <Church className="h-6 w-6 text-primary" />
              <span className="font-semibold">ÉgliseConnect</span>
            </div>
            <p className="text-sm text-slate-500">
              &copy; {new Date().getFullYear()} ÉgliseConnect. Tous droits réservés.
              Fait avec amour au Québec.
            </p>
            <div className="flex gap-6">
              <a href="#" className="text-sm text-slate-500 hover:text-slate-300 transition-colors">
                Confidentialité
              </a>
              <a href="#" className="text-sm text-slate-500 hover:text-slate-300 transition-colors">
                Conditions
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
