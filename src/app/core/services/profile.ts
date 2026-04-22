import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  UpdateProfilePayload,
  UpdateProfileResponse,
  UserProfile
} from '../models/user.model';

@Injectable({
  providedIn: 'root'
})
export class ProfileService {
  private readonly http = inject(HttpClient);
  private readonly apiBaseUrl = environment.backendApiBaseUrl;

  getProfile(userId: number): Observable<UserProfile> {
    return this.http.get<UserProfile>(`${this.apiBaseUrl}/users/${userId}`);
  }

  updateProfile(userId: number, payload: UpdateProfilePayload): Observable<UpdateProfileResponse> {
    return this.http.put<UpdateProfileResponse>(`${this.apiBaseUrl}/users/${userId}/profile`, payload);
  }
}
