import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  CreateLiveEventPayload,
  LiveEvent,
  LiveEventDetail,
} from '../models/live-event.model';

@Injectable({
  providedIn: 'root'
})
export class LiveEventsService {
  private readonly http = inject(HttpClient);
  private readonly apiBaseUrl = `${environment.backendApiBaseUrl}/live-events`;

  getLiveEvents(): Observable<LiveEvent[]> {
    return this.http.get<LiveEvent[]>(this.apiBaseUrl);
  }

  getLiveEventById(eventId: number): Observable<LiveEventDetail> {
    return this.http.get<LiveEventDetail>(`${this.apiBaseUrl}/${eventId}`);
  }

  createLiveEvent(payload: CreateLiveEventPayload): Observable<LiveEvent> {
    return this.http.post<LiveEvent>(this.apiBaseUrl, payload);
  }

  startLiveEvent(eventId: number): Observable<LiveEvent> {
    return this.http.post<LiveEvent>(`${this.apiBaseUrl}/${eventId}/start`, {});
  }

  endLiveEvent(eventId: number): Observable<LiveEvent> {
    return this.http.post<LiveEvent>(`${this.apiBaseUrl}/${eventId}/end`, {});
  }

  deleteLiveEvent(eventId: number): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.apiBaseUrl}/${eventId}`);
  }
}
