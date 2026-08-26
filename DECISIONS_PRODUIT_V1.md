# Décisions Produit V1 - MyKELASI

Version : 1.0  
Date : 26 août 2026  
Périmètre : Plateforme Web Django, API REST et Application Mobile Flutter  

---

# Partie 0.1 - Rôles et responsabilités

## 1. Rôles publics

MyKELASI propose deux rôles publics principaux pour les utilisateurs de la plateforme :

- **`LEARNER` (Apprenant)** :
  - **Droits & Accès** : Création et gestion de son profil apprenant, publication de demandes d'apprentissage (`LearningRequest`), consultation des enseignants publics et des propositions reçues, acceptation de propositions, création et paiement de réservations (`Booking`), participation aux sessions, échanges par messagerie sécurisée, publication d'avis sur les sessions terminées, émission de signalements.
  - **Restrictions** : Ne peut pas créer de profil enseignant, envoyer de propositions, ni accéder aux dossiers de vérification ou aux fonctions d'administration interne.

- **`TEACHER` (Enseignant / Formateur)** :
  - **Droits & Accès** : Création, complétion et publication de son profil professionnel, gestion de ses disponibilités et tarification en CDF, soumission de documents d'identité et de certifications pour vérification, consultation des demandes d'apprentissage compatibles/matchées, envoi de propositions, suivi de ses réservations, enregistrement de sa présence/fin de session, consultation de ses revenus et avis reçus, réponse aux avis reçus (si autorisé).
  - **Restrictions** : Ne peut pas publier de demandes d'apprentissage en tant qu'apprenant, ni initier de paiement de réservation pour d'autres apprenants.

---

## 2. Rôles internes (Groupes d'administration / Support)

L'administration et la modération s'appuient sur les groupes Django `accounts.roles.INTERNAL_ROLE_NAMES` selon le principe du moindre privilège :

- **`SUPPORT`** :
  - Accès aux fiches utilisateurs, demandes et réservations pour assister les utilisateurs. Aucun accès aux documents d'identité privés ni aux outils d'exécution financière directe.
- **`VERIFICATION`** :
  - File de traitement des pièces d'identité et certifications professionnelles (`IdentityVerification`, `ProfessionalCredential`). Décisions d'approbation, rejet ou expiration avec motifs auditables.
- **`FINANCE`** :
  - Supervision des transactions Mobile Money, journal immuable (`LedgerEntry`), rapprochement manuel, traitement des litiges financiers et des remboursements.
- **`MODERATION`** :
  - Traitement des signalements (`Report`), modération des contenus, masquage/restauration d'avis (`Review`), suspension temporaire de contenus ou comptes litigieux.
- **`ADMIN`** :
  - Administration globale des référentiels (matières, niveaux, modes, zones), gestion des paramètres système, supervision des équipes internes.
- **`SUPER_ADMIN`** :
  - Accès d'urgence complet, gestion des clés, configuration de sécurité et droits d'accès des administrateurs avec obligation de MFA.

---

## 3. Rôle public principal & Changement de rôle

- **Unicité du rôle public en V1** : Un compte `User` possède un rôle public principal fixé lors de son inscription (`account_type = LEARNER` ou `TEACHER`).
- **Changement de rôle** : La conversion ou le changement de rôle public n'est pas automatique en libre-service dans la V1 pour garantir la cohérence des profils (`LearnerProfile` vs `TeacherProfile`) et des vérifications. La procédure nécessite une demande auprès du support qui procède au contrôle et au basculement.

---

## 4. Statuts de compte et procédures (Suspension, Désactivation, Suppression, Réactivation)

Le modèle `User` contient le champ `status` (`ACTIVE`, `SUSPENDED`, `DEACTIVATED`) :

- **`ACTIVE`** : Le compte fonctionne normalement et a accès aux fonctionnalités de son rôle.
- **`SUSPENDED`** (Suspension) :
  - Déclenché par la modération ou un administrateur en cas de non-respect des CGU, litige grave ou suspicion d'usurpation.
  - **Effets** : Bloque l'authentification (jetons JWT refusés, connexion Web/API refusée avec message explicite), dépublie immédiatement le profil enseignant s'il s'agit d'un formateur, gèle les propositions en cours.
- **`DEACTIVATED`** (Désactivation / Suppression logique) :
  - Demandé par l'utilisateur (droit à l'oubli / clôture) ou appliqué suite à une fermeture administrative.
  - **Effets** : Anonymisation des données personnelles non réglementaires, désactivation de l'accès. Les historiques financiers et ledger immuables sont conservés conformément aux obligations légales congolaises.
- **`REACTIVATION`** (Réactivation) :
  - Réservée aux administrateurs ou au pôle Support/Modération après résolution du litige ou vérification d'identité.

---

# Partie 0.2 - Référentiels et règles métier

## 1. Référentiels V1

Les référentiels actifs sont scellés et seedés de manière immuable et idempotente en base de données (`profiles.migrations.0002_seed_catalog`) :

- **Matières (`Subject`)** : Mathématiques, Français, Anglais, Physique, Chimie, Biologie et sciences, Informatique et bureautique, Programmation, Comptabilité et gestion, Statistiques et méthodologie.
- **Niveaux (`Level`)** : Primaire, Secondaire, Humanités, Supérieur et universitaire, Professionnel et certifications.
- **Modes d'enseignement (`TeachingMode`)** : En ligne, À domicile, Lieu public, Centre de formation.
- **Zones d'intervention (`ServiceArea`)** : Les 24 communes de la ville-province de Kinshasa (Bandalungwa, Barumbu, Bumbu, Gombe, Kalamu, Kasa-Vubu, Kimbanseke, Kinshasa, Kintambo, Kisenso, Lemba, Limete, Lingwala, Makala, Maluku, Masina, Matete, Mont-Ngafula, Ndjili, Ngaba, Ngaliema, Ngiri-Ngiri, Nsele, Selembao). Aucun repérage GPS exact ou adresse résidentielle précise n'est exposé publiquement.

---

## 2. Devise transactionnelle & Fuseau horaire

- **Devise unique transactionnelle V1** : **Franc Congolais (CDF)**.
  - Tous les montants en base et dans l'API REST sont stockés et transmis en valeurs décimales précises associées à la devise `CDF`.
  - Un affichage indicatif en USD est fourni sur les interfaces mobiles/web à des fins de comparaison informative (basé sur le taux indicatif configuré), mais le paiement s'effectue exclusivement en CDF.
- **Fuseau horaire de référence** : **`Africa/Kinshasa`** (`UTC+1`).
  - Toutes les dates et heures de réservations, disponibilités et sessions sont traitées et formatées selon la norme ISO 8601 avec décalage de fuseau horaire.

---

## 3. Charte d'intégrité académique

- **Périmètre d'accompagnement autorisé** : Le soutien scolaire, la préparation aux examens, le coaching méthodologique et le guidage pédagogique.
- **Interdiction stricte** : La rédaction intégrale à la place de l'étudiant de Travaux de Fin de Cycle (TFC), mémoires, thèses, devoirs cotés ou compositions d'examen.
- **Circuit de signalement** : Toute offre, demande ou message sollicitant la rédaction frauduleuse d'un travail académique est automatiquement ou manuellement signalé au pôle `MODERATION` via l'API/interface de signalement (`messaging.Report`).

---

## 4. Paiement Mobile Money, Commissions, Annulations et Litiges

- **Prestataire Mobile Money** : Intégration sandbox standard pour Mobile Money RDC (M-Pesa, Orange Money, Airtel Money).
- **Taux de commission V1** : **10 %** (configurable via `PAYMENT_COMMISSION_RATE`).
- **Politique d'annulation & Remboursement** :
  - Annulation gratuite pour l'apprenant si effectuée plus de 24 heures avant le début de la session.
  - En cas d'annulation hors délai ou de litige (`NO_SHOW`, contestation de déroulement), le montant est gelé et transmis au pôle `FINANCE` / `SUPPORT` pour arbitrage.
- **Journalisation comptable** : Tout flux financier génère une écriture immuable dans le livre journal (`LedgerEntry`).

---

## 5. Critères du pilote Kinshasa

Le succès du pilote opérationnel repose sur les KPI suivis par le module `analytics` :
1. Volume d'inscriptions qualifiées (`LEARNER` et `TEACHER` avec email vérifié).
2. Taux de complétion des profils formateurs (avec vérification d'identité).
3. Nombre de demandes d'apprentissage créées et taux de matching (au moins 3 matches par demande).
4. Nombre de réservations payées et confirmées.
5. Taux de sessions réellement terminées (`COMPLETED`).
6. Taux de réachat (réapparition de réservations secondaires avec le même enseignant).
7. Taux de litiges / signalements (maintenu sous 2 %).

---

# Partie 0.3 - Parcours V1 accepté

## 1. Parcours Apprenant (`LEARNER`)
`Inscription` → `Vérification Email` → `Profil & Préférences` → `Création de demande` → `Matches générés` → `Réception & Comparaison des propositions` → `Acceptation de proposition` → `Création de réservation` → `Paiement Mobile Money (CDF)` → `Réalisation de la session` → `Émission d'un avis` → `Option de réachat / Nouvelle réservation`.

## 2. Parcours Formateur (`TEACHER`)
`Inscription` → `Vérification Email` → `Profil professionnel` → `Dépôt pièces d'identité & Diplômes` → `Validation par le pôle Vérification` → `Déclaration des disponibilités` → `Publication du profil` → `Consultation des demandes matchées` → `Envoi de proposition` → `Réservation confirmée` → `Exécution de la session` → `Suivi des revenus CDF & Avis reçus`.

## 3. Parcours Admin & Opérations
`Connexion sécurisée (MFA en production)` → `Supervision du tableau de bord` → `File de vérification des justificatifs formateurs` → `File de modération des signalements / avis` → `Rapprochement financier & Litiges` → `Rapports & KPI du pilote Kinshasa`.
