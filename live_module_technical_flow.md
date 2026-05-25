# Technical Deep Dive: NewsHub Live Module Architecture & Flow

This document outlines the technical workflow, function calls, and exact mechanisms that power the Live Module in the NewsHub project. The system relies on a hybrid architecture: **REST** for state management, **WebSockets (WS)** for signaling and chat, and **WebRTC** for peer-to-peer (P2P) video streaming.

---

## 1. Room Creation (State Management)
**Triggered by:** The Editor (Admin)
1. In the frontend, the editor navigates to the hub and fills out the creation form.
2. `LiveHubPageComponent.createLiveRoom()` is activated. *(Located in: `frontend/src/app/features/live/live-hub-page/live-hub-page.ts`)*
3. This triggers the HTTP service `LiveEventsService.create()` *(Located in: `frontend/src/app/core/services/live-events.ts`)* which sends a `POST /live-events` request.
4. The `create_live_event()` FastAPI endpoint processes the request. *(Located in: `backend/main.py`)*
5. It validates the user's role using the `ensure_editor()` dependency, instantiates a `models.LiveEvent` object (with status `"upcoming"`), commits it to MySQL via SQLAlchemy, and returns the serialized object. *(Models are located in: `backend/models.py`)*

---

## 2. Establishing the WebSocket Connection (Signaling Channel)
**Triggered by:** Any user (Editor or Viewer) joining the room.
1. When navigating to `/live/:id`, the Angular `LiveRoomPageComponent` initializes. *(Located in: `frontend/src/app/features/live/live-room-page/live-room-page.ts`)*
2. On `ngOnInit()`, it activates `LiveRoomSocketService.connect(roomId, token)`. *(Located in: `frontend/src/app/core/services/live-room-socket.ts`)*
3. This opens a `ws://` connection to the backend endpoint `@app.websocket("/ws/live-events/{event_id}")` which maps to the `live_event_socket()` function. *(Located in: `backend/main.py`)*
4. The backend verifies the JWT token and the user's access rights using `can_access_live_event()`. *(Located in: `backend/main.py`)*
5. `live_room_manager.connect()` is called. The `LiveRoomManager` class generates a unique `client_id` (UUID4) and stores the websocket instance in its memory dictionary `self.connections[room_id][client_id]`. *(Class located in: `backend/main.py`)*
6. The backend immediately activates `await live_room_manager.broadcast_viewer_count(event_id)` *(Located in: `backend/main.py`)* to update the UI for everyone in the room.

---

## 3. Going Live & Initializing Media (WebRTC Preparation)
**Triggered by:** The Editor clicking "Start Stream".
1. `LiveRoomPageComponent.startLiveRoom()` is activated *(Located in: `frontend/src/app/features/live/live-room-page/live-room-page.ts`)*, making a REST call to `POST /live-events/{id}/start` via `LiveEventsService.start()`.
2. The backend `start_live_event()` endpoint updates the database state to `"live"`. *(Located in: `backend/main.py`)*
3. Next, `LiveRoomPageComponent.goLiveWithCamera()` is invoked on the frontend. *(Located in: `frontend/src/app/features/live/live-room-page/live-room-page.ts`)*
4. This function requests hardware access via native browser APIs: `navigator.mediaDevices.getUserMedia({ video: true, audio: true })`.
5. The resulting `MediaStream` is attached to the local `<video>` HTML element (`this.localVideo.nativeElement.srcObject = stream`).
6. The Editor's socket emits a `{ type: 'broadcaster_ready' }` payload to the backend WebSocket using `LiveRoomSocketService.send()`.
7. `live_event_socket()` receives this payload and uses `live_room_manager.broadcast()` to relay it to all connected viewers. *(Located in: `backend/main.py`)*

---

## 4. The WebRTC Signaling Flow (Peer-to-Peer Handshake)
Because video streaming is too heavy for the backend, the backend simply acts as a **Signaling Server**. It passes messages between browsers so they can connect directly.

**Step A: Viewer creates an Offer**
1. Viewers receive the `'broadcaster_ready'` WS event.
2. `LiveRoomPageComponent.createViewerOffer()` is activated. *(Located in: `frontend/src/app/features/live/live-room-page/live-room-page.ts`)*
3. It creates a new `RTCPeerConnection` instance.
4. It calls `peerConnection.createOffer()`, sets it as the `LocalDescription`, and sends this SDP (Session Description Protocol) payload to the backend via WS: `{ type: 'offer', sdp: ... }`.

**Step B: Editor handles the Offer and creates an Answer**
1. The backend `live_event_socket()` receives the `'offer'` and routes it strictly to the Editor using `live_room_manager.send_to_client()`. *(Located in: `backend/main.py`)*
2. The Editor's frontend activates `LiveRoomPageComponent.handleViewerOffer()`. *(Located in: `frontend/src/app/features/live/live-room-page/live-room-page.ts`)*
3. It creates a dedicated `RTCPeerConnection` for that specific viewer.
4. It attaches its local `MediaStream` tracks to this connection (`peerConnection.addTrack(track, stream)`).
5. It sets the viewer's SDP as the `RemoteDescription`.
6. It generates an answer using `peerConnection.createAnswer()`, sets its own `LocalDescription`, and sends `{ type: 'answer', sdp: ... }` back to the backend.

**Step C: Viewer finalizes the connection**
1. The backend routes the `'answer'` back to the specific Viewer via `live_room_manager.send_to_client()`. *(Located in: `backend/main.py`)*
2. The Viewer receives it and activates `LiveRoomPageComponent.handleBroadcasterAnswer()`, setting it as the `RemoteDescription`. *(Located in: `frontend/src/app/features/live/live-room-page/live-room-page.ts`)*
3. **ICE Candidates:** During this process, both browsers discover their IP routes via STUN servers. They emit native `icecandidate` events, which trigger `LiveRoomPageComponent.sendIceCandidate()`. These are sent via WS (`{ type: 'ice_candidate' }`) and handled by `peerConnection.addIceCandidate()` on the other side.
4. Once connected, the native `ontrack` event fires on the Viewer's side, and the remote `MediaStream` is attached to their `<video>` element. **The P2P video connection is now live.**

---

## 5. Live Interaction: Chat & Updates
While the video bypasses the backend, the chat does not.
1. A user types a message and `LiveRoomPageComponent.sendChatMessage()` is activated. *(Located in: `frontend/src/app/features/live/live-room-page/live-room-page.ts`)*
2. It sends a `{ type: 'chat', content: '...' }` WS payload using `LiveRoomSocketService`.
3. In `backend/main.py`, the `live_event_socket()` endpoint intercepts the `'chat'` type.
4. It instantiates a `models.LiveMessage` object, commits it to the MySQL database (so it persists for late joiners). *(Model in: `backend/models.py`)*
5. It formats the message using the helper function `serialize_live_message()` *(Located in: `backend/main.py`)* and broadcasts it back to the room using `live_room_manager.broadcast()`.
6. (The same exact flow applies to Editor Updates, but with the type `'update'`, triggered by `LiveRoomPageComponent.publishEditorUpdate()`).

---

## 6. Teardown & Disconnection
**Triggered by:** The Editor ending the stream or a user closing the tab.
1. The Editor clicks End, activating `POST /live-events/{id}/end`. This triggers the `end_live_event()` endpoint. *(Located in: `backend/main.py`)*
2. The backend updates the DB state to `"ended"` and broadcasts a `{ type: 'stream_ended' }` WS event.
3. Viewers receive this event and trigger `LiveRoomPageComponent.cleanupConnections()`, which calls `peerConnection.close()` to kill the WebRTC video feeds. *(Located in: `frontend/src/app/features/live/live-room-page/live-room-page.ts`)*
4. When any user closes their tab, the WS connection drops natively, raising a `WebSocketDisconnect` exception in `backend/main.py` inside `live_event_socket()`.
5. The `except WebSocketDisconnect` block catches it, calls `live_room_manager.disconnect()` to remove the user from memory, and triggers `live_room_manager.broadcast_viewer_count()` to update the UI for remaining users.
