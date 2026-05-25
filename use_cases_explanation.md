# 🌐 NewsHub : Explication des Cas d'Utilisation (Détaillée)

Ce document explique le fonctionnement technique des quatre fonctionnalités principales de notre site web. Pour chaque cas d'utilisation, nous détaillons le flux de données précis entre le **Frontend** (Angular) et le **Backend** (FastAPI).

---

## 1. 👤 Créer un compte (Sign Up)

Permet à un nouvel utilisateur de s'inscrire en fournissant ses informations et ses intérêts.

### 🔄 Flux de données détaillé
1.  **Saisie** : L'utilisateur remplit son nom, email, mot de passe et choisit jusqu'à 3 intérêts.
2.  **Vérification (Frontend)** :
    *   La fonction `finishSignup` (📁 `frontend/src/app/shared/components/auth-card/`) envoie d'abord une requête **GET** à `/check-email/{email}` pour s'assurer que le compte n'existe pas déjà.
3.  **Envoi des données** :
    *   Si l'email est disponible, le Frontend envoie une requête **HTTP POST** vers `/complete-signup`.
    *   **📦 Payload (Données envoyées)** : Un objet JSON contenant : `full_name`, `email`, `password`, `interest_ids`.
4.  **Traitement (Backend)** :
    *   La fonction `complete_signup` (📁 `backend/`) reçoit ces données.
    *   Le mot de passe est sécurisé avec `hash_password` (📁 `backend/`) qui transforme le texte clair en une empreinte sécurisée.
    *   Un nouvel objet `User` est créé et enregistré dans la base de données.
5.  **Réponse** : Le serveur renvoie un objet contenant un `access_token` et les infos de l'utilisateur.

### 🛠️ Localisation des Fonctions
*   **Frontend : `finishSignup()`**
    *   📂 Dossier : `frontend/src/app/shared/components/auth-card/`
    *   📄 Fichier : `auth-card.ts`
*   **Backend : `complete_signup()`**
    *   📂 Dossier : `backend/`
    *   📄 Fichier : `main.py`
*   **Backend : `hash_password()`**
    *   📂 Dossier : `backend/`
    *   📄 Fichier : `security.py`

---

## 2. 🔑 Se connecter (Log In)

Permet à un utilisateur de s'authentifier pour accéder à ses préférences.

### 🔄 Flux de données détaillé
1.  **Saisie** : L'utilisateur entre son email et son mot de passe.
2.  **Envoi** : La fonction `onSubmit` (📁 `frontend/src/app/shared/components/login-form/`) déclenche une requête **HTTP POST** vers `/login`.
3.  **Vérification (Backend)** :
    *   La fonction `login` (📁 `backend/`) cherche l'utilisateur dans la base de données.
    *   Elle utilise `verify_password` (📁 `backend/`) pour comparer le mot de passe saisi avec celui stocké.
4.  **Réponse** :
    *   **Succès** : Le serveur génère un jeton JWT avec `create_access_token` (📁 `backend/`) et renvoie le jeton.
    *   Le Frontend stocke ce jeton via `setAuthData` (📁 `frontend/src/app/core/services/auth/`) pour maintenir la session.

### 🛠️ Localisation des Fonctions
*   **Frontend : `onSubmit()`**
    *   📂 Dossier : `frontend/src/app/shared/components/login-form/`
    *   📄 Fichier : `login-form.ts`
*   **Backend : `login()`**
    *   📂 Dossier : `backend/`
    *   📄 Fichier : `main.py`
*   **Backend : `verify_password()` & `create_access_token()`**
    *   📂 Dossier : `backend/`
    *   📄 Fichier : `security.py`
*   **Frontend : `setAuthData()`**
    *   📂 Dossier : `frontend/src/app/core/services/auth/`
    *   📄 Fichier : `auth.ts`

---

## 3. 📰 Consulter le fil d'actualité (News Feed)

C'est ici que l'on récupère les articles depuis une source externe pour les afficher sur le site. Imaginez un pont entre le site de nouvelles et votre navigateur.

### 🔄 Le voyage de l'information (Data Flow)

1.  **Le Départ (Frontend)** : Dès que vous ouvrez le site, le `NewsService` s'active. La fonction `fetchNewsStore` prépare la demande. Elle appelle `requestNewsApi` qui va toquer à la porte de notre Backend.
2.  **Le Relais (Backend)** : Notre serveur reçoit la demande via la fonction `get_news_feed`. 
    *   *Pourquoi passer par lui ?* Parce que pour obtenir les nouvelles, il faut une "Clé API" (un code secret payant). Si on mettait ce code dans le Frontend, n'importe qui pourrait nous le voler. Le Backend garde cette clé secrète.
3.  **L'Appel Externe** : Le Backend utilise sa clé secrète pour appeler le site **NewsData.io** (le vrai fournisseur de nouvelles).
4.  **Le Retour** : NewsData envoie une grosse liste de données brutes (JSON) au Backend, qui les renvoie aussitôt au Frontend.
5.  **La Préparation (Frontend)** : Les données reçues sont "brutes" (parfois mal rangées). Le Frontend utilise alors `mapArticle` pour :
    *   Formater les dates.
    *   Choisir la bonne image.
    *   Nettoyer le texte.
6.  **L'Arrivée** : Les articles sont enfin affichés joliment sur votre écran !

### 🛠️ Localisation des Fonctions
*   **Frontend : `fetchNewsStore()`** (Prépare la demande globale)
    *   📂 Dossier : `frontend/src/app/core/services/` | 📄 Fichier : `news.ts`
*   **Frontend : `requestNewsApi()`** (Fait l'appel HTTP vers le Backend)
    *   📂 Dossier : `frontend/src/app/core/services/` | 📄 Fichier : `news.ts`
*   **Backend : `get_news_feed()`** (Fait le pont avec l'API externe et cache la clé secrète)
    *   📂 Dossier : `backend/` | 📄 Fichier : `main.py`
*   **Frontend : `mapArticle()`** (Transforme les données brutes en articles lisibles)
    *   📂 Dossier : `frontend/src/app/core/services/` | 📄 Fichier : `news.ts`

---

## 4. 🔍 Filtrer l'actualité (Filter News)

Affinement des résultats selon des critères précis.

### 🔄 Flux de données détaillé
1.  **Action** : L'utilisateur sélectionne un filtre (ex: Pays "France").
2.  **Envoi** : Le Frontend envoie une requête **HTTP GET** vers `/news-feed` avec des paramètres comme `?country=fr`.
3.  **Traitement (Backend)** :
    *   La fonction `get_news_feed` (📁 `backend/`) transmet ces paramètres à l'API externe.
4.  **Filtrage Local** : La fonction `applyFilters` (📁 `frontend/src/app/core/services/`) permet aussi de trier instantanément les articles déjà chargés pour une meilleure réactivité.

### 🛠️ Localisation des Fonctions
*   **Frontend : `applyFilters()`**
    *   📂 Dossier : `frontend/src/app/core/services/`
    *   📄 Fichier : `news.ts`
*   **Backend : `get_news_feed()`**
    *   📂 Dossier : `backend/`
    *   📄 Fichier : `main.py`

---

## 5. 💬 Commenter une actualité (Comment News)

Permet aux utilisateurs de donner leur avis sur un article spécifique.

### 🔄 Flux de données détaillé
1.  **Saisie** : L'utilisateur écrit un commentaire sous un article.
2.  **Envoi** : La fonction `addComment` (📁 `frontend/src/app/core/services/`) envoie une requête **HTTP POST** vers `/comments`.
    *   **📦 Payload** : L'ID de l'utilisateur, l'objet complet de l'article, et le texte du commentaire.
3.  **Traitement (Backend)** :
    *   La fonction `add_comment` (📁 `backend/`) vérifie d'abord si l'article existe déjà dans notre base locale (via `upsert_news_record`).
    *   Elle enregistre ensuite le commentaire lié à cet article et à l'utilisateur.
4.  **Réponse** : Le serveur confirme l'ajout et renvoie l'ID du nouveau commentaire.

### 🛠️ Localisation des Fonctions
*   **Frontend : `addComment()`**
    *   📂 Dossier : `frontend/src/app/core/services/` | 📄 Fichier : `comments.ts`
*   **Backend : `add_comment()`**
    *   📂 Dossier : `backend/` | 📄 Fichier : `main.py`
*   **Backend : `upsert_news_record()`** (Fonction utilitaire pour gérer l'article en base)
    *   📂 Dossier : `backend/` | 📄 Fichier : `crud.py`

---

## 6. 📁 Enregistrer une actualité (Save / Favorite)

Permet de mettre un article de côté pour le relire plus tard.

### 🔄 Flux de données détaillé
1.  **Action** : L'utilisateur clique sur l'icône "Favoris" (marque-page).
2.  **Envoi** : La fonction `saveArticle` (📁 `frontend/src/app/core/services/`) envoie une requête **HTTP POST** vers `/favorites`.
    *   **📦 Payload** : `user_id` et les détails de l'article.
3.  **Traitement (Backend)** :
    *   La fonction `save_favorite` (📁 `backend/`) crée ou met à jour un lien de "favori" entre l'utilisateur et l'article.
4.  **Affichage** : Plus tard, l'utilisateur peut voir sa liste via la fonction `getFavorites` qui appelle **GET** `/favorites/{user_id}`.

### 🛠️ Localisation des Fonctions
*   **Frontend : `saveArticle()` & `getFavorites()`**
    *   📂 Dossier : `frontend/src/app/core/services/` | 📄 Fichier : `favorites.ts`
*   **Backend : `save_favorite()` & `get_favorites()`**
    *   📂 Dossier : `backend/` | 📄 Fichier : `main.py`

---

## 7. 🏗️ Créer une Room (Create Live Room)

C'est ici que l'on transforme des intentions utilisateur en données persistantes. Le voyage d'un simple clic vers une ligne en base de données suit un cycle de transformation rigoureux.

### 🔄 Cycle de Transformation des Données (Détaillé)

1.  **Capture (Angular Reactive Forms)** :
    *   L'interface utilise un `FormGroup` (📁 `frontend/.../live-hub-page.ts`) qui lie chaque champ HTML (titre, description) à des objets `FormControl`. 
    *   Cela permet une validation en temps réel (ex: `Validators.required`).

2.  **Extraction & Normalisation (Frontend)** :
    *   Lors du clic sur "Créer", la méthode `getRawValue()` extrait les données brutes. 
    *   Elles sont ensuite "mappées" vers un objet de type `CreateLiveEventPayload`. C'est là qu'on effectue le **Trimming** (suppression des espaces inutiles) et que les chaînes vides sont transformées en `null`.

3.  **Sérialisation (JSON Over HTTP)** :
    *   Le service `HttpClient` d'Angular transforme cet objet JavaScript en une chaîne de caractères au format **JSON**.
    *   Cette chaîne est placée dans le corps (Body) d'une requête **HTTP POST**.

4.  **Désérialisation & Validation (FastAPI / Pydantic)** :
    *   À la réception, le Backend utilise un schéma **Pydantic** (`CreateLiveEventRequest`). 
    *   Pydantic vérifie la structure, les types de données (ex: s'assurer que `premium_only` est un booléen) et rejette la requête si elle est malformée avant même qu'elle ne touche la logique métier.

5.  **Mapping ORM (SQLAlchemy)** :
    *   La fonction `create_live_event` instancie un modèle **SQLAlchemy** (`models.LiveEvent`). 
    *   C'est ici que l'on fusionne les données du formulaire avec des données système, comme l'ID de l'utilisateur connecté (`current_user.id`) et le statut par défaut (`upcoming`).

6.  **Persistance (SQL Insert)** :
    *   L'appel à `db.add()` place l'objet dans la session de base de données.
    *   `db.commit()` génère l'instruction SQL `INSERT INTO live_events (...)` qui écrit définitivement les données sur le disque dur du serveur de base de données.

### 🛠️ Localisation des Fonctions & Fichiers
*   **Frontend : `createForm` & `createLiveRoom()`**
    *   📂 Dossier : `frontend/src/app/features/live/live-hub-page/` | 📄 Fichier : `live-hub-page.ts`
*   **Backend : `CreateLiveEventRequest` (Schéma de validation)**
    *   📂 Dossier : `backend/` | 📄 Fichier : `schemas.py`
*   **Backend : `create_live_event()` (Logique métier & ORM)**
    *   📂 Dossier : `backend/` | 📄 Fichier : `main.py`
*   **Backend : `models.LiveEvent` (Modèle de base de données)**
    *   📂 Dossier : `backend/` | 📄 Fichier : `models.py`

---

## 8. 🤝 Rejoindre une Room (Analyse Technique Exhaustive)

Le système de "Live" est une prouesse d'ingénierie combinant synchronisation d'état et streaming haute performance. Voici le parcours complet de la donnée, fonction par fonction.

### 🔄 Le Parcours pas-à-pas du Flux de Données

#### Étape 1 : Initialisation du Tunnel (WebSocket)
*   **Action** : L'utilisateur ouvre la page.
*   **Frontend (`attemptSocketConnection`)** (📁 `frontend/src/app/features/live/live-room-page/` | 📄 `live-room-page.ts`) : Récupère le jeton JWT et appelle `LiveRoomSocketService.connect()`.
*   **Protocole** : Ouverture d'une socket **TCP** vers le Backend.
*   **Backend (`live_event_socket`)** (📁 `backend/` | 📄 `main.py`) : Authentifie l'utilisateur, accepte la connexion et l'enregistre via `live_room_manager.connect()`.

#### Étape 2 : Préparation Média (Côté Éditeur)
*   **Frontend (`prepareCamera`)** (📁 `frontend/src/app/features/live/live-room-page/` | 📄 `live-room-page.ts`) : Utilise l'API native `navigator.mediaDevices.getUserMedia()` pour accéder au flux matériel (Webcam/Micro).
*   **Frontend (`bindLocalStream`)** (📁 `frontend/src/app/features/live/live-room-page/` | 📄 `live-room-page.ts`) : Attache le flux à l'élément `<video>` local pour que l'éditeur se voie.

#### Étape 3 : Négociation WebRTC (Le "Signaling")
C'est ici que le WebSocket sert de messager pour que les deux PC s'accordent.
1.  **Notification (`viewer_joined`)** : Un spectateur arrive et envoie ce signal au Backend via `requestViewerConnection()`.
2.  **Création de l'Offre (`createOfferForViewer`)** (📁 `frontend/src/app/features/live/live-room-page/` | 📄 `live-room-page.ts`) : L'éditeur crée une instance de `RTCPeerConnection`. Il génère un **SDP (Offer)** qui décrit ses codecs vidéo.
3.  **Relais Backend (`send_to_client`)** (📁 `backend/` | 📄 `main.py`) : Le Backend reçoit l'offre et l'envoie **uniquement** au spectateur concerné.
4.  **Réponse du Spectateur (`handleViewerOffer`)** (📁 `frontend/src/app/features/live/live-room-page/` | 📄 `live-room-page.ts`) : Le spectateur reçoit l'offre, l'accepte via `setRemoteDescription()`, crée une **`answer`** et la renvoie à l'éditeur.
5.  **Échange de Candidats (`onicecandidate`)** : Les deux PC s'envoient leurs adresses IP via le signal `ice_candidate`.

#### Étape 4 : Le Flux Vidéo Direct (UDP) - Le "Bypass" du Backend
C'est ici que réside la magie de l'architecture WebRTC.

> [!IMPORTANT]
> **Le Backend ne touche jamais à la vidéo.** 
> Contrairement au Chat ou au Compteur de spectateurs, les gigaoctets de données vidéo circulent en **Peer-to-Peer (P2P)**. Le fichier `main.py` de votre serveur ne reçoit, ne traite, et ne renvoie aucune image.

*   **Le Rôle du Navigateur** : Une fois la négociation terminée, le navigateur active son moteur **UDP**.
*   **Transport Direct** : Les paquets vidéo voyagent de l'adresse IP de l'éditeur vers l'adresse IP du spectateur sans passer par votre serveur FastAPI.
*   **Frontend Spectateur (`ontrack`)** : Cet événement se déclenche dès que les premiers paquets vidéo arrivent par ce tunnel direct. Il appelle `bindRemoteStream()` (📁 `frontend/src/app/features/live/live-room-page/` | 📄 `live-room-page.ts`) pour afficher la vidéo.

#### Étape 5 : Interaction Temps Réel (Chat & Compteur)
*   **Envoi Chat (`sendChatMessage`)** (📁 `frontend/src/app/features/live/live-room-page/` | 📄 `live-room-page.ts`) : Utilise `liveRoomSocketService.send()`.
*   **Diffusion (`broadcast`)** (📁 `backend/` | 📄 `main.py`) : Ici, les données **passent par le Backend** car ce sont des messages de contrôle légers qui doivent être synchronisés pour tout le monde.

### 🛠️ Cartographie des Fonctions

| Rôle | Frontend (`live-room-page.ts`) | Backend (`main.py`) |
| :--- | :--- | :--- |
| **Signalisation** | `handleSocketEvent()` | `live_event_socket()` |
| **Gestion Sockets** | `LiveRoomSocketService.connect()` | `LiveRoomManager.connect()` |
| **WebRTC Éditeur** | `createBroadcasterPeerConnection()` | *(Relais via Signaling)* |
| **WebRTC Spectateur** | `createViewerPeerConnection()` | *(Relais via Signaling)* |
| **Transport Vidéo** | `peerConnection.addTrack()` | *(Protocole UDP direct)* |
| **Mise à jour État** | `broadcast_viewer_count()` | `broadcast()` |

---

### 💡 Synthèse des Protocoles
*   **TCP** : Géré par les fonctions de `LiveRoomSocketService`. Assure que les messages de chat et de signalisation arrivent sans erreur.
*   **UDP** : Géré par l'objet natif `RTCPeerConnection`. Assure que la vidéo est fluide avec une latence proche de zéro.
