# Recette Phase 5.2

Date : 31 aout 2026

## Commande executee

```powershell
& .\.venv\Scripts\python.exe -m pytest app_core/tests/test_negative_journeys.py -q --no-cov
```

Resultat : `6 passed`.

## Cas verifies

- Un apprenant non verifie ne peut pas creer de demande : `403`.
- Un apprenant suspendu ou desactive ne peut pas creer de demande : `403`.
- Un formateur ne peut pas creer de demande Apprenant : `403`.
- Un apprenant ne peut ni lire la demande d'un tiers : `404`, ni modifier sa proposition : `403`.
- Un membre de l'equipe SUPPORT ne peut pas lire la file VERIFICATION : `403`.

Le garde-fou `IsActiveVerifiedUser` est applique aux demandes : il exige une session authentifiee, un compte actif, le statut `ACTIVE` et une adresse email verifiee.

## Controles associes

```powershell
& .\.venv\Scripts\ruff.exe format accounts/permissions.py learning/api_views.py app_core/tests/test_negative_journeys.py
& .\.venv\Scripts\ruff.exe check accounts/permissions.py learning/api_views.py app_core/tests/test_negative_journeys.py
& .\.venv\Scripts\python.exe manage.py check
```

Resultats : Ruff sans erreur et `System check identified no issues (0 silenced)`.