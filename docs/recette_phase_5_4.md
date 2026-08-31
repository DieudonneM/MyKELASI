# Recette Phase 5.4

Date : 31 aout 2026

## Commande executee

```powershell
& .\.venv\Scripts\python.exe -m pytest verification/tests/test_documents.py messaging/tests/test_messaging.py accounts/tests/test_logging.py -q --no-cov
```

Resultat : `25 passed`.

## Cas verifies

- Les documents trop volumineux, avec MIME incoherent ou signature PDF/JPEG/PNG invalide sont refuses.
- Les documents prives ne sont pas servis depuis `/media/`; leur consultation autorisee utilise `Cache-Control: private, no-store` et `X-Content-Type-Options: nosniff`.
- Les messages vides, trop longs, depassant le quota ou contenant une phrase interdite sont refuses.
- Un signalement ouvert identique est refuse; une cible de conversation inexistante retourne `404`.
- Les reponses ne publient ni document de verification ni URL `/media/`, les APIs de messagerie ne publient pas les numeros de telephone, et le filtre de logs masque les valeurs de mot de passe, token, autorisation et document. Le cache de messagerie est reserve aux quotas et identifiants, sans contenu ou document.

## Controles associes

```powershell
& .\.venv\Scripts\ruff.exe format accounts/logging.py app_core/settings/base.py verification/validators.py verification/tests/test_documents.py messaging/services.py messaging/tests/test_messaging.py accounts/tests/test_logging.py
& .\.venv\Scripts\ruff.exe check accounts/logging.py app_core/settings/base.py verification/validators.py verification/tests/test_documents.py messaging/services.py messaging/tests/test_messaging.py accounts/tests/test_logging.py
& .\.venv\Scripts\python.exe manage.py check
```

Resultats : Ruff sans erreur et `System check identified no issues (0 silenced)`.