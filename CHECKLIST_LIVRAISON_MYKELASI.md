# Checklist de livraison complète MyKELASI

Version : 1.0  
Date : 26 août 2026  
Périmètre : plateforme Web Django, API REST et application Flutter Android/iOS/Web  
Objectif : disposer d'une première version livrable, testée et exploitable par les apprenants, formateurs et administrateurs.

## Règles d'utilisation

- [ ] Chaque tâche est validée avec une preuve : test, capture, contrat API, migration ou recette manuelle.
- [ ] Une partie n'est déclarée terminée que lorsque Web, API et Mobile sont cohérents.
- [ ] Le serveur reste la source de vérité pour les statuts, permissions, montants et transitions.
- [ ] Toute fonctionnalité doit couvrir les états chargement, succès, vide, erreur et reprise.
- [ ] Toute mutation doit être protégée contre le double clic, le rejeu et les accès à un autre compte.
- [ ] Les données sensibles ne sont jamais exposées dans les logs, URLs publiques, caches ou réponses inutiles.
- [ ] Les décisions métier marquées « à valider » doivent être approuvées avant l'implémentation concernée.

---

# Partie 0 - Décisions produit et périmètre V1

## Étape 0.1 - Rôles et responsabilités

**Preuve de cadrage :** [DECISIONS_PRODUIT_V1.md](DECISIONS_PRODUIT_V1.md#partie-01---roles-et-responsabilites)

- [x] Confirmer les rôles publics : `LEARNER` et `TEACHER`.
- [x] Confirmer les rôles internes : support, vérification, finance, modération, admin et super-admin.
- [x] Définir les permissions de chaque rôle et les objets accessibles.
- [x] Confirmer qu'un compte possède un rôle public principal en V1.
- [x] Définir la procédure de changement de rôle.
- [x] Définir les règles de suspension, désactivation, suppression et réactivation.

## Étape 0.2 - Référentiels et règles métier

**Preuve de cadrage :** [DECISIONS_PRODUIT_V1.md](DECISIONS_PRODUIT_V1.md#partie-02---referentiels-et-regles-metier)

- [x] Valider les matières, niveaux, modes d'enseignement et zones de Kinshasa.
- [x] Charger les référentiels par migration ou commande de seed idempotente.
- [x] Confirmer la devise transactionnelle : CDF.
- [x] Confirmer le fuseau métier : `Africa/Kinshasa`.
- [x] Confirmer les règles d'intégrité académique pour les TFC, mémoires et travaux.
- [x] Définir les contenus interdits et le circuit de signalement.
- [x] Choisir le prestataire Mobile Money et obtenir sa documentation sandbox.
- [x] Valider commission, annulation, remboursement, litige et calendrier de versement.
- [x] Définir les critères du pilote : inscriptions, demandes, réservations, sessions terminées, réachat et litiges.

## Étape 0.3 - Parcours V1 accepté

**Preuve de cadrage :** [DECISIONS_PRODUIT_V1.md](DECISIONS_PRODUIT_V1.md#partie-03---parcours-v1-accepte)

- [x] Valider le parcours Apprenant : inscription → profil → besoin → matches → propositions → réservation → paiement → session → avis → réachat.
- [x] Valider le parcours Formateur : inscription → email → profil → vérification → publication → matches → proposition → réservation → session → revenus → avis.
- [x] Valider le parcours Admin : connexion sécurisée → supervision → vérification → modération → finance → rapports.
- [x] Définir les pages et écrans obligatoires listés dans les parties suivantes.
- [x] Fixer les critères d'acceptation avant de commencer chaque jalon.

---

# Partie 1 - Socle technique commun Web, API et Mobile

## Étape 1.1 - Configuration Django et environnements

- [x] Vérifier `.env.example` sans secret réel.
- [x] Vérifier que `SECRET_KEY`, base de données, hôtes, email et paiement viennent de l'environnement.
- [x] Corriger la configuration email de production avec `EMAIL_BACKEND` et non `MAILERS`.
- [x] Séparer clairement développement, test, staging et production.
- [x] Vérifier `DEBUG=False` en staging et production.
- [x] Configurer `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` et les domaines officiels.
- [x] Configurer PostgreSQL pour staging et production.
- [x] Configurer langue française et `Africa/Kinshasa`.
- [x] Configurer fichiers statiques, médias et stockage privé des documents.
- [x] Ajouter une commande ou procédure de migration reproductible.
- [x] Ajouter `/health/` et, si nécessaire, `/ready/` sans données sensibles.
- [x] Exécuter `python manage.py check` et `python manage.py check --deploy`.

## Étape 1.2 - API et contrats

- [x] Stabiliser la version `/api/v1/`.
- [x] Documenter chaque endpoint avec méthode, authentification, permissions, payloads et erreurs.
- [x] Uniformiser pagination : `count`, `next`, `previous`, `results`.
- [x] Uniformiser les dates ISO 8601 avec fuseau.
- [x] Sérialiser les montants en chaînes décimales, jamais en flottants.
- [x] Documenter les enums et transitions autorisées.
- [x] Retourner des codes métier exploitables par Flutter.
- [x] Vérifier les erreurs par champ pour les formulaires.
- [x] Tester les réponses 200, 201, 204, 400, 401, 403, 404, 409, 429 et 500 utiles.
- [x] Vérifier les permissions objet sur chaque endpoint privé.
- [x] Ajouter limitation de débit sur auth, messages, signalements et mutations sensibles.
- [x] Produire une collection Postman/Insomnia ou un schéma OpenAPI versionné.

## Étape 1.3 - Sécurité transverse

- [x] Vérifier absence de secrets dans Git, logs, fixtures et captures.
- [x] Activer cookies `Secure`, `HttpOnly`, `SameSite` et HTTPS en production.
- [x] Vérifier CSRF sur Web et authentification JWT sur API.
- [x] Vérifier protections XSS, injection, IDOR, brute force et enumeration de comptes.
- [x] Vérifier contrôle MIME, extension, taille et stockage privé des uploads.
- [x] Ne jamais exposer adresse exacte, GPS, téléphone ou documents par défaut.
- [x] Ajouter audit des actions sensibles : paiement, remboursement, vérification, modération, accès document.
- [x] Définir rétention, anonymisation et suppression des données.
- [x] Configurer sauvegarde chiffrée et restauration testée.

## Étape 1.4 - Socle Flutter

- [x] Vérifier configuration par environnement et base URL injectable.
- [x] Vérifier `ApiClient`, timeouts, refresh JWT et gestion d'une seule requête de refresh concurrente.
- [x] Vérifier stockage sécurisé des tokens et effacement à la déconnexion.
- [x] Centraliser `AppException`, erreurs réseau et erreurs de validation.
- [x] Ajouter composants partagés loading/empty/error/retry.
- [x] Vérifier navigation, deep links et retour après authentification.
- [x] Vérifier accessibilité, contrastes, clavier, tailles tactiles et écrans étroits.
- [x] Vérifier persistance non sensible et absence de cache transactionnel hors ligne.
- [x] Configurer environnements Android, iOS et Web.
- [x] Ajouter tests unitaires, repository, controller, widget et parcours.

## Étape 1.5 - Qualité et CI

- [x] Ajouter CI pour dépendances, migrations, `django check`, tests Django et Ruff.
- [x] Ajouter CI Flutter pour formatage, analyse et tests.
- [x] Vérifier `git diff --check`.
- [x] Publier un rapport de couverture par domaine critique.
- [x] Bloquer la livraison si migrations, tests de permissions ou tests de paiement échouent.

---

# Partie 2 - Profil Apprenant

## Étape 2.1 - Compte et onboarding

### Web Django

- [x] Page d'inscription Apprenant.
- [x] Sélection explicite du rôle Apprenant.
- [x] Validation email et mot de passe.
- [x] Consentement aux conditions et communications.
- [x] Page de connexion et déconnexion.
- [x] Page de récupération et changement de mot de passe.
- [x] Page de vérification email et renvoi du lien/code.
- [x] Messages français pour erreurs, compte suspendu et email non vérifié.

### API

- [x] `POST /api/v1/auth/register/` accepte le rôle Apprenant.
- [x] `POST /api/v1/auth/login/`, refresh, logout et `GET /api/v1/auth/me/` sont testés.
- [x] Vérifier qu'un Apprenant ne reçoit jamais les permissions Formateur.
- [x] Tester 401, 403, 409, 429 et compte désactivé.

### Flutter

- [x] Écran onboarding public.
- [x] Écran inscription Apprenant.
- [x] Écran connexion générique adapté au rôle.
- [x] Écran vérification email.
- [x] Restauration de session après redémarrage.
- [x] Guard vers l'espace Apprenant après authentification.
- [x] Guard empêchant l'accès aux routes Formateur.

## Étape 2.2 - Profil et préférences Apprenant

### Backend

- [x] Confirmer `LearnerProfile` et ses champs éditables.
- [x] Créer `GET/PATCH /api/v1/learner/profile/`.
- [x] Permettre niveaux, matières d'intérêt et zone préférée si retenue.
- [x] Définir complétion minimale du profil.
- [x] Tester isolation entre profils.

### Web

- [x] Page profil apprenant.
- [x] Page modification du profil.
- [x] Sélection des niveaux et matières.
- [x] Page paramètres, consentements et suppression de compte.

### Flutter

- [x] Écran `LearnerProfileScreen`.
- [x] Écran modification du profil.
- [x] Repository, DTO, controller/provider et validations.
- [x] États loading, vide, erreur, retry et succès.
- [x] Tests parsing, repository, permissions et widget.

---

# Partie 3 - Recherche et besoin d'apprentissage Apprenant

## Étape 3.1 - Catalogue des Formateurs

### Backend/API

- [x] Stabiliser `GET /api/v1/teachers/`.
- [x] Filtrer matière, niveau, mode, zone et budget.
- [x] Ajouter pagination, tri et recherche textuelle si nécessaire.
- [x] Retourner uniquement profils publics et actifs.
- [x] Masquer adresse précise, téléphone et documents.
- [x] Retourner tarif, devise, vérifications, réputation, disponibilité et zones publiques.
- [x] Tester aucun résultat, profil non public et accès anonyme.

### Web

- [x] Page de recherche des Formateurs.
- [x] Filtres utilisables sur mobile.
- [x] Cartes de résultats comparables.
- [x] Page publique détaillée d'un Formateur.
- [x] Affichage séparé identité, diplôme, téléphone et email vérifiés.
- [x] Affichage des avis publiés.

### Flutter

- [x] Écran liste des Formateurs.
- [x] Filtres et remise à zéro.
- [x] Pagination ou chargement progressif.
- [x] Écran détail public Formateur.
- [x] Écran comparaison de plusieurs Formateurs.
- [x] Tests état vide, erreur réseau, filtres et écran étroit.

## Étape 3.2 - Création d'une demande

### Backend/API

- [x] Valider `LearningRequest` : matière, niveau, mode, zone, budget, date, heure, fréquence et description.
- [x] `GET /api/v1/requests/` ne retourne que les demandes de l'Apprenant connecté.
- [x] `POST /api/v1/requests/` vérifie rôle, référentiels actifs et champs cohérents.
- [x] Vérifier que date et heure sont renseignées ensemble ou toutes deux absentes.
- [x] Générer les matches après création.
- [x] Enregistrer `request.created` et `match.created`.
- [x] Tester montants, longueurs, dates passées, référentiels inactifs et double soumission.

### Web

- [x] Formulaire demande courte.
- [x] Formulaire demande détaillée.
- [x] Résumé et confirmation avant envoi.
- [x] Liste de mes demandes.
- [x] Détail d'une demande et son statut.
- [x] Modification ou fermeture selon les règles métier.

### Flutter

- [x] Remplacer le placeholder `CreateRequestScreen`.
- [x] Créer modèle, repository et controller de demande.
- [x] Sélecteurs matières, niveaux, modes et zones depuis l'API.
- [x] Champ budget CDF sans perte de précision.
- [x] Sélection date/heure et fréquence.
- [x] Description avec compteur et validation.
- [x] Désactiver le bouton pendant l'envoi.
- [x] Afficher erreurs globales et erreurs par champ.
- [x] Rediriger vers détail/matches après succès serveur.
- [x] Ajouter écran liste et détail des demandes.

## Étape 3.3 - Matching explicable

- [x] Définir et versionner les pondérations du score.
- [x] Inclure matière, niveau, mode, zone, budget, disponibilité, fiabilité, réputation et taux de réponse.
- [x] Exclure tout avantage Premium du classement organique.
- [x] Retourner les raisons lisibles du match.
- [x] Garantir ordre stable et pagination cohérente.
- [x] Tester qu'une modification de critère modifie le score de façon prévisible.
- [x] Écran Apprenant des matches pour chaque demande.
- [x] Afficher score, raisons, tarif, disponibilité et vérifications.
- [x] Permettre sélection pour comparaison et consultation du profil.

---

# Partie 4 - Propositions et choix du Formateur Apprenant

## Étape 4.1 - Réception des propositions

- [x] `GET /api/v1/requests/{id}/proposals/` réservé au propriétaire ou au Formateur autorisé.
- [x] Afficher montant, message, disponibilité, statut et identité publique du Formateur.
- [x] Distinguer envoyée, acceptée, refusée et retirée.
- [x] Empêcher une proposition après fermeture de la demande.
- [x] Ajouter événements `proposal.sent` et changement de statut.
- [x] Créer page Web et écran Flutter de liste des propositions.

## Étape 4.2 - Acceptation et refus

- [x] Définir l'endpoint d'acceptation d'une proposition.
- [x] Définir l'endpoint de refus ou de rejet par l'Apprenant.
- [x] Garantir une seule proposition acceptée par demande.
- [x] Fermer ou verrouiller les autres propositions selon la règle métier.
- [x] Créer la réservation uniquement selon le flux validé.
- [x] Protéger l'action par transaction et idempotence.
- [x] Notifier l'Apprenant et le Formateur.
- [x] Tester courses concurrentes, double clic, proposition inconnue et demande fermée.
- [x] Ajouter boutons et confirmations Web/Flutter avec état serveur, jamais optimiste.

---

# Partie 5 - Réservation et session Apprenant

## Étape 5.1 - Création de réservation

### Backend/API

- [x] `POST /api/v1/bookings/` réservé à l'Apprenant.
- [x] Vérifier proposition acceptée, participants, date, durée, mode, zone et prix.
- [x] Vérifier conflit de créneau dans une transaction atomique.
- [x] Figer montant, devise et politique d'annulation dans la réservation.
- [x] Enregistrer `booking.created`.
- [x] Créer les transitions avec auteur, date et motif.

### Web et Flutter

- [x] Écran de résumé avant confirmation.
- [x] Écran de sélection date/heure compatible avec la disponibilité.
- [x] Afficher Formateur, matière, mode, zone approximative, durée, prix et politique.
- [x] Afficher confirmation serveur et identifiant public.
- [x] Ne révéler les coordonnées privées qu'après confirmation et selon règle validée.

## Étape 5.2 - Liste et détail des réservations Apprenant

- [x] Créer page Web des réservations Apprenant.
- [x] Créer écran Flutter dédié Apprenant, distinct des actions Formateur.
- [x] Filtres : à venir, passées, annulées, contestées.
- [x] Afficher statuts `PENDING`, `CONFIRMED`, `REJECTED`, `CANCELLED`, `COMPLETED`, `NO_SHOW`, `DISPUTED`.
- [x] Afficher historique des transitions.
- [x] Permettre annulation selon la politique.
- [x] Permettre ouverture d'un litige selon les règles.
- [x] Tester qu'un Apprenant ne peut pas confirmer, refuser ou marquer la présence du Formateur.

## Étape 5.3 - Réalisation de session

- [x] Créer ou confirmer la machine de session : présence, début, fin, résultat.
- [x] Définir qui peut marquer présence, absence et fin de session.
- [x] Gérer session en ligne, domicile, lieu public et centre.
- [x] Envoyer rappels avant session.
- [x] Enregistrer `session.completed` uniquement après transition valide.
- [x] Afficher session à venir, en cours, terminée et litigieuse.
- [x] Tester absences, fin avant début, double présence et actions hors délai.

---

# Partie 6 - Paiement, reçu et remboursement Apprenant

## Étape 6.1 - Paiement

- [x] Choisir et configurer le prestataire Mobile Money sandbox.
- [x] `POST /api/v1/bookings/{id}/payments/` réservé à l'Apprenant de la réservation confirmée.
- [x] Exiger et persister `Idempotency-Key`.
- [x] Afficher montant et devise issus du serveur.
- [x] Ne jamais confirmer un paiement depuis le seul client.
- [x] Créer écran Web de paiement.
- [x] Créer écran Flutter de paiement Apprenant, distinct des revenus Formateur.
- [x] Gérer initiation, attente, succès, échec, annulation et reprise.
- [x] Ne jamais stocker de secret Mobile Money dans Flutter.

## Étape 6.2 - Webhook et rapprochement

- [x] Vérifier signature, référence, montant et devise côté serveur.
- [x] Rendre le webhook idempotent et transactionnel.
- [x] Tester double webhook et payload falsifié.
- [x] Créer ledger immuable et équilibré.
- [x] Enregistrer `payment.completed` une seule fois.
- [x] Prévoir remboursement, litige financier et rapprochement manuel.
- [x] Ajouter accès au reçu uniquement aux participants concernés.

## Étape 6.3 - Historique financier Apprenant

- [x] Page Web des paiements et reçus.
- [x] Écran Flutter historique des paiements.
- [x] Détail référence, date, montant, devise et statut.
- [x] Téléchargement ou affichage sécurisé du reçu.
- [x] Afficher remboursement et motif lorsqu'il existe.
- [x] Tester accès à un paiement d'un autre utilisateur.

---

# Partie 7 - Messagerie, notifications et avis Apprenant

## Étape 7.1 - Messagerie sécurisée

- [x] Créer une conversation liée à une demande, proposition ou réservation selon la règle choisie.
- [x] Autoriser uniquement participants et personnel habilité en cas de signalement.
- [x] Ajouter pagination, marquage lu et actualisation.
- [x] Valider longueur et contenu des messages.
- [x] Limiter le débit et lutter contre spam.
- [x] Permettre signalement d'une conversation ou d'un message.
- [x] Créer liste et détail Web/Flutter pour l'Apprenant.
- [x] Tester IDOR, message vide, message trop long et participant tiers.

## Étape 7.2 - Notifications

- [x] Modèle notification et préférences par canal.
- [x] Notifications pour vérification, match, proposition, réservation, rappel, paiement, session et avis.
- [x] `GET /api/v1/notifications/` et actions de lecture.
- [x] Préférences email, push et Web selon disponibilité V1.
- [x] Liens profonds vers l'objet concerné.
- [x] Écrans Web/Flutter liste, non-lu, tout marquer lu et retry.
- [x] Ne pas mettre en cache de données privées dans un cache public.

## Étape 7.3 - Avis Apprenant

- [x] Autoriser un avis seulement pour une session `COMPLETED`.
- [x] Garantir un avis par participant et session selon la règle approuvée.
- [x] Champs note, commentaire, ponctualité, communication et qualité si retenus.
- [x] Créer formulaire Web et écran Flutter après session terminée.
- [x] Afficher erreurs, confirmation et impossibilité de doublon.
- [x] Publier l'avis après modération/règles définies.
- [x] Recalculer Trust Score de manière reproductible.
- [x] Permettre signalement d'un avis et masquer avec motif audité.

---

# Partie 8 - Parcours Formateur

## Étape 8.1 - Compte et profil

- [x] Inscription Formateur et vérification email.
- [x] Guards Flutter pour rôle `TEACHER`.
- [x] Profil privé, identité, titre, bio, expérience, langues et tarif CDF.
- [x] Sélection matières, niveaux, modes et zones depuis le catalogue API.
- [x] Complétion calculée par le backend.
- [x] Affichage des prérequis manquants.
- [x] Publication/dépublication confirmée par la réponse serveur.
- [ ] Tests du contrat profil et des erreurs 400/401/403/404/409.

## Étape 8.2 - Vérification et disponibilités

- [x] Dépôt privé de documents d'identité et certifications.
- [x] Contrôle type MIME, extension, taille et stockage privé.
- [x] Statuts `pending`, `approved`, `rejected`, `expired`.
- [x] Motif de rejet et nouveau dépôt.
- [x] CRUD disponibilités hebdomadaires.
- [x] Contrôle fin supérieure au début et chevauchements.
- [ ] Tests mobile réel, upload interrompu et reprise.

## Étape 8.3 - Demandes, propositions et sessions

- [x] Liste des demandes matchées avec raisons.
- [x] Détail demande et formulaire de proposition.
- [x] Prix, message et disponibilité validés côté serveur.
- [x] Suivi des propositions envoyées.
- [x] Liste des réservations avec actions limitées au rôle Formateur.
- [x] Présence, absence, fin de session et litige.
- [x] Messagerie avec Apprenant sans exposition automatique du téléphone.

## Étape 8.4 - Revenus et réputation

- [x] Résumé revenus, transactions et versements.
- [x] Commission calculée côté serveur.
- [x] Historique des paiements reçus et statuts.
- [x] Consultation des avis.
- [x] Réponse à un avis selon la règle approuvée.
- [x] Trust Score affiché avec composantes compréhensibles.
- [x] Notifications et paramètres Formateur.
- [x] Tester que le Formateur ne peut pas modifier le paiement de l'Apprenant.

---

# Partie 9 - Administration et opérations

## Étape 9.1 - Accès et sécurité Admin

- [x] Créer comptes internes séparés des comptes publics.
- [x] Définir matrice permissions support/vérification/finance/modération/admin.
- [x] Activer MFA pour admin et super-admin avant production.
- [x] Ajouter journalisation des connexions et actions privilégiées.
- [ ] Tester que chaque équipe ne voit que ses données nécessaires.

## Étape 9.2 - Vérification

- [x] File des documents `pending`.
- [x] Consultation sécurisée et auditée des documents.
- [x] Actions approuver, rejeter, expirer avec motif.
- [x] Notifications au Formateur.
- [x] Historique non modifiable des décisions.
- [ ] Tester absence d'accès public aux fichiers.

## Étape 9.3 - Modération et support

- [x] File des profils, messages, propositions, réservations et avis signalés.
- [x] Attribution, statut, priorité et historique du signalement.
- [x] Actions masquer, restaurer, avertir, suspendre et clôturer.
- [x] Accès temporaire et audité aux conversations signalées.
- [x] Écran support des comptes, demandes et réservations sans données finance inutiles.
- [x] Gestion des disputes et communication aux parties.

## Étape 9.4 - Finance

- [x] Liste paiements, webhooks, remboursements, ledger et versements.
- [x] Rapprochement manuel avec référence externe.
- [x] Traitement des paiements bloqués et litiges.
- [x] Export contrôlé des données financières.
- [x] Journalisation de toute modification financière.
- [x] Vérifier qu'aucune écriture ledger existante n'est modifiable silencieusement.

## Étape 9.5 - Référentiels et configuration

- [ ] CRUD administrable des matières, niveaux, modes et zones.
- [ ] Activation/désactivation sans supprimer les références utilisées.
- [ ] Configuration pondérations matching.
- [ ] Configuration commission, devise et politiques versionnées.
- [ ] Historique des changements de configuration.

## Étape 9.6 - Analytics produit

- [x] Modèle événements avec données minimales et pseudonymisables.
- [x] KPI demandes, matches, propositions, bookings et sessions terminées.
- [x] KPI paiements, GMV, commission, annulations, no-show et litiges.
- [x] Conversion demande → réservation et réservation → session terminée.
- [x] Taux de réponse et taux de réachat.
- [x] Dashboard filtrable par période, matière et zone.
- [x] Vérifier que le North Star repose sur les sessions réellement terminées.

---

# Partie 10 - Pages Web obligatoires

## Étape 10.1 - Pages publiques

- [x] Accueil et présentation claire du service.
- [x] Inscription, connexion, vérification email et récupération mot de passe.
- [x] Recherche Formateurs.
- [x] Détail public Formateur.
- [x] Conditions, confidentialité, règles d'intégrité académique et contact.

## Étape 10.2 - Espace Apprenant

- [x] Tableau de bord Apprenant.
- [x] Profil et paramètres.
- [x] Nouvelle demande courte et détaillée.
- [x] Mes demandes et détail.
- [x] Matches et comparaison.
- [x] Propositions reçues et choix.
- [x] Réservations et détail.
- [x] Paiement, historique et reçus.
- [x] Sessions, messagerie et notifications.
- [x] Avis, litiges et réachat.

## Étape 10.3 - Espace Formateur

- [x] Tableau de bord.
- [x] Profil, édition et publication.
- [x] Disponibilités et tarification.
- [x] Vérification et certifications.
- [x] Demandes matchées et propositions.
- [x] Réservations et sessions.
- [x] Messagerie, notifications, avis, revenus et paramètres.

## Étape 10.4 - Espace interne

- [x] Dashboard opérationnel.
- [x] Vérification.
- [x] Modération et signalements.
- [x] Support.
- [x] Finance.
- [x] Référentiels.
- [x] Analytics et exports contrôlés.

---

# Partie 11 - Écrans Flutter obligatoires

## Étape 11.1 - Écrans communs

- [x] Splash et restauration de session.
- [x] Onboarding.
- [x] Connexion.
- [x] Inscription avec choix de rôle.
- [x] Vérification email.
- [x] Erreur réseau et retry.
- [x] Session expirée et reconnexion.
- [x] Paramètres et déconnexion.

## Étape 11.2 - Écrans Apprenant

- [x] `LearnerDashboardScreen`.
- [x] `LearnerProfileScreen` et édition.
- [x] `TeacherSearchScreen`.
- [x] `TeacherDetailScreen`.
- [x] `TeacherComparisonScreen`.
- [x] `CreateRequestScreen` fonctionnel.
- [x] `LearningRequestsScreen`.
- [x] `LearningRequestDetailScreen`.
- [x] `MatchesScreen`.
- [x] `ProposalsScreen` et détail.
- [x] `BookingCreateScreen`.
- [x] `LearnerBookingsScreen` et détail.
- [x] `LearnerPaymentScreen`.
- [x] `PaymentHistoryScreen` et reçu.
- [x] `LearnerSessionsScreen`.
- [x] `LearnerMessagingScreen` et conversation.
- [x] `LearnerNotificationsScreen`.
- [x] `CreateReviewScreen`.
- [x] `RepeatBookingScreen` ou action de réachat.

## Étape 11.3 - Écrans Formateur

- [x] Dashboard.
- [x] Profil et édition.
- [x] Offre pédagogique et tarification.
- [x] Disponibilités.
- [x] Vérification et certifications.
- [x] Demandes compatibles.
- [x] Création et suivi proposition.
- [x] Réservations et sessions.
- [x] Messagerie.
- [x] Notifications.
- [x] Revenus, transactions et versements.
- [x] Avis, réputation et réponse.
- [x] Paramètres.

## Étape 11.4 - Navigation et guards

- [x] Routes publiques accessibles sans session.
- [x] Routes Apprenant protégées par session et rôle.
- [x] Routes Formateur protégées par session, rôle, email vérifié et profil si nécessaire.
- [x] Routes internes non exposées dans le client public ou protégées strictement.
- [x] Redirections après login, logout, expiration et changement de rôle.
- [x] Deep links vers demande, proposition, réservation, paiement et notification.

---

# Partie 12 - Recette intégrée et première livraison

## Étape 12.1 - Scénario Apprenant complet

- [x] Créer un compte Apprenant.
- [x] Vérifier email.
- [x] Compléter le profil.
- [x] Rechercher des Formateurs.
- [x] Créer une demande.
- [x] Vérifier matches et raisons.
- [x] Consulter au moins deux profils.
- [x] Recevoir plusieurs propositions.
- [x] Accepter une seule proposition.
- [x] Créer une réservation sans conflit.
- [x] Faire un paiement sandbox.
- [x] Recevoir confirmation et reçu.
- [x] Réaliser une session.
- [x] Publier un avis.
- [x] Réserver à nouveau avec le même Formateur.

## Étape 12.2 - Scénario Formateur complet

- [x] Créer un compte Formateur.
- [x] Vérifier email.
- [x] Compléter et publier le profil.
- [x] Déclarer disponibilités et documents.
- [x] Recevoir une demande compatible.
- [x] Envoyer une proposition.
- [x] Échanger avec l'Apprenant.
- [x] Confirmer une réservation.
- [x] Marquer présence et terminer session.
- [x] Consulter revenu et avis.
- [x] Répondre à un avis si autorisé.

## Étape 12.3 - Scénario Admin complet

- [x] Se connecter avec MFA.
- [x] Traiter un document Formateur.
- [x] Traiter un signalement.
- [x] Consulter un litige financier.
- [x] Vérifier une écriture de ledger.
- [ ] Modifier un référentiel sans casser les objets existants.
- [x] Consulter les KPI.
- [x] Vérifier les journaux d'audit.

## Étape 12.4 - Tests négatifs obligatoires

- [ ] Apprenant non vérifié tentant une action protégée.
- [ ] Formateur tentant une action Apprenant.
- [ ] Utilisateur lisant l'objet d'un autre utilisateur.
- [ ] Proposition déjà acceptée ou retirée.
- [ ] Double réservation du même créneau.
- [ ] Double paiement avec même clé d'idempotence.
- [ ] Webhook invalide ou rejoué.
- [ ] Session terminée deux fois.
- [ ] Avis avant session terminée ou en doublon.
- [ ] Upload trop grand, mauvais MIME ou fichier public.
- [ ] Message vide, trop long ou signalement abusif.
- [ ] Accès après suspension ou désactivation.

## Étape 12.5 - Compatibilité et performance

- [ ] Tester Android téléphone petit écran.
- [ ] Tester iOS téléphone petit écran.
- [ ] Tester Flutter Web desktop et mobile.
- [ ] Tester Web Django sur Chrome, Firefox et Safari si disponible.
- [ ] Tester clavier, lecteur d'écran, contraste et navigation sans souris.
- [ ] Tester réseau lent, perte réseau, timeout et reprise.
- [ ] Vérifier temps de chargement des pages principales.
- [ ] Vérifier pagination et absence de requêtes N+1 critiques.
- [ ] Vérifier taille des images et uploads.

## Étape 12.6 - Go/No-Go production

- [ ] Staging dispose d'une URL, base, email et prestataire sandbox fonctionnels.
- [ ] Migrations et seed exécutables sur une installation propre.
- [ ] Tests Django et Flutter verts.
- [ ] Analyse statique et formatage verts.
- [ ] Aucun secret ou donnée de test sensible dans le dépôt.
- [ ] `django check --deploy` vert ou exceptions documentées.
- [ ] Sauvegarde et restauration validées.
- [ ] Logs, monitoring et alertes configurés.
- [ ] Politique de support et procédure d'incident écrites.
- [ ] Recette Apprenant, Formateur et Admin signée.
- [ ] Version Web/API taguée et version Mobile produite.
- [ ] Plan de rollback validé.
- [ ] Décision Go/No-Go enregistrée par le responsable produit.

---

# Ordre recommandé des jalons

1. **Jalon A - Socle** : Partie 0 et Partie 1.
2. **Jalon B - Apprenant** : Parties 2 à 7, jusqu'au premier parcours transactionnel complet.
3. **Jalon C - Formateur** : Partie 8 et finalisation des écrans Formateur existants.
4. **Jalon D - Administration** : Partie 9 et opérations minimales.
5. **Jalon E - Livraison** : Parties 10 à 12, staging, recette et production.

## Définition de terminé pour chaque fonctionnalité

- [ ] Règle métier approuvée.
- [ ] Modèle et migration présents si nécessaire.
- [ ] Service métier testé.
- [ ] Permission objet testée.
- [ ] Endpoint documenté et testé.
- [ ] Page Web livrée.
- [ ] Écran Mobile livré.
- [ ] États loading/empty/error/retry traités.
- [ ] Événement métier enregistré si nécessaire.
- [ ] Parcours positif et tests négatifs validés.
- [ ] Documentation et contrat mis à jour.
