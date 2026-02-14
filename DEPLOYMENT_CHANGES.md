# CHMS (egliseconnect) - Deployment Changes

All changes made to get the application running in production on `chms.jhpetitfrere.com`.

---

## requirements.txt
- Added `psycopg2-binary>=2.9` — PostgreSQL database driver was missing, causing `ImproperlyConfigured: Error loading psycopg2 or psycopg module` on startup
- Added `gunicorn>=21.0` — WSGI server was missing from requirements, needed to run the application in production
