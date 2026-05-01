import { CommonModule, DatePipe, NgClass, TitleCasePipe } from '@angular/common';
import {
  AfterViewInit,
  Component,
  ElementRef,
  OnDestroy,
  OnInit,
  ViewChild,
  inject
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Subscription, finalize } from 'rxjs';
import {
  LiveEventDetail,
  LiveMessage,
  LiveSocketEvent
} from '../../../core/models/live-event.model';
import { UserSession } from '../../../core/models/user.model';
import { AuthService } from '../../../core/services/auth/auth';
import { LiveEventsService } from '../../../core/services/live-events';
import { LiveRoomSocketService } from '../../../core/services/live-room-socket';
import { FooterComponent } from '../../../shared/components/footer/footer';
import { HeaderComponent } from '../../../shared/components/header/header';

@Component({
  selector: 'app-live-room-page',
  standalone: true,
  imports: [
    CommonModule,
    DatePipe,
    FooterComponent,
    FormsModule,
    HeaderComponent,
    NgClass,
    RouterLink,
    TitleCasePipe
  ],
  templateUrl: './live-room-page.html',
  styleUrl: './live-room-page.css'
})
export class LiveRoomPageComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('localVideo') localVideoRef?: ElementRef<HTMLVideoElement>;
  @ViewChild('remoteVideo') remoteVideoRef?: ElementRef<HTMLVideoElement>;

  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly authService = inject(AuthService);
  private readonly liveEventsService = inject(LiveEventsService);
  private readonly liveRoomSocketService = inject(LiveRoomSocketService);

  private authSubscription?: Subscription;
  private socketSubscription?: Subscription;
  private localStream: MediaStream | null = null;
  private remoteStream: MediaStream | null = null;
  private readonly broadcasterPeerConnections = new Map<string, RTCPeerConnection>();
  private viewerPeerConnection: RTCPeerConnection | null = null;

  currentUser: UserSession | null = null;
  event: LiveEventDetail | null = null;
  updates: LiveMessage[] = [];
  chatMessages: LiveMessage[] = [];
  loading = true;
  error = '';
  connectionLabel = 'Offline';
  streamMessage = 'Waiting for the live stream to start.';
  editorUpdateText = '';
  chatText = '';
  loadingAction = false;
  isDeletingRoom = false;
  cameraError = '';
  socketClientId = '';
  isSocketReady = false;
  isSocketConnecting = false;
  isBroadcasting = false;
  isCameraPrepared = false;
  hasRequestedViewerConnection = false;
  loginReturnUrl = '';

  ngOnInit(): void {
    this.loginReturnUrl = this.router.url;
    this.socketSubscription = this.liveRoomSocketService.events$.subscribe((event) => {
      void this.handleSocketEvent(event);
    });

    this.authSubscription = this.authService.currentUser$.subscribe((user) => {
      this.currentUser = user;
      if (!user) {
        this.disconnectSocket();
        return;
      }

      this.attemptSocketConnection();
    });

    const eventId = Number(this.route.snapshot.paramMap.get('id'));
    if (!eventId) {
      this.error = 'Live room not found.';
      this.loading = false;
      return;
    }

    this.loadLiveRoom(eventId);
  }

  ngAfterViewInit(): void {
    this.bindLocalStream();
    this.bindRemoteStream();
  }

  ngOnDestroy(): void {
    this.authSubscription?.unsubscribe();
    this.socketSubscription?.unsubscribe();
    this.stopCameraBroadcast({ keepRoomLive: true });
    this.disconnectSocket();
  }

  get isPremiumUser(): boolean {
    return !!this.currentUser?.isPremium;
  }

  get isEditor(): boolean {
    return this.currentUser?.role === 'editor';
  }

  get isRoomEditor(): boolean {
    return !!this.currentUser && !!this.event && this.currentUser.id === this.event.editor_user_id && this.isEditor;
  }

  get canJoinLiveRoom(): boolean {
    if (!this.currentUser || !this.event) {
      return false;
    }

    if (this.isRoomEditor) {
      return true;
    }

    return this.event.premium_only ? this.isPremiumUser : true;
  }

  get showLoginGate(): boolean {
    return !this.currentUser;
  }

  get showPremiumGate(): boolean {
    return !!this.currentUser && !!this.event && !this.canJoinLiveRoom;
  }

  get canSendChat(): boolean {
    return this.isSocketReady && this.canJoinLiveRoom;
  }

  get hasRemoteStream(): boolean {
    return !!this.remoteStream;
  }

  async prepareCamera(): Promise<void> {
    if (!this.isRoomEditor) {
      return;
    }

    try {
      this.cameraError = '';
      if (!this.localStream) {
        this.localStream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: true
        });
      }

      this.isCameraPrepared = true;
      this.streamMessage = this.event?.status === 'live'
        ? 'Camera is ready. Go live when you are comfortable.'
        : 'Camera preview is ready. Start the room when the event begins.';
      this.bindLocalStream();
    } catch {
      this.cameraError = 'The webcam or microphone could not be opened.';
    }
  }

  startLiveRoom(): void {
    if (!this.event || !this.isRoomEditor) {
      return;
    }

    this.loadingAction = true;
    this.liveEventsService
      .startLiveEvent(this.event.id)
      .pipe(finalize(() => (this.loadingAction = false)))
      .subscribe({
        next: (event) => {
          if (this.event) {
            this.event = {
              ...this.event,
              ...event
            };
          }
          this.streamMessage = 'The room is now live. Start broadcasting when ready.';
        },
        error: (error) => {
          this.error = error.error?.detail || 'The live room could not be started.';
        }
      });
  }

  async goLiveWithCamera(): Promise<void> {
    if (!this.event || !this.isRoomEditor) {
      return;
    }

    if (!this.isCameraPrepared) {
      await this.prepareCamera();
    }

    if (!this.localStream) {
      return;
    }

    this.isBroadcasting = true;
    this.streamMessage = 'Broadcasting live from your camera.';
    this.liveRoomSocketService.send({ type: 'broadcaster_ready' });
  }

  endLiveRoom(): void {
    if (!this.event || !this.isRoomEditor) {
      return;
    }

    this.loadingAction = true;
    this.stopCameraBroadcast({ keepRoomLive: false });

    this.liveEventsService
      .endLiveEvent(this.event.id)
      .pipe(finalize(() => (this.loadingAction = false)))
      .subscribe({
        next: (event) => {
          if (this.event) {
            this.event = {
              ...this.event,
              ...event
            };
          }
          this.streamMessage = 'This live session has ended.';
        },
        error: (error) => {
          this.error = error.error?.detail || 'The live room could not be ended.';
        }
      });
  }

  deleteLiveRoom(): void {
    if (!this.event || !this.isRoomEditor) {
      return;
    }

    const confirmed = window.confirm(
      `Delete "${this.event.title}"? This will remove the room and all its live messages.`
    );
    if (!confirmed) {
      return;
    }

    this.isDeletingRoom = true;
    this.stopCameraBroadcast({ keepRoomLive: false });
    this.disconnectSocket();

    this.liveEventsService
      .deleteLiveEvent(this.event.id)
      .pipe(finalize(() => (this.isDeletingRoom = false)))
      .subscribe({
        next: () => {
          void this.router.navigate(['/live']);
        },
        error: (error) => {
          this.error = error.error?.detail || 'The live room could not be deleted.';
        }
      });
  }

  publishEditorUpdate(): void {
    const content = this.editorUpdateText.trim();
    if (!content || !this.isRoomEditor || !this.isSocketReady) {
      return;
    }

    this.liveRoomSocketService.send({
      type: 'live_update',
      content
    });
    this.editorUpdateText = '';
  }

  sendChatMessage(): void {
    const content = this.chatText.trim();
    if (!content || !this.canSendChat) {
      return;
    }

    this.liveRoomSocketService.send({
      type: 'chat_message',
      content
    });
    this.chatText = '';
  }

  private loadLiveRoom(eventId: number): void {
    this.loading = true;
    this.error = '';

    this.liveEventsService
      .getLiveEventById(eventId)
      .pipe(finalize(() => (this.loading = false)))
      .subscribe({
        next: (event) => {
          this.event = event;
          this.updates = [...event.updates].reverse();
          this.chatMessages = [...event.chat_messages];
          this.streamMessage =
            event.status === 'live'
              ? 'The room is live. Wait for the editor video to connect.'
              : event.status === 'ended'
                ? 'This live session has ended.'
                : 'The editor has not started the live session yet.';
          this.attemptSocketConnection();
        },
        error: () => {
          this.error = 'Unable to load this live room right now.';
        }
      });
  }

  private attemptSocketConnection(): void {
    if (!this.event || !this.currentUser || !this.canJoinLiveRoom || this.isSocketReady || this.isSocketConnecting) {
      return;
    }

    const token = this.authService.getToken();
    if (!token) {
      return;
    }

    this.connectionLabel = 'Connecting...';
    this.isSocketConnecting = true;
    this.liveRoomSocketService.connect(this.event.id, token);
  }

  private disconnectSocket(): void {
    this.isSocketReady = false;
    this.isSocketConnecting = false;
    this.socketClientId = '';
    this.connectionLabel = 'Offline';
    this.liveRoomSocketService.disconnect();
  }

  private async handleSocketEvent(event: LiveSocketEvent): Promise<void> {
    if (!this.event) {
      return;
    }

    if (event.type === 'socket_ready') {
      this.socketClientId = event.clientId;
      this.isSocketReady = true;
      this.isSocketConnecting = false;
      this.connectionLabel = 'Connected';
      this.event = {
        ...this.event,
        viewer_count: event.viewerCount,
        status: event.status
      };

      if (!this.isRoomEditor && this.event.status === 'live') {
        this.requestViewerConnection();
      }
      return;
    }

    if (event.type === 'viewer_count') {
      this.event = {
        ...this.event,
        viewer_count: event.viewerCount
      };
      return;
    }

    if (event.type === 'room_status') {
      this.event = {
        ...this.event,
        status: event.status
      };

      if (event.status === 'live') {
        this.streamMessage = this.isRoomEditor
          ? 'The room is live. Start the camera broadcast whenever you are ready.'
          : 'The room is live. Waiting for the editor camera stream.';
        this.requestViewerConnection();
      } else if (event.status === 'ended') {
        this.streamMessage = 'This live session has ended.';
        this.clearRemoteViewerState();
      }
      return;
    }

    if (event.type === 'chat_message') {
      this.chatMessages = [...this.chatMessages, event.message];
      return;
    }

    if (event.type === 'live_update') {
      this.updates = [event.message, ...this.updates];
      return;
    }

    if (event.type === 'broadcaster_ready') {
      if (!this.isRoomEditor && this.event.status === 'live') {
        this.hasRequestedViewerConnection = false;
        this.requestViewerConnection();
      }
      return;
    }

    if (event.type === 'viewer_joined' && this.isRoomEditor && this.isBroadcasting) {
      await this.createOfferForViewer(event.senderClientId);
      return;
    }

    if (event.type === 'offer' && !this.isRoomEditor) {
      await this.handleViewerOffer(event.senderClientId, event.sdp);
      return;
    }

    if (event.type === 'answer' && this.isRoomEditor) {
      const peerConnection = this.broadcasterPeerConnections.get(event.senderClientId);
      if (!peerConnection) {
        return;
      }

      await peerConnection.setRemoteDescription(new RTCSessionDescription(event.sdp));
      return;
    }

    if (event.type === 'ice_candidate') {
      if (this.isRoomEditor) {
        const peerConnection = this.broadcasterPeerConnections.get(event.senderClientId);
        if (!peerConnection) {
          return;
        }

        await peerConnection.addIceCandidate(new RTCIceCandidate(event.candidate));
        return;
      }

      if (this.viewerPeerConnection) {
        await this.viewerPeerConnection.addIceCandidate(new RTCIceCandidate(event.candidate));
      }
      return;
    }

    if (event.type === 'stream_ended') {
      this.streamMessage = 'The editor has stopped the camera stream.';
      this.clearRemoteViewerState();
    }
  }

  private requestViewerConnection(): void {
    if (this.isRoomEditor || !this.isSocketReady || this.hasRequestedViewerConnection) {
      return;
    }

    this.hasRequestedViewerConnection = true;
    this.liveRoomSocketService.send({
      type: 'viewer_joined'
    });
  }

  private async createOfferForViewer(targetClientId: string): Promise<void> {
    if (!this.localStream) {
      return;
    }

    const peerConnection = this.createBroadcasterPeerConnection(targetClientId);
    const offer = await peerConnection.createOffer();
    await peerConnection.setLocalDescription(offer);

    this.liveRoomSocketService.send({
      type: 'offer',
      targetClientId,
      sdp: offer
    });
  }

  private createBroadcasterPeerConnection(targetClientId: string): RTCPeerConnection {
    const existing = this.broadcasterPeerConnections.get(targetClientId);
    if (existing) {
      return existing;
    }

    const peerConnection = new RTCPeerConnection({
      iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
    });

    this.localStream?.getTracks().forEach((track) => {
      peerConnection.addTrack(track, this.localStream!);
    });

    peerConnection.onicecandidate = (event) => {
      if (!event.candidate) {
        return;
      }

      this.liveRoomSocketService.send({
        type: 'ice_candidate',
        targetClientId,
        candidate: event.candidate.toJSON()
      });
    };

    this.broadcasterPeerConnections.set(targetClientId, peerConnection);
    return peerConnection;
  }

  private async handleViewerOffer(senderClientId: string, sdp: RTCSessionDescriptionInit): Promise<void> {
    const peerConnection = this.createViewerPeerConnection(senderClientId);
    await peerConnection.setRemoteDescription(new RTCSessionDescription(sdp));

    const answer = await peerConnection.createAnswer();
    await peerConnection.setLocalDescription(answer);

    this.liveRoomSocketService.send({
      type: 'answer',
      targetClientId: senderClientId,
      sdp: answer
    });
  }

  private createViewerPeerConnection(targetClientId: string): RTCPeerConnection {
    if (this.viewerPeerConnection) {
      return this.viewerPeerConnection;
    }

    this.viewerPeerConnection = new RTCPeerConnection({
      iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
    });

    this.viewerPeerConnection.ontrack = (event) => {
      this.remoteStream = event.streams[0] ?? null;
      this.bindRemoteStream();
      this.streamMessage = 'Connected to the editor video stream.';
    };

    this.viewerPeerConnection.onicecandidate = (event) => {
      if (!event.candidate) {
        return;
      }

      this.liveRoomSocketService.send({
        type: 'ice_candidate',
        targetClientId,
        candidate: event.candidate.toJSON()
      });
    };

    return this.viewerPeerConnection;
  }

  private stopCameraBroadcast(options: { keepRoomLive: boolean }): void {
    if (this.isBroadcasting || this.localStream) {
      this.liveRoomSocketService.send({ type: 'stream_ended' });
    }

    this.isBroadcasting = false;
    this.isCameraPrepared = false;
    this.closeBroadcasterPeerConnections();

    this.localStream?.getTracks().forEach((track) => track.stop());
    this.localStream = null;

    if (this.localVideoRef?.nativeElement) {
      this.localVideoRef.nativeElement.srcObject = null;
    }

    if (!options.keepRoomLive) {
      this.streamMessage = 'The camera stream has stopped.';
    }
  }

  private closeBroadcasterPeerConnections(): void {
    this.broadcasterPeerConnections.forEach((peerConnection) => peerConnection.close());
    this.broadcasterPeerConnections.clear();
  }

  private clearRemoteViewerState(): void {
    this.hasRequestedViewerConnection = false;
    this.viewerPeerConnection?.close();
    this.viewerPeerConnection = null;
    this.remoteStream = null;

    if (this.remoteVideoRef?.nativeElement) {
      this.remoteVideoRef.nativeElement.srcObject = null;
    }
  }

  private bindLocalStream(): void {
    if (!this.localVideoRef?.nativeElement || !this.localStream) {
      return;
    }

    this.localVideoRef.nativeElement.srcObject = this.localStream;
    void this.localVideoRef.nativeElement.play().catch(() => undefined);
  }

  private bindRemoteStream(): void {
    if (!this.remoteVideoRef?.nativeElement || !this.remoteStream) {
      return;
    }

    this.remoteVideoRef.nativeElement.srcObject = this.remoteStream;
    void this.remoteVideoRef.nativeElement.play().catch(() => undefined);
  }
}
