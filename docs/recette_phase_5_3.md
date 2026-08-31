# Recette Phase 5.3

Date : 31 aout 2026

## Commandes executees

```powershell
& .\.venv\Scripts\python.exe -m pytest learning/tests/test_matching.py bookings/tests/test_bookings.py payments/tests/test_payments.py reviews/tests/test_reviews.py -q --no-cov
```

Resultat : `45 passed`.

## Cas verifies

- L'acceptation, le refus et le retrait de proposition sont idempotents; le retrait est desormais une transition API reservee au formateur proprietaire.
- Deux reservations qui se chevauchent pour le meme formateur sont refusees. Le service verrouille la proposition et le formateur dans une transaction avant le controle de conflit.
- La meme cle d'idempotence retourne le meme paiement sans creer de doublon.
- Un webhook a signature invalide, montant falsifie, devise falsifiee ou rejoue est refuse ou traite sans nouvel effet.
- La presence avant le debut, la cloture avant la fin et une seconde cloture sont refusees; la contrainte de base empeche aussi une fin reelle avant le debut reel.
- Un avis avant session terminee, par un tiers ou en doublon est refuse.

## Controles associes

```powershell
& .\.venv\Scripts\ruff.exe format learning/services.py learning/api_views.py learning/tests/test_matching.py bookings/tests/test_bookings.py payments/tests/test_payments.py
& .\.venv\Scripts\ruff.exe check learning/services.py learning/api_views.py learning/tests/test_matching.py bookings/tests/test_bookings.py payments/tests/test_payments.py
```

Resultat : Ruff sans erreur.