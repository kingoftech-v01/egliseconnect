# Guide de Deploiement - EgliseConnect (CHMS)

Ce guide couvre le deploiement de l'application EgliseConnect avec Docker sur un serveur de production.

## Prerequis

- Serveur Linux (Ubuntu 20.04+ recommande)
- Docker et Docker Compose installes
- Domaine pointe vers le serveur (ex: `chms.votredomaine.com`)
- Nginx installe sur l'hote pour la terminaison SSL
- Certbot pour les certificats SSL

## Deploiement Rapide

```bash
# 1. Cloner le depot
git clone <repo-url>
cd egliseconnect

# 2. Creer le fichier d'environnement
cp .env.example .env
# Modifier .env avec vos parametres (voir Variables d'Environnement ci-dessous)

# 3. Construire et demarrer les conteneurs
docker compose build
docker compose up -d

# 4. Verifier le statut des conteneurs
docker ps
```

Le script d'entree gere automatiquement:
- Attendre que la base de donnees soit prete
- Executer les migrations
- Collecter les fichiers statiques

## Variables d'Environnement

Creer un fichier `.env` avec ces variables requises:

```env
# Parametres Django
SECRET_KEY=votre-cle-secrete-ici
DEBUG=False
ALLOWED_HOSTS=chms.votredomaine.com,localhost

# Base de donnees
POSTGRES_DB=chms_production
POSTGRES_USER=chms_user
POSTGRES_PASSWORD=mot-de-passe-securise
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# Email (optionnel - console par defaut)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
# Pour SMTP:
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_HOST_USER=votre-email
# EMAIL_HOST_PASSWORD=votre-mot-de-passe-app

# Verification email (optionnel pour eviter les erreurs 500)
ACCOUNT_EMAIL_VERIFICATION=optional

# Securite
CSRF_TRUSTED_ORIGINS=https://chms.votredomaine.com
SECURE_SSL_REDIRECT=True
```

## Configuration Nginx (Hote)

Creer `/etc/nginx/sites-available/chms.votredomaine.com`:

```nginx
# Redirection HTTP vers HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name chms.votredomaine.com;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# Serveur HTTPS
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name chms.votredomaine.com;

    # Certificats SSL
    ssl_certificate /etc/letsencrypt/live/chms.votredomaine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/chms.votredomaine.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # En-tetes de securite
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=63072000" always;

    client_max_body_size 100M;

    # Proxy vers le conteneur Docker
    location / {
        proxy_pass http://127.0.0.1:8082;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 90;
    }
}
```

Activer le site et obtenir le certificat SSL:

```bash
# Activer le site
sudo ln -s /etc/nginx/sites-available/chms.votredomaine.com /etc/nginx/sites-enabled/

# Tester la config nginx
sudo nginx -t

# Obtenir le certificat SSL
sudo certbot certonly --webroot -w /var/www/html -d chms.votredomaine.com

# Recharger nginx
sudo systemctl reload nginx
```

## Ports des Conteneurs Docker

| Service | Port Interne | Port Externe |
|---------|--------------|--------------|
| web     | 8000         | -            |
| nginx   | 80           | 8082         |
| db      | 5432         | -            |
| redis   | 6379         | -            |

## Commandes Courantes

```bash
# Voir les logs
docker compose logs -f web

# Redemarrer les conteneurs
docker compose restart

# Reconstruire apres des changements de code
docker compose build web
docker compose up -d web

# Executer des commandes Django
docker compose exec web python manage.py <commande>

# Creer un superutilisateur
docker compose exec web python manage.py createsuperuser

# Acceder au shell Django
docker compose exec web python manage.py shell

# Sauvegarde de la base de donnees
docker compose exec db pg_dump -U chms_user chms_production > backup.sql
```

## Depannage

### Le conteneur ne demarre pas
```bash
# Verifier les logs
docker compose logs web

# Verifier si les ports sont utilises
sudo lsof -i :8082
```

### Erreurs de connexion a la base de donnees
```bash
# Verifier que la base de donnees fonctionne
docker compose ps db

# Verifier les logs de la base de donnees
docker compose logs db
```

### Fichiers statiques non charges
```bash
# Collecter manuellement les fichiers statiques
docker compose exec web python manage.py collectstatic --noinput
```

### Erreurs CSRF
Assurez-vous que `CSRF_TRUSTED_ORIGINS` dans `.env` inclut votre domaine avec le prefixe `https://`.

### Erreur 500 a l'inscription
Verifiez que `EMAIL_BACKEND` et `ACCOUNT_EMAIL_VERIFICATION` sont configures dans `.env`.

## Mise a jour

```bash
# Recuperer le dernier code
git pull origin main

# Reconstruire et redemarrer
docker compose build
docker compose up -d

# Executer les nouvelles migrations (si necessaire)
docker compose exec web python manage.py migrate
```

## Configuration de l'Application

Apres le deploiement, accedez a l'interface d'administration:
- URL: `https://chms.votredomaine.com/admin/`
- Creez un superutilisateur si pas encore fait

Configurez l'eglise dans l'admin:
1. Aller dans "Church Configuration"
2. Ajouter les informations de l'eglise
3. Configurer les parametres de dons et recus fiscaux
