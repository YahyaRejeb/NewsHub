import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { AbstractControl, FormBuilder, ReactiveFormsModule, ValidationErrors, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';
import { NewsArticle } from '../../../core/models/news.model';
import { UserSession } from '../../../core/models/user.model';
import { AuthService } from '../../../core/services/auth/auth';
import { FavoritesService } from '../../../core/services/favorites';
import { ProfileService } from '../../../core/services/profile';
import { FooterComponent } from '../../../shared/components/footer/footer';
import { HeaderComponent } from '../../../shared/components/header/header';
import { NewsCardComponent } from '../../../shared/components/news-card/news-card';

@Component({
  selector: 'app-profile-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, NewsCardComponent, HeaderComponent, FooterComponent],
  templateUrl: './profile-page.html',
  styleUrl: './profile-page.css'
})
export class ProfilePageComponent implements OnInit {
  private readonly formBuilder = inject(FormBuilder);
  private readonly favoritesService = inject(FavoritesService);
  private readonly authService = inject(AuthService);
  private readonly profileService = inject(ProfileService);
  private readonly router = inject(Router);

  currentUser: UserSession | null = null;
  savedArticles: NewsArticle[] = [];
  isLoadingProfile = true;
  isLoadingFavorites = true;
  isSaving = false;
  loadError = '';
  saveError = '';
  successMessage = '';

  readonly profileForm = this.formBuilder.nonNullable.group(
    {
      firstName: ['', [Validators.required, Validators.minLength(2)]],
      lastName: ['', [Validators.required, Validators.minLength(2)]],
      email: ['', [Validators.required, Validators.email]],
      currentPassword: [''],
      newPassword: ['', [Validators.minLength(8)]],
      confirmPassword: ['']
    },
    { validators: [ProfilePageComponent.passwordValidator] }
  );

  ngOnInit(): void {
    const authenticatedUser = this.authService.currentUserValue as UserSession | null;

    if (!authenticatedUser?.id) {
      this.router.navigate(['/login'], { queryParams: { returnUrl: '/profile' } });
      return;
    }

    this.currentUser = authenticatedUser;
    this.patchForm(authenticatedUser);
    this.loadProfile(authenticatedUser.id);
    this.loadFavorites(authenticatedUser.id);
  }

  get initials(): string {
    if (!this.currentUser?.full_name) {
      return 'N';
    }

    return this.currentUser.full_name
      .split(' ')
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part.charAt(0).toUpperCase())
      .join('');
  }

  get savedArticlesCount(): number {
    return this.savedArticles.length;
  }

  get isPremiumUser(): boolean {
    return !!this.currentUser?.isPremium;
  }

  get premiumPlanLabel(): string {
    return this.currentUser?.premiumPlan ? this.currentUser.premiumPlan : 'free';
  }

  get profileCompletion(): number {
    const values = this.profileForm.getRawValue();
    const completedFields = [values.firstName, values.lastName, values.email].filter(
      (value) => value.trim().length > 0
    ).length;

    return Math.round((completedFields / 3) * 100);
  }

  get isBusy(): boolean {
    return this.isLoadingProfile || this.isSaving;
  }

  get firstNameControl(): AbstractControl<string, string> {
    return this.profileForm.controls.firstName;
  }

  get lastNameControl(): AbstractControl<string, string> {
    return this.profileForm.controls.lastName;
  }

  get emailControl(): AbstractControl<string, string> {
    return this.profileForm.controls.email;
  }

  get currentPasswordControl(): AbstractControl<string, string> {
    return this.profileForm.controls.currentPassword;
  }

  get newPasswordControl(): AbstractControl<string, string> {
    return this.profileForm.controls.newPassword;
  }

  get confirmPasswordControl(): AbstractControl<string, string> {
    return this.profileForm.controls.confirmPassword;
  }

  loadFavorites(userId: number): void {
    this.isLoadingFavorites = true;

    this.favoritesService
      .getFavorites(userId)
      .pipe(finalize(() => (this.isLoadingFavorites = false)))
      .subscribe({
        next: (articles) => {
          this.savedArticles = articles;
        },
        error: (error) => {
          console.error('Failed to load favorites', error);
        }
      });
  }

  saveProfile(): void {
    if (!this.currentUser?.id) {
      return;
    }

    this.successMessage = '';
    this.saveError = '';

    if (this.profileForm.invalid) {
      this.profileForm.markAllAsTouched();
      return;
    }

    const formValue = this.profileForm.getRawValue();
    const fullName = `${formValue.firstName} ${formValue.lastName}`.replace(/\s+/g, ' ').trim();
    const payload = {
      full_name: fullName,
      email: formValue.email.trim().toLowerCase(),
      current_password: formValue.currentPassword.trim() || undefined,
      new_password: formValue.newPassword.trim() || undefined
    };

    this.isSaving = true;

    this.profileService
      .updateProfile(this.currentUser.id, payload)
      .pipe(finalize(() => (this.isSaving = false)))
      .subscribe({
        next: (response) => {
          this.authService.setCurrentUser(response.user);
          this.currentUser = this.authService.currentUserValue;
          if (this.currentUser) {
            this.patchForm(this.currentUser);
          }
          this.successMessage = 'Your profile has been updated successfully.';
        },
        error: (error) => {
          this.saveError =
            error?.error?.detail ?? 'Unable to update your profile right now. Please try again.';
        }
      });
  }

  resetForm(): void {
    if (!this.currentUser) {
      return;
    }

    this.saveError = '';
    this.successMessage = '';
    this.patchForm(this.currentUser);
  }

  trackByArticle(_: number, article: NewsArticle): string {
    return article.url;
  }

  private loadProfile(userId: number): void {
    this.isLoadingProfile = true;
    this.loadError = '';

    this.profileService
      .getProfile(userId)
      .pipe(finalize(() => (this.isLoadingProfile = false)))
      .subscribe({
        next: (user) => {
          this.authService.setCurrentUser(user);
          this.currentUser = this.authService.currentUserValue;
          if (this.currentUser) {
            this.patchForm(this.currentUser);
          }
        },
        error: () => {
          this.loadError =
            'The latest profile data could not be loaded from the server. You can still edit the local session data.';
        }
      });
  }

  private patchForm(user: UserSession): void {
    const [firstName, ...lastNameParts] = user.full_name.trim().split(/\s+/);

    this.profileForm.reset(
      {
        firstName: firstName ?? '',
        lastName: lastNameParts.join(' '),
        email: user.email ?? '',
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      },
      { emitEvent: false }
    );
  }

  private static passwordValidator(control: AbstractControl): ValidationErrors | null {
    const currentPassword = control.get('currentPassword')?.value?.trim() ?? '';
    const newPassword = control.get('newPassword')?.value?.trim() ?? '';
    const confirmPassword = control.get('confirmPassword')?.value?.trim() ?? '';

    if (currentPassword && !newPassword) {
      return { newPasswordRequired: true };
    }

    if (newPassword && !currentPassword) {
      return { currentPasswordRequired: true };
    }

    if (newPassword && newPassword !== confirmPassword) {
      return { passwordMismatch: true };
    }

    return null;
  }
}
