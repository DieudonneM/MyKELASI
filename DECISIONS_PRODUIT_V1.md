# Registre des décisions produit V1 MyKELASI

Version : 1.0  
Date : 26 août 2026  
Périmètre : étapes 0.1, 0.2 et 0.3 de `CHECKLIST_LIVRAISON_MYKELASI.md`  
Statut global : **à valider par le porteur produit**

Ce document transforme les propositions existantes en décisions traçables. Une décision ne devient validée qu'après confirmation explicite du porteur produit. Aucun développement dépendant d'un choix `À CONFIRMER` ne doit commencer.

## Légende

- **PROPOSÉ** : cohérent avec les documents actuels, mais pas encore approuvé.
- **À CONFIRMER** : choix nécessaire avant développement ou intégration.
- **VALIDÉ** : approuvé explicitement par le porteur produit.
- **BLOQUANT** : empêche le passage à une étape métier dépendante.

---

# Partie 0.1 - Rôles et responsabilités

| ID | Décision V1 | Statut | Critère d'acceptation |
| --- | --- | --- | --- |
| R-01 | Les rôles publics sont `LEARNER` (Apprenant) et `TEACHER` (Formateur). | PROPOSÉ / À CONFIRMER | Un compte public possède un rôle principal et l'API applique ce rôle sur chaque action. |
| R-02 | Les rôles internes sont `SUPPORT`, `VERIFICATION`, `FINANCE`, `MODERATION`, `ADMIN` et `SUPER_ADMIN`. | PROPOSÉ / À CONFIRMER | Chaque rôle interne possède des permissions distinctes et testées. |
| R-03 | L'Apprenant recherche, crée un besoin, compare, choisit, réserve, paie, suit une session, évalue et peut réacheter. | PROPOSÉ / À CONFIRMER | Le parcours Apprenant complet est démontrable sur Web, API et Mobile. |
| R-04 | Le Formateur gère son profil, ses disponibilités, ses justificatifs, ses propositions, ses réservations, ses sessions, ses revenus et ses avis. | PROPOSÉ / À CONFIRMER | Le parcours Formateur ne donne aucune permission d'Apprenant par défaut. |
| R-05 | Le Support gère les comptes, demandes et réservations nécessaires à l'assistance, sans accès financier ni aux documents sensibles par défaut. | PROPOSÉ / À CONFIRMER | Une matrice de permissions et des tests d'isolation sont disponibles. |
| R-06 | La Vérification traite uniquement l'identité et les justificatifs professionnels nécessaires. | PROPOSÉ / À CONFIRMER | Les accès aux fichiers sont privés, temporaires et audités. |
| R-07 | La Finance traite paiements, remboursements, versements et litiges financiers. | PROPOSÉ / À CONFIRMER | Les données financières ne sont pas visibles par Support ou Vérification par défaut. |
| R-08 | La Modération traite profils, messages, propositions, réservations et avis signalés. | PROPOSÉ / À CONFIRMER | Les accès aux contenus signalés sont limités, temporaires si nécessaire et audités. |
| R-09 | L'Admin configure les référentiels, règles et permissions sans accès global implicite aux données opérationnelles. | PROPOSÉ / À CONFIRMER | Toute action privilégiée est journalisée. |
| R-10 | Le Super-admin est réservé aux actions exceptionnelles et doit être protégé par MFA. | PROPOSÉ / À CONFIRMER | MFA, audit et procédure d'accès exceptionnel sont testés avant production. |
| R-11 | Un compte public ne change pas de rôle silencieusement. Le changement est une action explicite et auditée. | PROPOSÉ / À CONFIRMER | L'ancien rôle ne conserve pas de permissions après changement validé. |
| R-12 | Les comptes peuvent être `ACTIVE`, `SUSPENDED` ou `DEACTIVATED`, avec des actions limitées selon le statut. | PROPOSÉ / À CONFIRMER | Un compte suspendu ou désactivé ne peut pas exécuter d'action métier protégée. |

**Décision nécessaire pour clôturer l'étape 0.1 :** approuver les rôles et la matrice de responsabilité, ou fournir les corrections dans la colonne de décision.

---

# Partie 0.2 - Référentiels et règles métier

## Référentiels éducatifs

| ID | Élément V1 | Valeurs proposées | Statut |
| --- | --- | --- | --- |
| E-01 | Niveaux | primaire ; secondaire ; humanités ; supérieur/universitaire ; professionnel et préparation aux certifications | PROPOSÉ / À CONFIRMER |
| E-02 | Matières | mathématiques ; français ; anglais ; physique ; chimie ; biologie/sciences ; informatique et bureautique ; programmation ; comptabilité et gestion ; statistiques et méthodologie de recherche | PROPOSÉ / À CONFIRMER |
| E-03 | Modes d'enseignement | `ONLINE` ; `HOME` ; `PUBLIC_PLACE` ; `TRAINING_CENTER` | PROPOSÉ / À CONFIRMER |
| E-04 | Zones | communes de Kinshasa, sans GPS exact ni adresse publique | PROPOSÉ / À CONFIRMER |
| E-05 | Administration | les référentiels sont stockés en base, actifs/inactifs, et modifiables sans migration métier | PROPOSÉ / À CONFIRMER |

## Règles générales V1

| ID | Décision | Statut | Conséquence attendue |
| --- | --- | --- | --- |
| M-01 | Devise transactionnelle : CDF. Les montants sont en Decimal ou chaîne décimale, jamais en float. | PROPOSÉ / À CONFIRMER | API, Web, Mobile, paiement, reçu et ledger affichent explicitement CDF. |
| M-02 | Fuseau métier : `Africa/Kinshasa`. Les dates API sont ISO 8601 avec fuseau. | PROPOSÉ / À CONFIRMER | Les créneaux, rappels et sessions sont interprétés dans ce fuseau. |
| M-03 | Téléphone non public. L'adresse exacte et le GPS ne sont jamais exposés publiquement. | PROPOSÉ / À CONFIRMER | Une zone approximative est affichée ; les coordonnées privées suivent une règle de réservation validée. |
| M-04 | Les services liés aux TFC, mémoires et travaux doivent respecter l'intégrité académique. | PROPOSÉ / À CONFIRMER | Tutorat, méthodologie, correction pédagogique et aide autorisée ; rédaction à la place de l'étudiant, fraude et plagiat interdits. |
| M-05 | Tout contenu contraire à l'intégrité académique peut être signalé, modéré et retiré. | PROPOSÉ / À CONFIRMER | Demandes, propositions et messages peuvent entrer dans le circuit de modération. |
| M-06 | Le matching est rule-based, explicable et ne favorise pas un statut Premium. | PROPOSÉ / À CONFIRMER | Les raisons du score sont retournées et les pondérations sont configurables. |
| M-07 | Le prestataire Mobile Money n'est pas encore choisi. | À CONFIRMER / BLOQUANT POUR PAIEMENT | L'intégration paiement ne peut pas être déclarée prête avant documentation sandbox, devise, signature webhook et règles de test. |
| M-08 | La commission pilote proposée est de 10 % du prix de la session terminée. | PROPOSÉ / À CONFIRMER | Le taux est configurable et figé dans la transaction concernée. |
| M-09 | La politique d'annulation proposée : gratuité Apprenant à 24 h ou plus ; cas tardifs et litiges soumis à examen manuel ; annulation Formateur avec remboursement intégral. | PROPOSÉ / À CONFIRMER | La politique est affichée avant confirmation et testée par cas limite. |
| M-10 | Les documents Formateur acceptés sont PDF, JPEG et PNG, avec limite initiale de 10 Mo, stockage privé et vérification humaine. | PROPOSÉ / À CONFIRMER | Les statuts sont `PENDING`, `APPROVED`, `REJECTED`, `EXPIRED`; un rejet est motivé. |
| M-11 | Les critères du pilote sont : 30 Formateurs complets, 100 Apprenants, 50 demandes qualifiées, 20 sessions terminées, 70 % de demandes avec proposition pertinente, 60 % des réservations confirmées terminées, 25 % de réachat, note moyenne 4/5 et litiges < 5 %. | PROPOSÉ / À CONFIRMER | Les KPI sont calculables depuis les événements métier et validés par le produit. |

**Décisions bloquantes restantes de l'étape 0.2 :** prestataire Mobile Money, règles financières définitives, liste des référentiels, politique d'intégrité académique et critères du pilote.

---

# Partie 0.3 - Parcours V1 accepté

## Parcours Apprenant

1. Inscription et choix du rôle Apprenant.
2. Vérification email et accès sécurisé.
3. Création ou complétion du profil.
4. Recherche et comparaison des Formateurs.
5. Création d'un besoin d'apprentissage.
6. Génération de matches explicables.
7. Réception et comparaison des propositions.
8. Acceptation d'une seule proposition.
9. Création et confirmation de la réservation.
10. Paiement CDF via Mobile Money.
11. Rappel, réalisation et suivi de la session.
12. Avis transactionnel.
13. Réservation à nouveau.

**Critère d'acceptation :** ce parcours doit être réalisable sur Web et Mobile, avec API commune, permissions objet, états d'erreur et reprise réseau.

## Parcours Formateur

1. Inscription et choix du rôle Formateur.
2. Vérification email.
3. Complétion du profil professionnel.
4. Dépôt et suivi des justificatifs.
5. Déclaration du tarif et des disponibilités.
6. Publication après satisfaction des prérequis.
7. Réception de demandes compatibles.
8. Envoi et suivi des propositions.
9. Échange avec l'Apprenant.
10. Confirmation et réalisation des sessions.
11. Consultation des revenus et versements.
12. Consultation et réponse aux avis selon la règle validée.

**Critère d'acceptation :** le Formateur ne peut pas utiliser les actions réservées à l'Apprenant et les transitions viennent du serveur.

## Parcours Admin et opérations

1. Connexion interne sécurisée.
2. Accès selon le rôle interne et le moindre privilège.
3. Supervision des comptes, demandes et réservations.
4. Traitement des vérifications.
5. Traitement des signalements et litiges.
6. Traitement des paiements, remboursements et versements.
7. Gestion des référentiels et paramètres autorisés.
8. Consultation des KPI et exports contrôlés.
9. Consultation des journaux d'audit.

**Critère d'acceptation :** chaque action Admin est autorisée par rôle, journalisée et testée ; aucune donnée sensible n'est visible par défaut à une équipe non habilitée.

## Pages et écrans indispensables V1

- [ ] Pages publiques : accueil, inscription, connexion, vérification email, mot de passe, recherche Formateurs et détail public.
- [ ] Apprenant : dashboard, profil, demandes, matches, comparaison, propositions, réservation, paiement, reçus, sessions, messagerie, notifications, avis et réachat.
- [ ] Formateur : dashboard, profil, publication, disponibilités, vérification, demandes matchées, propositions, réservations, sessions, messagerie, notifications, revenus, avis et paramètres.
- [ ] Admin : dashboard, comptes, vérification, modération, support, finance, référentiels, analytics et audit.

## Décisions reportées explicitement

- [ ] Prestataire Mobile Money précis.
- [ ] Taux de conversion CDF/USD et affichage USD éventuel.
- [ ] Automatisation des versements Formateur.
- [ ] Géolocalisation précise PostGIS.
- [ ] Abonnements Premium.
- [ ] Portail B2B.
- [ ] Intégration WhatsApp avancée.
- [ ] Machine learning et classement avancé.

---

# Validation du cadrage

| Élément | Réponse du porteur produit | Date | Statut |
| --- | --- | --- | --- |
| Rôles et responsabilités (0.1) | À compléter |  | À CONFIRMER |
| Référentiels et règles métier (0.2) | À compléter |  | À CONFIRMER |
| Parcours V1 et écrans obligatoires (0.3) | À compléter |  | À CONFIRMER |
| Prestataire Mobile Money | À compléter |  | BLOQUANT POUR PAIEMENT |
| Autorisation de passer à la Partie 1 | À compléter |  | BLOQUÉE |

## Format de validation

Pour valider, remplacer les réponses `À compléter` par une décision explicite, puis renseigner la date. Exemple : `Validé sans modification` ou `Validé avec les changements suivants : ...`.

La Partie 1 ne doit commencer qu'après validation de 0.1, 0.2 et 0.3.
