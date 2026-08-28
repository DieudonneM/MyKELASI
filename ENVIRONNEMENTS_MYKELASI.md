# Environnements MyKELASI

Les configurations Django sont sélectionnées avec `DJANGO_ENV` :

| Environnement | Configuration | DEBUG | Usage |
| --- | --- | --- | --- |
| `development` | `app_core.settings.development` | configurable | développement local |
| `test` | `app_core.settings.test` | `False` | tests automatisés, SQLite mémoire |
| `staging` | `app_core.settings.staging` | `False` | recette préproduction |
| `production` | `app_core.settings.production` | `False` | production |

## Variables obligatoires

Copier `.env.example` vers `.env`, puis remplacer toutes les valeurs d'exemple :

- `DJANGO_SECRET_KEY`
- `DJANGO_ENV`
- `DJANGO_DEBUG` uniquement en développement
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`
- `EMAIL_BACKEND`, `DEFAULT_FROM_EMAIL` et les variables SMTP si l'envoi SMTP est activé
- `PAYMENT_PROVIDER`, `PAYMENT_WEBHOOK_SECRET` et `PAYMENT_COMMISSION_RATE`

Les secrets doivent être injectés par l'environnement de déploiement et ne doivent jamais être commités.

## Commandes

Depuis `Web_MyKELASI` :

```powershell
# Développement local
$env:DJANGO_ENV = "development"
python manage.py runserver

# Vérification de la configuration staging
$env:DJANGO_ENV = "staging"
python manage.py validate_environment
python manage.py check
python manage.py migrate --noinput

# Tests
$env:DJANGO_ENV = "test"
python manage.py check
python -m pytest

# Production
$env:DJANGO_ENV = "production"
python manage.py validate_environment
python manage.py check --deploy
python manage.py migrate --noinput
```

En staging et production, fournir une base PostgreSQL, un domaine HTTPS, les hôtes autorisés, les origines CSRF et les paramètres email/paiement correspondant à l'environnement.

## Sécurité de déploiement

Staging et production imposent HTTPS : `SECURE_SSL_REDIRECT`, les cookies de session et CSRF sécurisés, et HSTS sont activés par la configuration. `DJANGO_SECURE_HSTS_SECONDS` vaut un an par défaut et doit être strictement positif.

La seule exception admise est le développement local, qui peut utiliser HTTP afin de servir `127.0.0.1` et `localhost`. Aucune exception HTTPS ou HSTS n'est admise en staging ou production sans une décision de sécurité documentée avant livraison.

## Médias sensibles

Les pièces d'identité, certifications et fragments d'upload sont stockés dans `DJANGO_PRIVATE_MEDIA_ROOT`, hors de `MEDIA_ROOT` et de toute URL publique. La valeur par défaut est le répertoire frère `mykelasi-private-media`; staging et production doivent fournir un volume privé dédié, non servi par le proxy HTTP.

Le téléchargement passe uniquement par la route authentifiée de vérification, contrôle l'objet et le statut du compte, ne sert pas les documents expirés et répond avec `Cache-Control: private, no-store`. Les réponses API ne contiennent ni URL ni chemin de document.

La désactivation d'un compte purge immédiatement ses documents et fragments privés. Les autres données personnelles sont anonymisées ou supprimées après les délais légaux, tandis que les journaux financiers et d'audit requis sont conservés sous forme minimisée. Les sauvegardes chiffrées et leur restauration sur une installation isolée restent une procédure d'exploitation à exécuter avant livraison : conserver la preuve de restauration, sans inclure de document ou de secret dans les logs.