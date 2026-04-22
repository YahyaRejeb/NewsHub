import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private currentUserSubject: BehaviorSubject<any>;
  public currentUser$: Observable<any>;

  constructor() {
    const storedUser = localStorage.getItem('currentUser');
    this.currentUserSubject = new BehaviorSubject<any>(storedUser ? JSON.parse(storedUser) : null);
    this.currentUser$ = this.currentUserSubject.asObservable();
  }

  public get currentUserValue(): any {
    return this.currentUserSubject.value;
  }

  public getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  setAuthData(user: any, token?: string): void {
    if (user) {
      localStorage.setItem('currentUser', JSON.stringify(user));
      if (token) {
        localStorage.setItem('access_token', token);
      }
    } else {
      localStorage.removeItem('currentUser');
      localStorage.removeItem('access_token');
    }
    this.currentUserSubject.next(user);
  }

  logout(): void {
    this.setAuthData(null);
  }
}
