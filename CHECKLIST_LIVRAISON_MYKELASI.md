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

- [ ] Stabiliser `GET /api/v1/teachers/`.
- [ ] Filtrer matière, niveau, mode, zone et budget.
- [ ] Ajouter pagination, tri et recherche textuelle si nécessaire.
- [ ] Retourner uniquement profils publics et actifs.
- [ ] Masquer adresse précise, téléphone et documents.
- [ ] Retourner tarif, devise, vérifications, réputation, disponibilité et zones publiques.
- [ ] Tester aucun résultat, profil non public et accès anonyme.

### Web

- [ ] Page de recherche des Formateurs.
- [ ] Filtres utilisables sur mobile.
- [ ] Cartes de résultats comparables.
- [ ] Page publique détaillée d'un Formateur.
- [ ] Affichage séparé identité, diplôme, téléphone et email vérifiés.
- [ ] Affichage des avis publiés.

### Flutter

- [ ] Écran liste des Formateurs.
- [ ] Filtres et remise à zéro.
- [ ] Pagination ou chargement progressif.
- [ ] Écran détail public Formateur.
- [ ] Écran comparaison de plusieurs Formateurs.
- [ ] Tests état vide, erreur réseau, filtres et écran étroit.

## Étape 3.2 - Création d'une demande

### Backend/API

- [ ] Valider `LearningRequest` : matière, niveau, mode, zone, budget, date, heure, fréquence et description.
- [ ] `GET /api/v1/requests/` ne retourne que les demandes de l'Apprenant connecté.
- [ ] `POST /api/v1/requests/` vérifie rôle, référentiels actifs et champs cohérents.
- [ ] Vérifier que date et heure sont renseignées ensemble ou toutes deux absentes.
- [ ] Générer les matches après création.
- [ ] Enregistrer `request.created` et `match.created`.
- [ ] Tester montants, longueurs, dates passées, référentiels inactifs et double soumission.

### Web

- [ ] Formulaire demande courte.
- [ ] Formulaire demande détaillée.
- [ ] Résumé et confirmation avant envoi.
- [ ] Liste de mes demandes.
- [ ] Détail d'une demande et son statut.
- [ ] Modification ou fermeture selon les règles métier.

### Flutter

- [ ] Remplacer le placeholder `CreateRequestScreen`.
- [ ] Créer modèle, repository et controller de demande.
- [ ] Sélecteurs matières, niveaux, modes et zones depuis l'API.
- [ ] Champ budget CDF sans perte de précision.
- [ ] Sélection date/heure et fréquence.
- [ ] Description avec compteur et validation.
- [ ] Désactiver le bouton pendant l'envoi.
- [ ] Afficher erreurs globales et erreurs par champ.
- [ ] Rediriger vers détail/matches après succès serveur.
- [ ] Ajouter écran liste et détail des demandes.

## Étape 3.3 - Matching explicable

- [ ] Définir et versionner les pondérations du score.
- [ ] Inclure matière, niveau, mode, zone, budget, disponibilité, fiabilité, réputation et taux de réponse.
- [ ] Exclure tout avantage Premium du classement organique.
- [ ] Retourner les raisons lisibles du match.
- [ ] Garantir ordre stable et pagination cohérente.
- [ ] Tester qu'une modification de critère modifie le score de façon prévisible.
- [ ] Écran Apprenant des matches pour chaque demande.
- [ ] Afficher score, raisons, tarif, disponibilité et vérifications.
- [ ] Permettre sélection pour comparaison et consultation du profil.

---

# Partie 4 - Propositions et choix du Formateur Apprenant

## Étape 4.1 - Réception des propositions

- [ ] `GET /api/v1/requests/{id}/proposals/` réservé au propriétaire ou au Formateur autorisé.
- [ ] Afficher montant, message, disponibilité, statut et identité publique du Formateur.
- [ ] Distinguer envoyée, acceptée, refusée et retirée.
- [ ] Empêcher une proposition après fermeture de la demande.
- [ ] Ajouter événements `proposal.sent` et changement de statut.
- [ ] Créer page Web et écran Flutter de liste des propositions.

## Étape 4.2 - Acceptation et refus

- [ ] Définir l'endpoint d'acceptation d'une proposition.
- [ ] Définir l'endpoint de refus ou de rejet par l'Apprenant.
- [ ] Garantir une seule proposition acceptée par demande.
- [ ] Fermer ou verrouiller les autres propositions selon la règle métier.
- [ ] Créer la réservation uniquement selon le flux validé.
- [ ] Protéger l'action par transaction et idempotence.
- [ ] Notifier l'Apprenant et le Formateur.
- [ ] Tester courses concurrentes, double clic, proposition inconnue et demande fermée.
- [ ] Ajouter boutons et confirmations Web/Flutter avec état serveur, jamais optimiste.

---

# Partie 5 - Réservation et session Apprenant

## Étape 5.1 - Création de réservation

### Backend/API

- [ ] `POST /api/v1/bookings/` réservé à l'Apprenant.
- [ ] Vérifier proposition acceptée, participants, date, durée, mode, zone et prix.
- [ ] Vérifier conflit de créneau dans une transaction atomique.
- [ ] Figer montant, devise et politique d'annulation dans la réservation.
- [ ] Enregistrer `booking.created`.
- [ ] Créer les transitions avec auteur, date et motif.

### Web et Flutter

- [ ] Écran de résumé avant confirmation.
- [ ] Écran de sélection date/heure compatible avec la disponibilité.
- [ ] Afficher Formateur, matière, mode, zone approximative, durée, prix et politique.
- [ ] Afficher confirmation serveur et identifiant public.
- [ ] Ne révéler les coordonnées privées qu'après confirmation et selon règle validée.

## Étape 5.2 - Liste et détail des réservations Apprenant

- [ ] Créer page Web des réservations Apprenant.
- [ ] Créer écran Flutter dédié Apprenant, distinct des actions Formateur.
- [ ] Filtres : à venir, passées, annulées, contestées.
- [ ] Afficher statuts `PENDING`, `CONFIRMED`, `REJECTED`, `CANCELLED`, `COMPLETED`, `NO_SHOW`, `DISPUTED`.
- [ ] Afficher historique des transitions.
- [ ] Permettre annulation selon la politique.
- [ ] Permettre ouverture d'un litige selon les règles.
- [ ] Tester qu'un Apprenant ne peut pas confirmer, refuser ou marquer la présence du Formateur.

## Étape 5.3 - Réalisation de session

- [ ] Créer ou confirmer la machine de session : présence, début, fin, résultat.
- [ ] Définir qui peut marquer présence, absence et fin de session.
- [ ] Gérer session en ligne, domicile, lieu public et centre.
- [ ] Envoyer rappels avant session.
- [ ] Enregistrer `session.completed` uniquement après transition valide.
- [ ] Afficher session à venir, en cours, terminée et litigieuse.
- [ ] Tester absences, fin avant début, double présence et actions hors délai.

---

# Partie 6 - Paiement, reçu et remboursement Apprenant

## Étape 6.1 - Paiement

- [ ] Choisir et configurer le prestataire Mobile Money sandbox.
- [ ] `POST /api/v1/bookings/{id}/payments/` réservé à l'Apprenant de la réservation confirmée.
- [ ] Exiger et persister `Idempotency-Key`.
- [ ] Afficher montant et devise issus du serveur.
- [ ] Ne jamais confirmer un paiement depuis le seul client.
- [ ] Créer écran Web de paiement.
- [ ] Créer écran Flutter de paiement Apprenant, distinct des revenus Formateur.
- [ ] Gérer initiation, attente, succès, échec, annulation et reprise.
- [ ] Ne jamais stocker de secret Mobile Money dans Flutter.

## Étape 6.2 - Webhook et rapprochement

- [ ] Vérifier signature, référence, montant et devise côté serveur.
- [ ] Rendre le webhook idempotent et transactionnel.
- [ ] Tester double webhook et payload falsifié.
- [ ] Créer ledger immuable et équilibré.
- [ ] Enregistrer `payment.completed` une seule fois.
- [ ] Prévoir remboursement, litige financier et rapprochement manuel.
- [ ] Ajouter accès au reçu uniquement aux participants concernés.

## Étape 6.3 - Historique financier Apprenant

- [ ] Page Web des paiements et reçus.
- [ ] Écran Flutter historique des paiements.
- [ ] Détail référence, date, montant, devise et statut.
- [ ] Téléchargement ou affichage sécurisé du reçu.
- [ ] Afficher remboursement et motif lorsqu'il existe.
- [ ] Tester accès à un paiement d'un autre utilisateur.

---

# Partie 7 - Messagerie, notifications et avis Apprenant

## Étape 7.1 - Messagerie sécurisée

- [ ] Créer une conversation liée à une demande, proposition ou réservation selon la règle choisie.
- [ ] Autoriser uniquement participants et personnel habilité en cas de signalement.
- [ ] Ajouter pagination, marquage lu et actualisation.
- [ ] Valider longueur et contenu des messages.
- [ ] Limiter le débit et lutter contre spam.
- [ ] Permettre signalement d'une conversation ou d'un message.
- [ ] Créer liste et détail Web/Flutter pour l'Apprenant.
- [ ] Tester IDOR, message vide, message trop long et participant tiers.

## Étape 7.2 - Notifications

- [ ] Modèle notification et préférences par canal.
- [ ] Notifications pour vérification, match, proposition, réservation, rappel, paiement, session et avis.
- [ ] `GET /api/v1/notifications/` et actions de lecture.
- [ ] Préférences email, push et Web selon disponibilité V1.
- [ ] Liens profonds vers l'objet concerné.
- [ ] Écrans Web/Flutter liste, non-lu, tout marquer lu et retry.
- [ ] Ne pas mettre en cache de données privées dans un cache public.

## Étape 7.3 - Avis Apprenant

- [ ] Autoriser un avis seulement pour une session `COMPLETED`.
- [ ] Garantir un avis par participant et session selon la règle approuvée.
- [ ] Champs note, commentaire, ponctualité, communication et qualité si retenus.
- [ ] Créer formulaire Web et écran Flutter après session terminée.
- [ ] Afficher erreurs, confirmation et impossibilité de doublon.
- [ ] Publier l'avis après modération/règles définies.
- [ ] Recalculer Trust Score de manière reproductible.
- [ ] Permettre signalement d'un avis et masquer avec motif audité.

---

# Partie 8 - Parcours Formateur

## Étape 8.1 - Compte et profil

- [ ] Inscription Formateur et vérification email.
- [ ] Guards Flutter pour rôle `TEACHER`.
- [ ] Profil privé, identité, titre, bio, expérience, langues et tarif CDF.
- [ ] Sélection matières, niveaux, modes et zones depuis le catalogue API.
- [ ] Complétion calculée par le backend.
- [ ] Affichage des prérequis manquants.
- [ ] Publication/dépublication confirmée par la réponse serveur.
- [ ] Tests du contrat profil et des erreurs 400/401/403/404/409.

## Étape 8.2 - Vérification et disponibilités

- [ ] Dépôt privé de documents d'identité et certifications.
- [ ] Contrôle type MIME, extension, taille et stockage privé.
- [ ] Statuts `pending`, `approved`, `rejected`, `expired`.
- [ ] Motif de rejet et nouveau dépôt.
- [ ] CRUD disponibilités hebdomadaires.
- [ ] Contrôle fin supérieure au début et chevauchements.
- [ ] Tests mobile réel, upload interrompu et reprise.

## Étape 8.3 - Demandes, propositions et sessions

- [ ] Liste des demandes matchées avec raisons.
- [ ] Détail demande et formulaire de proposition.
- [ ] Prix, message et disponibilité validés côté serveur.
- [ ] Suivi des propositions envoyées.
- [ ] Liste des réservations avec actions limitées au rôle Formateur.
- [ ] Présence, absence, fin de session et litige.
- [ ] Messagerie avec Apprenant sans exposition automatique du téléphone.

## Étape 8.4 - Revenus et réputation

- [ ] Résumé revenus, transactions et versements.
- [ ] Commission calculée côté serveur.
- [ ] Historique des paiements reçus et statuts.
- [ ] Consultation des avis.
- [ ] Réponse à un avis selon la règle approuvée.
- [ ] Trust Score affiché avec composantes compréhensibles.
- [ ] Notifications et paramètres Formateur.
- [ ] Tester que le Formateur ne peut pas modifier le paiement de l'Apprenant.

---

# Partie 9 - Administration et opérations

## Étape 9.1 - Accès et sécurité Admin

- [ ] Créer comptes internes séparés des comptes publics.
- [ ] Définir matrice permissions support/vérification/finance/modération/admin.
- [ ] Activer MFA pour admin et super-admin avant production.
- [ ] Ajouter journalisation des connexions et actions privilégiées.
- [ ] Tester que chaque équipe ne voit que ses données nécessaires.

## Étape 9.2 - Vérification

- [ ] File des documents `pending`.
- [ ] Consultation sécurisée et auditée des documents.
- [ ] Actions approuver, rejeter, expirer avec motif.
- [ ] Notifications au Formateur.
- [ ] Historique non modifiable des décisions.
- [ ] Tester absence d'accès public aux fichiers.

## Étape 9.3 - Modération et support

- [ ] File des profils, messages, propositions, réservations et avis signalés.
- [ ] Attribution, statut, priorité et historique du signalement.
- [ ] Actions masquer, restaurer, avertir, suspendre et clôturer.
- [ ] Accès temporaire et audité aux conversations signalées.
- [ ] Écran support des comptes, demandes et réservations sans données finance inutiles.
- [ ] Gestion des disputes et communication aux parties.

## Étape 9.4 - Finance

- [ ] Liste paiements, webhooks, remboursements, ledger et versements.
- [ ] Rapprochement manuel avec référence externe.
- [ ] Traitement des paiements bloqués et litiges.
- [ ] Export contrôlé des données financières.
- [ ] Journalisation de toute modification financière.
- [ ] Vérifier qu'aucune écriture ledger existante n'est modifiable silencieusement.

## Étape 9.5 - Référentiels et configuration

- [ ] CRUD administrable des matières, niveaux, modes et zones.
- [ ] Activation/désactivation sans supprimer les références utilisées.
- [ ] Configuration pondérations matching.
- [ ] Configuration commission, devise et politiques versionnées.
- [ ] Historique des changements de configuration.

## Étape 9.6 - Analytics produit

- [ ] Modèle événements avec données minimales et pseudonymisables.
- [ ] KPI demandes, matches, propositions, bookings et sessions terminées.
- [ ] KPI paiements, GMV, commission, annulations, no-show et litiges.
- [ ] Conversion demande → réservation et réservation → session terminée.
- [ ] Taux de réponse et taux de réachat.
- [ ] Dashboard filtrable par période, matière et zone.
- [ ] Vérifier que le North Star repose sur les sessions réellement terminées.

---

# Partie 10 - Pages Web obligatoires

## Étape 10.1 - Pages publiques

- [ ] Accueil et présentation claire du service.
- [ ] Inscription, connexion, vérification email et récupération mot de passe.
- [ ] Recherche Formateurs.
- [ ] Détail public Formateur.
- [ ] Conditions, confidentialité, règles d'intégrité académique et contact.

## Étape 10.2 - Espace Apprenant

- [ ] Tableau de bord Apprenant.
- [ ] Profil et paramètres.
- [ ] Nouvelle demande courte et détaillée.
- [ ] Mes demandes et détail.
- [ ] Matches et comparaison.
- [ ] Propositions reçues et choix.
- [ ] Réservations et détail.
- [ ] Paiement, historique et reçus.
- [ ] Sessions, messagerie et notifications.
- [ ] Avis, litiges et réachat.

## Étape 10.3 - Espace Formateur

- [ ] Tableau de bord.
- [ ] Profil, édition et publication.
- [ ] Disponibilités et tarification.
- [ ] Vérification et certifications.
- [ ] Demandes matchées et propositions.
- [ ] Réservations et sessions.
- [ ] Messagerie, notifications, avis, revenus et paramètres.

## Étape 10.4 - Espace interne

- [ ] Dashboard opérationnel.
- [ ] Vérification.
- [ ] Modération et signalements.
- [ ] Support.
- [ ] Finance.
- [ ] Référentiels.
- [ ] Analytics et exports contrôlés.

---

# Partie 11 - Écrans Flutter obligatoires

## Étape 11.1 - Écrans communs

- [ ] Splash et restauration de session.
- [ ] Onboarding.
- [ ] Connexion.
- [ ] Inscription avec choix de rôle.
- [ ] Vérification email.
- [ ] Erreur réseau et retry.
- [ ] Session expirée et reconnexion.
- [ ] Paramètres et déconnexion.

## Étape 11.2 - Écrans Apprenant

- [ ] `LearnerDashboardScreen`.
- [ ] `LearnerProfileScreen` et édition.
- [ ] `TeacherSearchScreen`.
- [ ] `TeacherDetailScreen`.
- [ ] `TeacherComparisonScreen`.
- [ ] `CreateRequestScreen` fonctionnel.
- [ ] `LearningRequestsScreen`.
- [ ] `LearningRequestDetailScreen`.
- [ ] `MatchesScreen`.
- [ ] `ProposalsScreen` et détail.
- [ ] `BookingCreateScreen`.
- [ ] `LearnerBookingsScreen` et détail.
- [ ] `LearnerPaymentScreen`.
- [ ] `PaymentHistoryScreen` et reçu.
- [ ] `LearnerSessionsScreen`.
- [ ] `LearnerMessagingScreen` et conversation.
- [ ] `LearnerNotificationsScreen`.
- [ ] `CreateReviewScreen`.
- [ ] `RepeatBookingScreen` ou action de réachat.

## Étape 11.3 - Écrans Formateur

- [ ] Dashboard.
- [ ] Profil et édition.
- [ ] Offre pédagogique et tarification.
- [ ] Disponibilités.
- [ ] Vérification et certifications.
- [ ] Demandes compatibles.
- [ ] Création et suivi proposition.
- [ ] Réservations et sessions.
- [ ] Messagerie.
- [ ] Notifications.
- [ ] Revenus, transactions et versements.
- [ ] Avis, réputation et réponse.
- [ ] Paramètres.

## Étape 11.4 - Navigation et guards

- [ ] Routes publiques accessibles sans session.
- [ ] Routes Apprenant protégées par session et rôle.
- [ ] Routes Formateur protégées par session, rôle, email vérifié et profil si nécessaire.
- [ ] Routes internes non exposées dans le client public ou protégées strictement.
- [ ] Redirections après login, logout, expiration et changement de rôle.
- [ ] Deep links vers demande, proposition, réservation, paiement et notification.

---

# Partie 12 - Recette intégrée et première livraison

## Étape 12.1 - Scénario Apprenant complet

- [ ] Créer un compte Apprenant.
- [ ] Vérifier email.
- [ ] Compléter le profil.
- [ ] Rechercher des Formateurs.
- [ ] Créer une demande.
- [ ] Vérifier matches et raisons.
- [ ] Consulter au moins deux profils.
- [ ] Recevoir plusieurs propositions.
- [ ] Accepter une seule proposition.
- [ ] Créer une réservation sans conflit.
- [ ] Faire un paiement sandbox.
- [ ] Recevoir confirmation et reçu.
- [ ] Réaliser une session.
- [ ] Publier un avis.
- [ ] Réserver à nouveau avec le même Formateur.

## Étape 12.2 - Scénario Formateur complet

- [ ] Créer un compte Formateur.
- [ ] Vérifier email.
- [ ] Compléter et publier le profil.
- [ ] Déclarer disponibilités et documents.
- [ ] Recevoir une demande compatible.
- [ ] Envoyer une proposition.
- [ ] Échanger avec l'Apprenant.
- [ ] Confirmer une réservation.
- [ ] Marquer présence et terminer session.
- [ ] Consulter revenu et avis.
- [ ] Répondre à un avis si autorisé.

## Étape 12.3 - Scénario Admin complet

- [ ] Se connecter avec MFA.
- [ ] Traiter un document Formateur.
- [ ] Traiter un signalement.
- [ ] Consulter un litige financier.
- [ ] Vérifier une écriture de ledger.
- [ ] Modifier un référentiel sans casser les objets existants.
- [ ] Consulter les KPI.
- [ ] Vérifier les journaux d'audit.

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
