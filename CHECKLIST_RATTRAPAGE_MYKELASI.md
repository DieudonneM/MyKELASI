# Checklist de rattrapage MyKELASI

Version : 1.0  
Date : 28 août 2026  
Référence : `CHECKLIST_LIVRAISON_MYKELASI.md` et audit du 28 août 2026

## Règles d'exécution

- [ ] Ne cocher une tâche qu'avec une preuve : test, capture, commande, contrat, migration ou recette.
- [ ] Respecter l'ordre des phases ; chaque phase débloque la suivante.
- [ ] Ne pas considérer une route ou un écran comme fonctionnel sans appel API et états loading/succès/vide/erreur/reprise.
- [ ] Pour chaque mutation, vérifier permission objet, double clic, rejeu et idempotence.
- [ ] Ne jamais remplacer les données serveur par des données métier simulées.

## État de référence

- [x] Suite Django verte lors de l'audit.
- [x] Suite Flutter verte : 132 tests lors de l'audit.
- [x] `flutter analyze` sans erreur lors de l'audit.
- [x] `manage.py check` sans erreur lors de l'audit.
- [ ] `manage.py check --deploy` sans avertissement.
- [ ] Parcours intégrés Web/API/Mobile exécutés et archivés.

---

# Phase 1 - Fondations et sécurité

## 1.1 Environnements Django

- [x] Ajouter `staging` dans `app_core/settings/__init__.py`.
- [x] Vérifier que `DJANGO_ENV=staging` charge la bonne configuration.
- [x] Vérifier `DEBUG=False` en staging et production.
- [x] Valider les variables obligatoires de chaque environnement avec `validate_environment`.
- [x] Documenter lancement, base, domaines, email et paiement par environnement.

## 1.2 Sécurité de déploiement

- [x] Configurer `SECURE_SSL_REDIRECT=True` lorsque HTTPS est obligatoire.
- [x] Définir et valider `SECURE_HSTS_SECONDS`.
- [x] Activer `SESSION_COOKIE_SECURE=True` en staging/production.
- [x] Activer `CSRF_COOKIE_SECURE=True` en staging/production.
- [x] Exécuter `python manage.py check --deploy` avec `DEBUG=False`.
- [x] Documenter toute exception de sécurité avant livraison.

## 1.3 Médias et données sensibles

- [x] Configurer le stockage privé des documents de vérification et certifications.
- [x] Empêcher l'exposition directe publique de `MEDIA_ROOT`.
- [x] Tester 403/404 pour tout document appartenant à un autre utilisateur.
- [x] Tester accès après expiration, suspension et suppression.
- [x] Vérifier absence de données sensibles dans logs, réponses, URLs et caches.
- [x] Définir rétention, anonymisation, suppression et sauvegarde chiffrée.
- [ ] Tester une restauration sur une installation isolée.

## 1.4 CI et qualité

- [x] Ajouter `manage.py check --deploy` à la CI.
- [x] Ajouter `ruff format --check` et `dart format --set-exit-if-changed`.
- [x] Publier les rapports de couverture Django et Flutter.
- [x] Exécuter explicitement les tests de permissions et de paiements.
- [x] Conserver `git diff --check` dans la CI.

**Preuve phase 1 :** configurations validées, CI verte et rapport sécurité.

---

# Phase 2 - Contrats API et administration backend

## 2.1 Documentation API

- [x] Produire un schéma OpenAPI versionné dans `docs/openapi.json`.
- [x] Documenter méthode, URL, authentification et permission des endpoints recensés.
- [x] Documenter payloads, champs obligatoires, enums et transitions recensés.
- [x] Documenter réponses 200, 201, 204, 400, 401, 403, 404, 409 et 429 utiles.
- [x] Documenter erreurs par champ, pagination, dates ISO 8601 et montants décimaux.
- [x] Servir le schéma versionné par `/api/v1/schema/` et le vérifier par test.

## 2.2 Référentiels administrables

- [x] Identifier modèles et endpoints des matières, niveaux, modes et zones.
- [x] Ajouter permissions par équipe et audit des changements.
- [x] Implémenter CRUD Web/API des référentiels.
- [x] Implémenter activation/désactivation sans supprimer les références utilisées.
- [x] Refuser une nouvelle mutation utilisant une référence inactive.
- [x] Préserver l'affichage historique des objets existants.
- [x] Versionner pondérations de matching, commission, devise et politiques.
- [x] Ajouter tests de permission, validation, concurrence et non-régression.

## 2.3 Permissions internes

- [x] Tester l'isolation entre support, vérification, finance, modération, admin et super-admin.
- [x] Limiter les champs visibles au besoin de chaque équipe.
- [x] Tester accès direct par identifiant hors périmètre.
- [x] Auditer consultations et mutations sensibles.
- [x] Tester suspension, désactivation et retrait de permission.

**Preuve phase 2 :** migrations, endpoints, documentation, tests et journal d'audit.

---

# Phase 3 - Flutter Formateur et fonctionnalités communes

Pour chaque écran : repository, DTO, controller/provider, appel API, états complets, navigation et tests.

## 3.1 Remplacer les placeholders

- [x] `proposal_received_screen.dart` : propositions réelles et actions serveur.
- [x] `chat_list_screen.dart` : conversations réelles, pagination et non-lu.
- [x] `requests_received_screen.dart` : demandes matchées réelles.
- [x] `identity_verification_screen.dart` : dépôt, statut et reprise de document.
- [x] `add_certifications_screen.dart` : dépôt et suivi des certifications.
- [x] `comparison_screen.dart` : comparaison alimentée par le serveur.

## 3.2 Paiement et historique Apprenant

- [x] Brancher paiement et historique aux controllers/providers réels.
- [x] Afficher montant, devise, statut, référence et reçu du serveur.
- [x] Couvrir initiation, attente, succès, échec, annulation et reprise.
- [x] Empêcher double soumission et réutilisation incorrecte d'une clé d'idempotence.
- [x] Ajouter tests widget, repository et erreurs financières.

## 3.3 Session et deep links

- [x] Faire passer la déconnexion Admin par le contrôleur de session.
- [x] Effacer tokens et données de session lors du logout.
- [x] Rendre `/teachers/:id` fonctionnel sans `state.extra`.
- [x] Rendre `/learner-bookings/:id` fonctionnel avec l'ID de l'URL.
- [x] Tester demande, proposition, réservation, paiement et notification depuis un lien externe.
- [x] Couvrir objet introuvable, non autorisé et session expirée.

## 3.4 Configuration Mobile

- [x] Documenter `API_BASE_URL` pour Android, iOS et Web.
- [x] Documenter les valeurs development, staging et production.
- [x] Vérifier l'absence de secrets dans `--dart-define` et le dépôt.
- [x] Valider la configuration au démarrage.
- [x] Produire des builds reproductibles des trois cibles.

**Preuve phase 3 :** tests repository/controller/widget, tests de routing et recette mobile.

---

# Phase 4 - Administration Flutter connectée

## 4.1 Socle Admin

- [x] Ajouter client API, repositories et controllers Admin.
- [x] Couvrir chargement, rafraîchissement, vide, erreur et reprise.
- [x] Gérer 401, 403, 404 et 409.
- [x] Tester les rôles internes côté Flutter et API.

## 4.2 Vérification

- [x] Remplacer la liste statique par les documents pending réels.
- [x] Ajouter consultation sécurisée et auditée.
- [x] Ajouter approuver, rejeter et expirer avec motif.
- [x] Ajouter nouveau dépôt après rejet/expiration et historique des décisions.

## 4.3 Modération et support

- [ ] Charger les signalements depuis l'API.
- [ ] Ajouter attribution, statut, priorité et historique.
- [ ] Ajouter masquer, restaurer, avertir, suspendre et clôturer.
- [ ] Ajouter accès temporaire et audité aux conversations signalées.
- [ ] Limiter les données affichées au périmètre support.

## 4.4 Finance, référentiels et analytics

- [ ] Charger paiements, remboursements, webhooks, ledger et versements réels.
- [ ] Ajouter rapprochement manuel, litiges et exports contrôlés/audités.
- [ ] Vérifier qu'une écriture ledger existante ne peut pas être modifiée silencieusement.
- [ ] Brancher Référentiels aux endpoints CRUD, activation et désactivation.
- [ ] Brancher Analytics aux KPI serveur avec filtres période, matière et zone.
- [ ] Vérifier que les KPI reposent sur les sessions réellement terminées.

**Preuve phase 4 :** tests widget/controller, permissions API et recette par équipe interne.

---

# Phase 5 - Parcours intégrés et tests négatifs

## 5.1 Parcours complets

- [x] Automatiser le parcours Apprenant : inscription, email, profil, recherche, demande, match, proposition, réservation, paiement, session, avis et réachat.
- [x] Automatiser le parcours Formateur : inscription, email, profil, vérification, publication, match, proposition, réservation, session, revenus et avis.
- [x] Automatiser le parcours Admin : MFA, vérification, modération, finance, référentiel, analytics et audit.
- [x] Exécuter ces parcours sur une base propre avec seed reproductible.
- [x] Archiver résultats, données de test et captures utiles.

**Preuve 5.1 :** [`app_core/tests/test_integrated_journeys.py`](app_core/tests/test_integrated_journeys.py) et [`docs/recette_phase_5_1.md`](docs/recette_phase_5_1.md), exécutés le 31 août 2026.

## 5.2 Authentification et permissions

- [x] Apprenant non vérifié sur action protégée.
- [x] Formateur sur action Apprenant.
- [x] Lecture/modification de l'objet d'un autre utilisateur.
- [x] Accès après suspension ou désactivation.
- [x] Équipe interne hors de son périmètre.

**Preuve 5.2 :** [`app_core/tests/test_negative_journeys.py`](app_core/tests/test_negative_journeys.py) et [`docs/recette_phase_5_2.md`](docs/recette_phase_5_2.md), executes le 31 aout 2026.

## 5.3 Transactions

- [x] Proposition acceptée, refusée ou retirée réutilisée.
- [x] Double réservation concurrente du même créneau.
- [x] Double paiement avec même clé d'idempotence.
- [x] Webhook invalide, montant/devise falsifiés ou webhook rejoué.
- [x] Session terminée deux fois, fin avant début ou action hors délai.
- [x] Avis avant session terminée ou en doublon.

**Preuve 5.3 :** [`learning/tests/test_matching.py`](learning/tests/test_matching.py), [`bookings/tests/test_bookings.py`](bookings/tests/test_bookings.py), [`payments/tests/test_payments.py`](payments/tests/test_payments.py), [`reviews/tests/test_reviews.py`](reviews/tests/test_reviews.py) et [`docs/recette_phase_5_3.md`](docs/recette_phase_5_3.md), executes le 31 aout 2026.

## 5.4 Fichiers et contenus

- [x] Upload trop grand, mauvais MIME, extension incohérente ou fichier corrompu.
- [x] Fichier uploadé inaccessible publiquement.
- [x] Message vide, trop long, spam ou contenu interdit.
- [x] Signalement abusif, doublonné ou objet inexistant.
- [x] Données sensibles absentes des réponses, URLs, caches et logs.

**Preuve 5.4 :** [`verification/tests/test_documents.py`](verification/tests/test_documents.py), [`messaging/tests/test_messaging.py`](messaging/tests/test_messaging.py), [`accounts/tests/test_logging.py`](accounts/tests/test_logging.py) et [`docs/recette_phase_5_4.md`](docs/recette_phase_5_4.md), executes le 31 aout 2026.

**Preuve phase 5 :** tests automatisés, codes HTTP attendus et couverture des cas négatifs.

---

# Phase 6 - Compatibilité, performance et production

## 6.1 Compatibilité et accessibilité

- [ ] Tester Android et iOS sur petit écran.
- [ ] Tester Flutter Web desktop et mobile.
- [ ] Tester Web Django sur Chrome, Firefox et Safari si disponible.
- [ ] Tester clavier, lecteur d'écran, contraste, navigation sans souris et tailles tactiles.
- [ ] Vérifier absence de chevauchement des textes et contrôles.

## 6.2 Réseau et performance

- [ ] Tester réseau lent, perte réseau, timeout et reconnexion.
- [ ] Vérifier retry sans doubler une mutation.
- [ ] Vérifier reprise d'upload interrompu et refresh JWT concurrent.
- [ ] Mesurer temps de chargement Web/Mobile et définir des seuils.
- [ ] Vérifier pagination, absence de N+1 critiques, taille images et limites uploads.

## 6.3 Observabilité et incidents

- [ ] Configurer logs structurés sans données sensibles.
- [ ] Configurer monitoring disponibilité et erreurs.
- [ ] Configurer alertes API, paiements, webhooks et jobs critiques.
- [ ] Versionner procédure d'incident, support et restauration.

## 6.4 Go/No-Go

- [ ] Staging avec URL, base, email et prestataire sandbox fonctionnels.
- [ ] Installation propre, migrations et seed validés.
- [ ] Tests, analyse et formatage Web/API/Mobile verts.
- [ ] Aucun secret ou donnée de test sensible dans le dépôt.
- [ ] Sauvegarde/restauration et `check --deploy` validés.
- [ ] Recettes Apprenant, Formateur et Admin signées.
- [ ] Versions Web/API et Mobile produites.
- [ ] Rollback validé et décision Go/No-Go enregistrée.

## Définition de terminé

Une tâche est terminée uniquement si la règle métier, le modèle/migration, le service, la permission objet, le contrat API, l'interface concernée, les états asynchrones, les événements, les tests positifs/négatifs et la documentation sont couverts par une preuve.

## Ordre de codage recommandé

1. Phase 1 : environnements, sécurité, stockage et CI.
2. Phase 2 : contrats API, référentiels et permissions internes.
3. Phase 3 : écrans Flutter Formateur, paiement, session et deep links.
4. Phase 4 : administration Flutter connectée.
5. Phase 5 : parcours intégrés et tests négatifs.
6. Phase 6 : compatibilité, performance, monitoring et Go/No-Go.