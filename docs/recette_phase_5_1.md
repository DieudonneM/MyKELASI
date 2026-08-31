# Recette Phase 5.1

Date : 31 aout 2026

## Commande executee

```powershell
& .\.venv\Scripts\python.exe -m pytest app_core/tests/test_integrated_journeys.py -q --no-cov
```

Resultat : `3 passed`.

## Jeux de donnees et preuves

- Chaque test cree ses propres utilisateurs, referentiels issus des migrations de test et objets metier; aucune donnee persistante ou fixture externe n'est requise.
- Le parcours Apprenant couvre inscription API, verification email, profil, recherche, matching, proposition, deux reservations, paiement webhook, session terminee et avis.
- Le parcours Formateur couvre inscription API, verification email, profil, publication, document prive, decision de verification, matching, proposition, session, revenus et avis recus.
- Le parcours Admin couvre MFA, verification, moderation, paiement, rapprochement finance, referentiel, KPI filtres et journaux d'audit.
- Les assertions et les donnees de recette sont archivees dans `app_core/tests/test_integrated_journeys.py`. Les captures ne sont pas applicables : il s'agit de recettes API/services sans interface graphique.

## Controles associes

```powershell
& .\.venv\Scripts\ruff.exe format app_core/tests/test_integrated_journeys.py
& .\.venv\Scripts\ruff.exe check app_core/tests/test_integrated_journeys.py
& .\.venv\Scripts\python.exe manage.py check
```

Resultats : Ruff sans erreur et `System check identified no issues (0 silenced)`.