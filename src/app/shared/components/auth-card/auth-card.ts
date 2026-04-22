import { Component, inject, ChangeDetectorRef, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RegisterForm } from '../register-form/register-form';
import { InterestsForm } from '../interests-form/interests-form';
import { LoginForm } from '../login-form/login-form';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth/auth';

@Component({
  selector: 'app-auth-card',
  standalone: true,
  imports: [CommonModule, RegisterForm, InterestsForm, LoginForm],
  templateUrl: './auth-card.html',
  styleUrls: ['./auth-card.css']
})
export class AuthCard implements OnInit {
  private http = inject(HttpClient);
  private cdr = inject(ChangeDetectorRef);
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private authService = inject(AuthService);

  step = 1;
  mode: 'login' | 'signup' = 'login';
  registrationData: any = null;
  isLoading = false;
  errorMessage = '';
  successUser: any = null;
  returnUrl = '/';

  ngOnInit(): void {
    // Detect mode from route path
    const path = this.router.url;
    this.returnUrl = this.route.snapshot.queryParamMap.get('returnUrl') || '/';

    if (path.includes('register')) {
      this.mode = 'signup';
    } else {
      this.mode = 'login';
    }
  }

  goToNextStep(data: any) {
    console.log("Registration data collected:", data);
    this.registrationData = data;
    this.step = 2;
    this.cdr.detectChanges();
  }

  finishSignup(interestIds: number[]) {
    if (!this.registrationData) return;

    this.isLoading = true;
    this.errorMessage = '';
    this.cdr.detectChanges();
    
    const payload = {
      ...this.registrationData,
      interest_ids: interestIds
    };

    this.http.post('http://127.0.0.1:8000/complete-signup', payload).subscribe({
      next: (responseData: any) => {
        this.isLoading = false;
        console.log("Signup complete! Auto logging in...");
        // Create user object based on registration
        const user = {
          id: responseData.user_id,
          full_name: this.registrationData.full_name,
          email: this.registrationData.email
        };
        this.authService.setAuthData(user, responseData.access_token);
        this.router.navigate(['/']);
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = err.error?.detail || 'An error occurred during signup. Please try again.';
        console.error("Error completing signup:", err);
        this.cdr.detectChanges();
      }
    });
  }

  onLoginSuccess(res: any) {
    this.successUser = res.user;
    this.authService.setAuthData(res.user, res.access_token);
    this.router.navigateByUrl('/');
  }

  switchToSignup() {
    this.router.navigate(['/register']);
    this.mode = 'signup';
    this.step = 1;
    this.errorMessage = '';
    this.cdr.detectChanges();
  }

  switchToLogin() {
    this.router.navigate(['/login']);
    this.mode = 'login';
    this.step = 1;
    this.errorMessage = '';
    this.cdr.detectChanges();
  }
}