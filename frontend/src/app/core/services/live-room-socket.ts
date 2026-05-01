import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { environment } from '../../../environments/environment';
import { LiveSocketEvent } from '../models/live-event.model';

@Injectable({
  providedIn: 'root'
})
export class LiveRoomSocketService {
  private socket: WebSocket | null = null;
  private readonly eventsSubject = new Subject<LiveSocketEvent>();

  readonly events$: Observable<LiveSocketEvent> = this.eventsSubject.asObservable();

  connect(roomId: number, token: string): void {
    this.disconnect();

    const wsBaseUrl = environment.backendApiBaseUrl.replace(/^http/i, 'ws');
    const socketUrl = `${wsBaseUrl}/ws/live-events/${roomId}?token=${encodeURIComponent(token)}`;
    this.socket = new WebSocket(socketUrl);

    this.socket.onmessage = (event) => {
      const message = JSON.parse(event.data) as LiveSocketEvent;
      this.eventsSubject.next(message);
    };
  }

  send(payload: object): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      return;
    }

    this.socket.send(JSON.stringify(payload));
  }

  disconnect(): void {
    this.socket?.close();
    this.socket = null;
  }
}
