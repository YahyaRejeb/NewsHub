import { Injectable, inject } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { UserProfile, UserSession } from '../../models/user.model';
import { PremiumService } from '../premium';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly premiumService = inject(PremiumService);
  private currentUserSubject: BehaviorSubject<UserSession | null>;
  public currentUser$: Observable<UserSession | null>;

  constructor() {
    const storedUser = localStorage.getItem('currentUser');
    const parsedUser = storedUser ? (JSON.parse(storedUser) as UserProfile | UserSession) : null;
    this.currentUserSubject = new BehaviorSubject<UserSession | null>(
      this.premiumService.decorateUser(parsedUser)
    );
    this.currentUser$ = this.currentUserSubject.asObservable();
  }

  public get currentUserValue(): UserSession | null {
    return this.currentUserSubject.value;
  }

  setCurrentUser(user: UserProfile | UserSession | null): void {
    const decoratedUser = this.premiumService.decorateUser(user);

    if (decoratedUser) {
      localStorage.setItem('currentUser', JSON.stringify(decoratedUser));
    } else {
      localStorage.removeItem('currentUser');
    }

    this.currentUserSubject.next(decoratedUser);
  }

  logout(): void {
    this.setCurrentUser(null);
  }

  refreshCurrentUser(): void {
    this.setCurrentUser(this.currentUserSubject.value);
  }
}
