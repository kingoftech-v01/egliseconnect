# Plan d'implementation - EgliseConnect v2.0

## Vue d'ensemble

Refonte majeure du systeme avec un flux d'onboarding complet
(inscription -> membre officiel) et des fonctionnalites Phase 1
(auth, PWA, presences, dons en ligne).

---

## ARCHITECTURE GLOBALE

### Nouvelles apps Django a creer

```
apps/
  onboarding/      # NOUVEAU - Parcours inscription -> membre
  attendance/      # NOUVEAU - Check-in QR + presences
  payments/        # NOUVEAU - Dons en ligne Stripe
```

### Apps existantes a modifier

```
apps/core/         # Nouvelles constantes (MembershipStatus, etc.)
apps/members/      # Ajout membership_status, champs onboarding
config/settings/   # 2FA, PWA, Stripe config
templates/         # Nouveaux templates dashboard conditionnel
```

### Nouvelles dependances (requirements.txt)

```
# Authentification 2FA
django-otp>=1.3
django-two-factor-auth>=1.16
qrcode>=7.4

# PWA
django-pwa>=1.1

# Paiements
stripe>=8.0
dj-stripe>=2.8    # OU integration Stripe directe

# QR Code generation
qrcode[pil]>=7.4
python-barcode>=0.15
```

---

## SPRINT 1 : Statut membre + Onboarding (Semaine 1-2)

### 1.1 Nouvelles constantes dans `apps/core/constants.py`

```python
class MembershipStatus:
    """Etapes du parcours d'adhesion."""
    REGISTERED = 'registered'       # Compte cree, QR seulement
    FORM_PENDING = 'form_pending'   # 30 jours pour remplir formulaire
    FORM_SUBMITTED = 'form_submitted'  # Formulaire soumis, attente admin
    IN_REVIEW = 'in_review'         # Admin examine le dossier
    APPROVED = 'approved'           # Approuve, en attente de parcours
    IN_TRAINING = 'in_training'     # Parcours de formation en cours
    INTERVIEW_SCHEDULED = 'interview_scheduled'  # Interview planifiee
    ACTIVE = 'active'              # Membre officiel - acces complet
    SUSPENDED = 'suspended'        # Compte suspendu
    REJECTED = 'rejected'          # Refuse a une etape
    EXPIRED = 'expired'            # Formulaire non soumis dans les 30j

    CHOICES = [
        (REGISTERED, 'Inscrit'),
        (FORM_PENDING, 'Formulaire en attente'),
        (FORM_SUBMITTED, 'Formulaire soumis'),
        (IN_REVIEW, 'En cours de revision'),
        (APPROVED, 'Approuve'),
        (IN_TRAINING, 'En formation'),
        (INTERVIEW_SCHEDULED, 'Interview planifiee'),
        (ACTIVE, 'Membre actif'),
        (SUSPENDED, 'Suspendu'),
        (REJECTED, 'Refuse'),
        (EXPIRED, 'Expire'),
    ]

    # Statuts qui permettent l'acces au QR de presence
    QR_ALLOWED = [REGISTERED, FORM_PENDING, FORM_SUBMITTED,
                  IN_REVIEW, APPROVED, IN_TRAINING,
                  INTERVIEW_SCHEDULED, ACTIVE]

    # Statuts qui permettent l'acces complet au dashboard
    FULL_ACCESS = [ACTIVE]

    # Statuts en cours de processus (pas encore membre)
    IN_PROCESS = [REGISTERED, FORM_PENDING, FORM_SUBMITTED,
                  IN_REVIEW, APPROVED, IN_TRAINING, INTERVIEW_SCHEDULED]


class InterviewStatus:
    """Resultat de l'interview finale."""
    PROPOSED = 'proposed'       # Date proposee par admin
    ACCEPTED = 'accepted'       # Membre a accepte la date
    COUNTER = 'counter'         # Membre propose autre date
    CONFIRMED = 'confirmed'     # Date finale confirmee
    COMPLETED_PASS = 'passed'   # Interview reussie
    COMPLETED_FAIL = 'failed'   # Interview echouee
    NO_SHOW = 'no_show'         # Absent a l'interview
    CANCELLED = 'cancelled'     # Annulee par admin

    CHOICES = [
        (PROPOSED, 'Date proposee'),
        (ACCEPTED, 'Acceptee'),
        (COUNTER, 'Contre-proposition'),
        (CONFIRMED, 'Confirmee'),
        (COMPLETED_PASS, 'Reussie'),
        (COMPLETED_FAIL, 'Echouee'),
        (NO_SHOW, 'Absent'),
        (CANCELLED, 'Annulee'),
    ]


class LessonStatus:
    """Statut de presence a une lecon."""
    UPCOMING = 'upcoming'
    COMPLETED = 'completed'
    ABSENT = 'absent'
    MAKEUP = 'makeup'         # Session de rattrapage

    CHOICES = [
        (UPCOMING, 'A venir'),
        (COMPLETED, 'Completee'),
        (ABSENT, 'Absent'),
        (MAKEUP, 'Rattrapage'),
    ]
```

### 1.2 Modification du modele Member (`apps/members/models.py`)

Nouveaux champs a ajouter au modele `Member` existant :

```python
# --- CHAMPS ONBOARDING ---
membership_status = models.CharField(
    max_length=30,
    choices=MembershipStatus.CHOICES,
    default=MembershipStatus.REGISTERED,
    db_index=True,
    verbose_name='Statut d\'adhesion'
)

registration_date = models.DateTimeField(
    auto_now_add=True,
    verbose_name='Date d\'inscription'
)

form_deadline = models.DateTimeField(
    null=True, blank=True,
    verbose_name='Date limite formulaire'
)

form_submitted_at = models.DateTimeField(
    null=True, blank=True,
    verbose_name='Formulaire soumis le'
)

admin_reviewed_at = models.DateTimeField(
    null=True, blank=True,
    verbose_name='Revise par admin le'
)

admin_reviewed_by = models.ForeignKey(
    'self', null=True, blank=True,
    on_delete=models.SET_NULL,
    related_name='reviewed_members',
    verbose_name='Revise par'
)

became_active_at = models.DateTimeField(
    null=True, blank=True,
    verbose_name='Devenu membre actif le'
)

rejection_reason = models.TextField(
    blank=True,
    verbose_name='Raison du refus'
)

# --- Champ 2FA ---
two_factor_enabled = models.BooleanField(
    default=False,
    verbose_name='2FA active'
)

two_factor_deadline = models.DateTimeField(
    null=True, blank=True,
    verbose_name='Date limite activation 2FA'
)
```

Nouvelles proprietes :

```python
@property
def days_remaining_for_form(self):
    """Jours restants pour soumettre le formulaire."""
    if not self.form_deadline:
        return None
    from django.utils import timezone
    delta = self.form_deadline - timezone.now()
    return max(0, delta.days)

@property
def is_form_expired(self):
    """Le delai de 30 jours est-il depasse?"""
    if not self.form_deadline:
        return False
    from django.utils import timezone
    return timezone.now() > self.form_deadline

@property
def has_full_access(self):
    """Acces complet au dashboard?"""
    return self.membership_status == MembershipStatus.ACTIVE

@property
def can_use_qr(self):
    """Peut utiliser le QR pour les presences?"""
    return self.membership_status in MembershipStatus.QR_ALLOWED
```

### 1.3 Nouvelle app : `apps/onboarding/`

#### Structure

```
apps/onboarding/
  __init__.py
  admin.py
  apps.py
  constants.py
  forms.py
  models.py
  serializers.py
  services.py          # Logique metier (transitions, rappels)
  signals.py           # Auto-creation profil onboarding
  tasks.py             # Taches Celery (rappels, expiration)
  urls.py
  views_api.py
  views_frontend.py
  tests/
    __init__.py
    factories.py
    test_models.py
    test_views_api.py
    test_views_frontend.py
    test_services.py
    test_tasks.py
  migrations/
    __init__.py
```

#### Modeles

```python
class TrainingCourse(BaseModel):
    """Modele de parcours de formation defini par l'admin."""
    name = models.CharField(max_length=200)        # "Parcours Decouverte 2025"
    description = models.TextField(blank=True)
    total_lessons = models.PositiveIntegerField(default=5)
    is_default = models.BooleanField(default=False) # Parcours par defaut
    created_by = models.ForeignKey(Member, ...)

    # Meta
    class Meta:
        verbose_name = 'Parcours de formation'


class Lesson(BaseModel):
    """Une lecon individuelle dans un parcours."""
    course = models.ForeignKey(TrainingCourse, related_name='lessons')
    order = models.PositiveIntegerField()          # Lecon #1, #2, etc.
    title = models.CharField(max_length=200)       # "Introduction a la foi"
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=90)

    # Supports pedagogiques
    materials_pdf = models.FileField(upload_to='lessons/pdf/', blank=True)
    materials_audio = models.FileField(upload_to='lessons/audio/', blank=True)
    materials_notes = models.TextField(blank=True)  # Notes texte

    class Meta:
        ordering = ['course', 'order']
        unique_together = ['course', 'order']


class MemberTraining(BaseModel):
    """Assignation d'un parcours a un membre specifique."""
    member = models.ForeignKey(Member, related_name='trainings')
    course = models.ForeignKey(TrainingCourse, related_name='enrollments')
    assigned_by = models.ForeignKey(Member, related_name='assigned_trainings')
    assigned_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ['member', 'course']

    @property
    def progress_percentage(self):
        total = self.scheduled_lessons.count()
        done = self.scheduled_lessons.filter(
            status=LessonStatus.COMPLETED
        ).count()
        return int((done / total) * 100) if total > 0 else 0

    @property
    def completed_count(self):
        return self.scheduled_lessons.filter(
            status=LessonStatus.COMPLETED
        ).count()

    @property
    def total_count(self):
        return self.scheduled_lessons.count()


class ScheduledLesson(BaseModel):
    """Une lecon planifiee pour un membre avec date/heure."""
    training = models.ForeignKey(MemberTraining, related_name='scheduled_lessons')
    lesson = models.ForeignKey(Lesson, related_name='scheduled_instances')
    scheduled_date = models.DateTimeField()    # Date/heure precise
    location = models.CharField(max_length=200, blank=True)  # Lieu a l'eglise
    status = models.CharField(
        max_length=20,
        choices=LessonStatus.CHOICES,
        default=LessonStatus.UPCOMING
    )
    attended_at = models.DateTimeField(null=True, blank=True)
    marked_by = models.ForeignKey(
        Member, null=True, blank=True,
        related_name='marked_lessons'
    )  # Qui a scanne le QR
    is_makeup = models.BooleanField(default=False)  # Session de rattrapage
    notes = models.TextField(blank=True)

    # Rappels
    reminder_3days_sent = models.BooleanField(default=False)
    reminder_1day_sent = models.BooleanField(default=False)
    reminder_sameday_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ['scheduled_date']


class Interview(BaseModel):
    """Interview finale pour devenir membre officiel."""
    member = models.ForeignKey(Member, related_name='interviews')
    training = models.ForeignKey(MemberTraining, related_name='interview')
    status = models.CharField(
        max_length=20,
        choices=InterviewStatus.CHOICES,
        default=InterviewStatus.PROPOSED
    )

    # Planification
    proposed_date = models.DateTimeField()        # Date proposee par admin
    counter_proposed_date = models.DateTimeField(  # Contre-proposition membre
        null=True, blank=True
    )
    confirmed_date = models.DateTimeField(         # Date finale
        null=True, blank=True
    )
    location = models.CharField(max_length=200, blank=True)

    # Gestion
    interviewer = models.ForeignKey(
        Member, related_name='conducted_interviews'
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    result_notes = models.TextField(blank=True)

    # Rappels
    reminder_3days_sent = models.BooleanField(default=False)
    reminder_1day_sent = models.BooleanField(default=False)
    reminder_sameday_sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Interview'
        ordering = ['-proposed_date']
```

#### Service Layer (`services.py`)

```python
class OnboardingService:
    """Gere toutes les transitions du parcours d'adhesion."""

    @staticmethod
    def register_new_member(user, first_name, last_name, email):
        """Etape 1: Inscription -> genere QR + demarre countdown 30j."""
        member = Member.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            email=email,
            membership_status=MembershipStatus.REGISTERED,
            form_deadline=timezone.now() + timedelta(days=30),
        )
        QRCode.objects.create(member=member)  # Genere QR unique
        # Envoyer notification bienvenue
        return member

    @staticmethod
    def submit_form(member, form_data):
        """Etape 2: Formulaire soumis -> notifie admin."""
        member.membership_status = MembershipStatus.FORM_SUBMITTED
        member.form_submitted_at = timezone.now()
        # Sauvegarder les donnees du formulaire
        member.save()
        # Notifier tous les admins
        notify_admins_new_form(member)

    @staticmethod
    def admin_approve(member, admin, course):
        """Etape 3: Admin approuve -> assigne parcours."""
        member.membership_status = MembershipStatus.IN_TRAINING
        member.admin_reviewed_at = timezone.now()
        member.admin_reviewed_by = admin
        member.save()
        # Creer le MemberTraining avec les lecons planifiees
        training = create_training_for_member(member, course)
        return training

    @staticmethod
    def admin_reject(member, admin, reason):
        """Admin refuse le dossier."""
        member.membership_status = MembershipStatus.REJECTED
        member.admin_reviewed_at = timezone.now()
        member.admin_reviewed_by = admin
        member.rejection_reason = reason
        member.save()

    @staticmethod
    def mark_lesson_attended(scheduled_lesson, marked_by):
        """Marquer une lecon comme completee via scan QR."""
        scheduled_lesson.status = LessonStatus.COMPLETED
        scheduled_lesson.attended_at = timezone.now()
        scheduled_lesson.marked_by = marked_by
        scheduled_lesson.save()
        # Verifier si toutes les lecons sont completees
        training = scheduled_lesson.training
        if training.progress_percentage == 100:
            training.is_completed = True
            training.completed_at = timezone.now()
            training.save()
            # Notifier admin pour planifier interview
            notify_admin_training_complete(training)

    @staticmethod
    def schedule_interview(member, training, interviewer, date, location):
        """Planifier l'interview finale."""
        member.membership_status = MembershipStatus.INTERVIEW_SCHEDULED
        member.save()
        return Interview.objects.create(
            member=member,
            training=training,
            interviewer=interviewer,
            proposed_date=date,
            location=location,
        )

    @staticmethod
    def complete_interview(interview, passed, notes=''):
        """Finaliser l'interview."""
        interview.completed_at = timezone.now()
        interview.result_notes = notes
        member = interview.member

        if passed:
            interview.status = InterviewStatus.COMPLETED_PASS
            member.membership_status = MembershipStatus.ACTIVE
            member.became_active_at = timezone.now()
            member.role = Roles.MEMBER  # Confirme le role
            # Notifier le membre
            notify_member_welcome(member)
        else:
            interview.status = InterviewStatus.COMPLETED_FAIL
            member.membership_status = MembershipStatus.REJECTED
            member.rejection_reason = notes

        interview.save()
        member.save()

    @staticmethod
    def expire_overdue_members():
        """Tache Celery: supprime les comptes avec formulaire expire."""
        expired = Member.objects.filter(
            membership_status__in=[
                MembershipStatus.REGISTERED,
                MembershipStatus.FORM_PENDING
            ],
            form_deadline__lt=timezone.now()
        )
        count = expired.count()
        expired.update(membership_status=MembershipStatus.EXPIRED)
        # Optionnel: soft delete ou suppression
        return count
```

#### Taches Celery (`tasks.py`)

```python
@shared_task
def check_expired_forms():
    """Tourne chaque jour - expire les comptes sans formulaire."""
    count = OnboardingService.expire_overdue_members()
    logger.info(f"{count} comptes expires")

@shared_task
def send_lesson_reminders():
    """Tourne chaque jour - envoie rappels 3j, 1j, jour meme."""
    today = timezone.now().date()

    # Rappels J-3
    lessons_3d = ScheduledLesson.objects.filter(
        scheduled_date__date=today + timedelta(days=3),
        status=LessonStatus.UPCOMING,
        reminder_3days_sent=False
    )
    for lesson in lessons_3d:
        send_lesson_reminder(lesson, '3_days')
        lesson.reminder_3days_sent = True
        lesson.save()

    # Rappels J-1
    lessons_1d = ScheduledLesson.objects.filter(
        scheduled_date__date=today + timedelta(days=1),
        status=LessonStatus.UPCOMING,
        reminder_1day_sent=False
    )
    for lesson in lessons_1d:
        send_lesson_reminder(lesson, '1_day')
        lesson.reminder_1day_sent = True
        lesson.save()

    # Rappels jour meme
    lessons_today = ScheduledLesson.objects.filter(
        scheduled_date__date=today,
        status=LessonStatus.UPCOMING,
        reminder_sameday_sent=False
    )
    for lesson in lessons_today:
        send_lesson_reminder(lesson, 'same_day')
        lesson.reminder_sameday_sent = True
        lesson.save()

@shared_task
def send_interview_reminders():
    """Rappels pour les interviews a venir."""
    # Meme logique que les lecons

@shared_task
def send_form_deadline_reminders():
    """Rappels pour les deadlines de formulaire."""
    # Rappel a 7 jours, 3 jours, 1 jour
```

---

## SPRINT 2 : Systeme de presences QR (Semaine 3-4)

### 2.1 Nouvelle app : `apps/attendance/`

#### Structure

```
apps/attendance/
  __init__.py
  admin.py
  apps.py
  models.py
  serializers.py
  services.py
  tasks.py            # Alertes absence
  urls.py
  views_api.py
  views_frontend.py
  qr_utils.py         # Generation et validation QR
  tests/
    ...
  migrations/
```

#### Modeles

```python
class MemberQRCode(BaseModel):
    """QR code unique et rotatif par membre."""
    member = models.OneToOneField(Member, related_name='qr_code')
    code = models.CharField(max_length=100, unique=True, db_index=True)
    # Le code change periodiquement pour empecher le partage
    generated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # Rotation chaque semaine
    qr_image = models.ImageField(
        upload_to='qrcodes/%Y/%m/',
        blank=True
    )

    def regenerate(self):
        """Genere un nouveau code et QR image."""
        self.code = generate_secure_qr_code()
        self.generated_at = timezone.now()
        self.expires_at = timezone.now() + timedelta(days=7)
        self.qr_image = generate_qr_image(self.code)
        self.save()

    @property
    def is_valid(self):
        return timezone.now() < self.expires_at


class AttendanceSession(BaseModel):
    """Session de check-in (un culte, un evenement, une lecon)."""
    name = models.CharField(max_length=200)       # "Culte du 15 mars"
    session_type = models.CharField(max_length=30, choices=[
        ('worship', 'Culte'),
        ('event', 'Evenement'),
        ('lesson', 'Lecon de formation'),
        ('other', 'Autre'),
    ])
    event = models.ForeignKey(
        'events.Event', null=True, blank=True,
        related_name='attendance_sessions'
    )
    scheduled_lesson = models.ForeignKey(
        'onboarding.ScheduledLesson', null=True, blank=True,
        related_name='attendance_session'
    )
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    opened_by = models.ForeignKey(Member, related_name='opened_sessions')
    is_open = models.BooleanField(default=True)  # Check-in accepte?

    class Meta:
        ordering = ['-date', '-start_time']


class AttendanceRecord(BaseModel):
    """Enregistrement de presence d'un membre."""
    session = models.ForeignKey(
        AttendanceSession,
        related_name='records'
    )
    member = models.ForeignKey(Member, related_name='attendance_records')
    checked_in_at = models.DateTimeField(auto_now_add=True)
    checked_in_by = models.ForeignKey(
        Member, null=True, blank=True,
        related_name='scanned_records'
    )  # Qui a scanne (responsable)
    method = models.CharField(max_length=20, choices=[
        ('qr_scan', 'Scan QR'),
        ('manual', 'Manuel'),
    ], default='qr_scan')
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['session', 'member']  # Un check-in par session


class AbsenceAlert(BaseModel):
    """Alerte generee quand un membre manque plusieurs fois."""
    member = models.ForeignKey(Member, related_name='absence_alerts')
    consecutive_absences = models.PositiveIntegerField()
    last_attendance_date = models.DateField(null=True)
    alert_sent = models.BooleanField(default=False)
    alert_sent_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        Member, null=True, blank=True,
        related_name='acknowledged_alerts'
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-consecutive_absences']
```

#### Service QR (`qr_utils.py`)

```python
import qrcode
import uuid
import hmac
import hashlib
from io import BytesIO
from django.core.files.base import ContentFile

def generate_secure_qr_code():
    """Genere un code unique et non-devinable."""
    unique = str(uuid.uuid4())
    secret = settings.SECRET_KEY
    signature = hmac.new(
        secret.encode(),
        unique.encode(),
        hashlib.sha256
    ).hexdigest()[:16]
    return f"EC-{unique[:8]}-{signature}"

def generate_qr_image(code):
    """Genere l'image QR a partir du code."""
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(code)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return ContentFile(buffer.getvalue(), name=f'qr_{code[:8]}.png')

def validate_qr_code(code):
    """Valide un code QR scanne."""
    try:
        qr = MemberQRCode.objects.get(code=code)
        if not qr.is_valid:
            return None, "QR code expire"
        return qr.member, None
    except MemberQRCode.DoesNotExist:
        return None, "QR code invalide"
```

#### Check-in Flow (Admin)

```python
# Vue pour le scanner admin (tablette a l'entree)
class CheckInScannerView(AdminRequiredMixin, TemplateView):
    """Page scanner QR pour les responsables."""
    template_name = 'attendance/scanner.html'

    # Le template utilise la camera du telephone/tablette
    # pour lire les QR codes via JavaScript (html5-qrcode lib)

class CheckInAPIView(APIView):
    """API appelee quand un QR est scanne."""
    permission_classes = [IsAuthenticated, IsPastorOrAdmin]

    def post(self, request):
        code = request.data.get('qr_code')
        session_id = request.data.get('session_id')

        member, error = validate_qr_code(code)
        if error:
            return Response({'error': error}, status=400)

        session = AttendanceSession.objects.get(id=session_id)
        record, created = AttendanceRecord.objects.get_or_create(
            session=session,
            member=member,
            defaults={
                'checked_in_by': request.user.member_profile,
                'method': 'qr_scan'
            }
        )

        if not created:
            return Response({'warning': 'Deja enregistre'})

        # Si c'est une lecon de formation, marquer la presence
        if session.scheduled_lesson:
            OnboardingService.mark_lesson_attended(
                session.scheduled_lesson,
                request.user.member_profile
            )

        return Response({
            'success': True,
            'member_name': member.full_name,
            'member_photo': member.photo.url if member.photo else None,
        })
```

---

## SPRINT 3 : Authentification 2FA (Semaine 5)

### 3.1 Configuration

```python
# config/settings/base.py - Ajouts

INSTALLED_APPS += [
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
    'two_factor',
    'two_factor.plugins.phonenumber',  # SMS optionnel
]

MIDDLEWARE += [
    'django_otp.middleware.OTPMiddleware',
]

# Forcer 2FA dans les 30 premiers jours
TWO_FACTOR_PATCH_ADMIN = True
TWO_FACTOR_CALL_GATEWAY = None  # Pas d'appel tel
TWO_FACTOR_SMS_GATEWAY = None   # Configurer Twilio si SMS voulu
LOGIN_URL = 'two_factor:login'
```

### 3.2 Modele Audit Log

```python
class LoginAudit(BaseModel):
    """Journal de toutes les connexions."""
    user = models.ForeignKey(User, related_name='login_audits')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=True)
    failure_reason = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]
```

### 3.3 Middleware 2FA Enforcement

```python
class TwoFactorEnforcementMiddleware:
    """Force l'activation du 2FA dans les 30 premiers jours."""

    def __call__(self, request):
        if request.user.is_authenticated:
            member = getattr(request.user, 'member_profile', None)
            if member and not member.two_factor_enabled:
                if member.two_factor_deadline and timezone.now() > member.two_factor_deadline:
                    # Bloquer l'acces - rediriger vers la page 2FA
                    if request.path not in ALLOWED_PATHS_WITHOUT_2FA:
                        return redirect('two_factor:setup')
        return self.get_response(request)
```

---

## SPRINT 4 : Dons en ligne Stripe (Semaine 6-7)

### 4.1 Nouvelle app : `apps/payments/`

#### Modeles

```python
class StripeCustomer(BaseModel):
    """Lien entre un membre et son compte Stripe."""
    member = models.OneToOneField(Member, related_name='stripe_customer')
    stripe_customer_id = models.CharField(max_length=100, unique=True)


class OnlinePayment(BaseModel):
    """Paiement en ligne via Stripe."""
    member = models.ForeignKey(Member, related_name='online_payments')
    donation = models.OneToOneField(
        'donations.Donation',
        related_name='online_payment',
        null=True
    )
    stripe_payment_intent_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='CAD')
    status = models.CharField(max_length=30, choices=[
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('succeeded', 'Reussi'),
        ('failed', 'Echoue'),
        ('refunded', 'Rembourse'),
    ])
    donation_type = models.CharField(
        max_length=20,
        choices=DonationType.CHOICES,
        default=DonationType.OFFERING
    )
    campaign = models.ForeignKey(
        'donations.DonationCampaign',
        null=True, blank=True,
        related_name='online_payments'
    )

    class Meta:
        ordering = ['-created_at']


class RecurringDonation(BaseModel):
    """Don recurrent mensuel via Stripe Subscription."""
    member = models.ForeignKey(Member, related_name='recurring_donations')
    stripe_subscription_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    frequency = models.CharField(max_length=20, choices=[
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuel'),
    ], default='monthly')
    donation_type = models.CharField(
        max_length=20, choices=DonationType.CHOICES
    )
    next_payment_date = models.DateField(null=True)
    is_active_subscription = models.BooleanField(default=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
```

#### Vues

```python
class DonationPageView(LoginRequiredMixin, TemplateView):
    """Page de don integree (accessible aux membres actifs)."""
    template_name = 'payments/donate.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stripe_public_key'] = settings.STRIPE_PUBLIC_KEY
        context['campaigns'] = DonationCampaign.objects.filter(
            is_active=True
        )
        return context

class CreatePaymentIntentAPI(APIView):
    """Cree un PaymentIntent Stripe."""
    def post(self, request):
        amount = int(Decimal(request.data['amount']) * 100)  # En cents
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='cad',
            customer=get_or_create_stripe_customer(request.user.member_profile),
            metadata={
                'member_id': str(request.user.member_profile.id),
                'donation_type': request.data.get('donation_type', 'offering'),
            }
        )
        return Response({'client_secret': intent.client_secret})

class StripeWebhookView(View):
    """Recoit les webhooks Stripe (paiement reussi, etc.)."""
    # Cree automatiquement le Donation dans l'app donations existante
```

---

## SPRINT 5 : PWA (Semaine 8)

### 5.1 Configuration

```python
# config/settings/base.py
INSTALLED_APPS += ['pwa']

PWA_APP_NAME = 'EgliseConnect'
PWA_APP_DESCRIPTION = "Gestion d'eglise"
PWA_APP_THEME_COLOR = '#1a73e8'
PWA_APP_BACKGROUND_COLOR = '#ffffff'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_SCOPE = '/'
PWA_APP_ORIENTATION = 'any'
PWA_APP_START_URL = '/'
PWA_APP_STATUS_BAR_COLOR = 'default'
PWA_APP_ICONS = [
    {'src': '/static/w3crm/images/icon-192.png', 'sizes': '192x192'},
    {'src': '/static/w3crm/images/icon-512.png', 'sizes': '512x512'},
]
PWA_APP_DIR = 'ltr'
PWA_APP_LANG = 'fr-CA'
```

### 5.2 Service Worker

```javascript
// static/js/service-worker.js
const CACHE_NAME = 'egliseconnect-v1';
const OFFLINE_URLS = [
    '/',
    '/static/w3crm/css/style.css',
    '/static/w3crm/js/custom.min.js',
    '/offline/',  // Page hors-ligne
];

// Cache les pages visitees
self.addEventListener('fetch', (event) => {
    if (event.request.method === 'GET') {
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, clone);
                    });
                    return response;
                })
                .catch(() => caches.match(event.request))
        );
    }
});

// Notifications push
self.addEventListener('push', (event) => {
    const data = event.data.json();
    self.registration.showNotification(data.title, {
        body: data.body,
        icon: '/static/w3crm/images/icon-192.png',
        data: { url: data.url }
    });
});
```

---

## SPRINT 6 : Dashboard conditionnel (Semaine 9-10)

### 6.1 Middleware de restriction d'acces

```python
class MembershipAccessMiddleware:
    """Restreint l'acces selon le membership_status."""

    # Pages toujours accessibles (quelque soit le statut)
    ALWAYS_ALLOWED = [
        '/accounts/',        # Login/logout
        '/onboarding/',      # Tout le flux onboarding
        '/attendance/my-qr/', # Son QR code
        '/api/',             # API (gere par ses propres permissions)
        '/static/',
        '/media/',
    ]

    # Pages accessibles seulement aux membres actifs
    MEMBERS_ONLY = [
        '/donations/',
        '/events/',
        '/volunteers/',
        '/communication/',
        '/help-requests/',
        '/members/',
        '/reports/',
    ]

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        member = getattr(request.user, 'member_profile', None)
        if not member:
            return self.get_response(request)

        path = request.path

        # Toujours autoriser
        if any(path.startswith(p) for p in self.ALWAYS_ALLOWED):
            return self.get_response(request)

        # Bloquer les non-membres actifs
        if not member.has_full_access:
            if any(path.startswith(p) for p in self.MEMBERS_ONLY):
                return redirect('frontend:onboarding:dashboard')

        return self.get_response(request)
```

### 6.2 Templates du dashboard par statut

```
templates/onboarding/
  dashboard.html            # Dashboard principal (routeur par statut)
  status_registered.html    # QR + lien formulaire + countdown
  status_form_pending.html  # Formulaire + countdown
  status_submitted.html     # "En attente de validation" + historique
  status_in_training.html   # Progression lecons + supports + dates
  status_interview.html     # Date confirmee + rappels
  status_active.html        # Redirection vers dashboard complet
  status_rejected.html      # Message de refus
  form_complete.html        # Le formulaire complet a remplir
  my_qr.html               # Page QR code du membre
  lesson_detail.html        # Detail d'une lecon + supports

templates/attendance/
  scanner.html              # Interface scanner QR (admin)
  session_list.html         # Liste des sessions de check-in
  session_detail.html       # Detail d'une session + presences
  member_history.html       # Historique presences d'un membre
  alerts.html               # Alertes absence

templates/admin_onboarding/
  pending_reviews.html      # Liste des formulaires a revoir
  member_review.html        # Detail d'un dossier a approuver
  assign_training.html      # Assigner un parcours
  training_management.html  # Gerer les parcours/lecons
  schedule_interview.html   # Planifier une interview
  onboarding_stats.html     # Stats par etape du pipeline

templates/payments/
  donate.html               # Page de don (Stripe Elements)
  donation_success.html     # Confirmation
  recurring_manage.html     # Gerer ses dons recurrents
  payment_history.html      # Historique paiements
```

### 6.3 Sidebar dynamique

Le sidebar existant dans `templates/elements/sidebar.html` sera modifie
pour afficher les menus selon le `membership_status` :

```
Si REGISTERED / FORM_PENDING :
  - Mon QR Code
  - Formulaire d'adhesion
  - Mon statut

Si FORM_SUBMITTED / IN_REVIEW :
  - Mon QR Code
  - Mon statut
  - Historique presences

Si IN_TRAINING :
  - Mon QR Code
  - Ma formation (progression)
  - Supports de cours
  - Calendrier lecons
  - Mon statut

Si INTERVIEW_SCHEDULED :
  - Mon QR Code
  - Mon interview
  - Ma formation (terminee)
  - Mon statut

Si ACTIVE :
  - Tableau de bord (complet)
  - Membres / Repertoire
  - Groupes
  - Evenements / Calendrier
  - Dons
  - Benevoles
  - Communications
  - Demandes d'aide
  - Rapports
  - Mon QR Code
  - Mon profil
```

---

## SPRINT 7 : Dashboard Admin onboarding (Semaine 11-12)

### 7.1 Vues admin

```python
# Pipeline visuel des candidats
class OnboardingPipelineView(AdminRequiredMixin, TemplateView):
    """Vue Kanban des membres par statut."""

    def get_context_data(self):
        return {
            'registered': Member.objects.filter(
                membership_status=MembershipStatus.REGISTERED
            ),
            'form_submitted': Member.objects.filter(
                membership_status=MembershipStatus.FORM_SUBMITTED
            ),
            'in_training': Member.objects.filter(
                membership_status=MembershipStatus.IN_TRAINING
            ),
            'interview': Member.objects.filter(
                membership_status=MembershipStatus.INTERVIEW_SCHEDULED
            ),
            'stats': {
                'total_in_process': Member.objects.filter(
                    membership_status__in=MembershipStatus.IN_PROCESS
                ).count(),
                'success_rate': calculate_success_rate(),
                'avg_completion_days': calculate_avg_days(),
                'critical_absences': AbsenceAlert.objects.filter(
                    alert_sent=False
                ).count(),
            }
        }
```

---

## URLS FINALES

### Nouvelles URLs frontend

```python
# Onboarding
/onboarding/                        # Dashboard conditionnel
/onboarding/form/                   # Formulaire complet
/onboarding/my-qr/                  # Mon QR code
/onboarding/training/               # Ma progression
/onboarding/training/<id>/lesson/<id>/  # Detail lecon + supports
/onboarding/interview/              # Mon interview
/onboarding/status/                 # Mon statut actuel

# Admin Onboarding
/onboarding/admin/pipeline/         # Vue pipeline candidats
/onboarding/admin/reviews/          # Formulaires a revoir
/onboarding/admin/review/<id>/      # Detail d'un dossier
/onboarding/admin/courses/          # Gerer les parcours
/onboarding/admin/courses/<id>/     # Detail parcours + lecons
/onboarding/admin/interviews/       # Liste interviews
/onboarding/admin/stats/            # Statistiques onboarding

# Attendance
/attendance/scanner/                # Scanner QR (admin)
/attendance/sessions/               # Liste sessions
/attendance/sessions/create/        # Nouvelle session check-in
/attendance/sessions/<id>/          # Detail + presences
/attendance/member/<id>/            # Historique d'un membre
/attendance/alerts/                 # Alertes absence
/attendance/my-history/             # Mon historique (membre)

# Payments
/payments/donate/                   # Page de don
/payments/success/                  # Confirmation
/payments/recurring/                # Mes dons recurrents
/payments/history/                  # Historique paiements
/payments/webhook/                  # Stripe webhook (pas de login)
```

### Nouvelles URLs API

```python
/api/v1/onboarding/status/              # GET mon statut
/api/v1/onboarding/form/                # POST soumettre formulaire
/api/v1/onboarding/training/            # GET ma formation
/api/v1/onboarding/interview/           # GET/PUT mon interview
/api/v1/onboarding/admin/reviews/       # GET formulaires a revoir
/api/v1/onboarding/admin/approve/<id>/  # POST approuver
/api/v1/onboarding/admin/reject/<id>/   # POST refuser

/api/v1/attendance/checkin/             # POST scanner QR
/api/v1/attendance/sessions/            # CRUD sessions
/api/v1/attendance/my-history/          # GET mon historique
/api/v1/attendance/alerts/              # GET alertes

/api/v1/payments/create-intent/         # POST creer paiement
/api/v1/payments/recurring/             # CRUD dons recurrents
/api/v1/payments/history/               # GET historique
```

---

## MODELES - RESUME COMPLET

### Nouveaux modeles (14 modeles)

| App | Modele | Description |
|-----|--------|-------------|
| onboarding | TrainingCourse | Modele de parcours de formation |
| onboarding | Lesson | Lecon individuelle avec supports |
| onboarding | MemberTraining | Assignation parcours -> membre |
| onboarding | ScheduledLesson | Lecon planifiee avec date/heure |
| onboarding | Interview | Interview finale + planification |
| attendance | MemberQRCode | QR code unique rotatif |
| attendance | AttendanceSession | Session de check-in |
| attendance | AttendanceRecord | Enregistrement de presence |
| attendance | AbsenceAlert | Alerte d'absence consecutive |
| payments | StripeCustomer | Lien membre <-> Stripe |
| payments | OnlinePayment | Paiement unique en ligne |
| payments | RecurringDonation | Don recurrent (subscription) |
| core | LoginAudit | Journal des connexions |

### Modeles modifies (1 modele)

| App | Modele | Changements |
|-----|--------|-------------|
| members | Member | +8 champs onboarding, +2 champs 2FA |

---

## FICHIERS A MODIFIER

### Fichiers existants a modifier

```
config/settings/base.py          # Nouvelles apps, middleware, config
config/urls.py                   # Nouvelles URLs
apps/core/constants.py           # Nouveaux enums
apps/members/models.py           # Nouveaux champs Member
apps/members/serializers.py      # Nouveaux champs API
apps/members/forms.py            # Nouveau formulaire onboarding
templates/elements/sidebar.html  # Menu dynamique par statut
templates/base.html              # PWA manifest, service worker
templates/registration/login.html # 2FA integration
requirements.txt                 # Nouvelles dependances
```

### Nouveaux fichiers a creer

```
apps/onboarding/     (14 fichiers)  # Nouvelle app complete
apps/attendance/     (14 fichiers)  # Nouvelle app complete
apps/payments/       (14 fichiers)  # Nouvelle app complete
templates/onboarding/  (10 templates)
templates/attendance/  (5 templates)
templates/admin_onboarding/ (6 templates)
templates/payments/    (4 templates)
static/js/service-worker.js
static/js/qr-scanner.js
```

**Total estime : ~80 nouveaux fichiers, ~12 fichiers modifies**

---

## FLUX COMPLET UTILISATEUR

```
INSCRIPTION
    |
    v
[1] Cree compte (email/mdp)
    → Statut: REGISTERED
    → Recoit QR code unique
    → Countdown 30 jours demarre
    → Dashboard: QR + formulaire + countdown
    |
    v
[2] Remplit formulaire complet (dans les 30j)
    → Statut: FORM_SUBMITTED
    → Admin notifie
    → Dashboard: "En attente de validation"
    |                              |
    | (Si 30j depasses)           |
    v                              v
[EXPIRED]                    [3] Admin revise
Compte desactive                  |
                         --------+---------
                         |                 |
                         v                 v
                    [REJECTED]       [4] APPROVED
                    Compte refuse    Admin assigne parcours
                                         |
                                         v
                                    [5] IN_TRAINING
                                    Lecons planifiees avec dates
                                    Le membre:
                                      - Voit progression
                                      - Telecharge supports
                                      - Recoit rappels J-3, J-1, J
                                      - DOIT etre present (scan QR)
                                         |
                                         v
                                    [6] 100% lecons completees
                                    Admin notifie
                                         |
                                         v
                                    [7] INTERVIEW_SCHEDULED
                                    Admin propose date
                                    Membre confirme ou propose autre
                                    Date finale = DEFINITIVE
                                         |
                                    -----+------
                                    |          |
                                    v          v
                              [NO_SHOW]   [8] Interview
                              Refuse       Reussie?
                              definitif      |
                                        -----+------
                                        |          |
                                        v          v
                                  [REJECTED]   [ACTIVE]
                                  Refuse       MEMBRE OFFICIEL!
                                               Dashboard complet
                                               Acces a TOUT
```

---

## ORDRE D'IMPLEMENTATION RECOMMANDE

```
Sprint 1 (Sem 1-2)  : Constants + Member status + Onboarding models
Sprint 2 (Sem 3-4)  : Attendance app + QR system
Sprint 3 (Sem 5)    : 2FA + Login audit
Sprint 4 (Sem 6-7)  : Payments/Stripe
Sprint 5 (Sem 8)    : PWA setup
Sprint 6 (Sem 9-10) : Dashboard conditionnel + templates
Sprint 7 (Sem 11-12): Admin dashboard + stats + polish
Sprint 8 (Sem 13)   : Tests (objectif 95%+) + bug fixes
```

### Prototype rapide (MVP - 1 sprint)

Pour valider le flux complet avec 1 parcours test de 3 lecons :

```
1. Ajouter MembershipStatus + champs dans Member
2. Creer app onboarding avec modeles de base
3. Creer app attendance avec QR simple
4. Page formulaire onboarding
5. Page admin review
6. Page progression lecons
7. Scanner QR basique
8. Tache Celery expiration 30j
```

Ceci permet de tester le flux ENTIER de bout en bout avant
d'ajouter 2FA, Stripe, PWA.
