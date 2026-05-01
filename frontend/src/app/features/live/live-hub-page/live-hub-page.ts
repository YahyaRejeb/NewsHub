import { CommonModule, NgClass, TitleCasePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';
import { LiveEvent } from '../../../core/models/live-event.model';
import { UserSession } from '../../../core/models/user.model';
import { AuthService } from '../../../core/services/auth/auth';
import { LiveEventsService } from '../../../core/services/live-events';
import { FooterComponent } from '../../../shared/components/footer/footer';
import { HeaderComponent } from '../../../shared/components/header/header';

@Component({
  selector: 'app-live-hub-page',
  standalone: true,
  imports: [
    CommonModule,
    FooterComponent,
    HeaderComponent,
    NgClass,
    ReactiveFormsModule,
    RouterLink,
    TitleCasePipe
  ],
  templateUrl: './live-hub-page.html',
  styleUrl: './live-hub-page.css'
})
export class LiveHubPageComponent implements OnInit {
  private readonly authService = inject(AuthService);
  private readonly liveEventsService = inject(LiveEventsService);
  private readonly formBuilder = inject(FormBuilder);
  private readonly router = inject(Router);

  currentUser: UserSession | null = null;
  liveEvents: LiveEvent[] = [];
  loading = true;
  error = '';
  createError = '';
  isCreating = false;
  deletingEventId: number | null = null;

  readonly categories = [
    'technology',
    'business',
    'politics',
    'science',
    'entertainment',
    'sports',
    'health'
  ];

  readonly createForm = this.formBuilder.nonNullable.group({
    title: ['', [Validators.required, Validators.minLength(4)]],
    description: ['', [Validators.required, Validators.minLength(12)]],
    category: ['technology', [Validators.required]],
    coverImage: [''],
    premiumOnly: [true]
  });

  ngOnInit(): void {
    this.authService.currentUser$.subscribe((user) => {
      this.currentUser = user;
    });

    this.loadLiveEvents();
  }

  get isEditor(): boolean {
    return this.currentUser?.role === 'editor';
  }

  isOwnedByCurrentEditor(event: LiveEvent): boolean {
    return !!this.currentUser && this.isEditor && event.editor_user_id === this.currentUser.id;
  }

  createLiveRoom(): void {
    if (!this.isEditor) {
      return;
    }

    this.createError = '';

    if (this.createForm.invalid) {
      this.createForm.markAllAsTouched();
      return;
    }

    const formValue = this.createForm.getRawValue();
    this.isCreating = true;

    this.liveEventsService
      .createLiveEvent({
        title: formValue.title.trim(),
        description: formValue.description.trim(),
        category: formValue.category,
        cover_image: formValue.coverImage.trim() || null,
        premium_only: formValue.premiumOnly
      })
      .pipe(finalize(() => (this.isCreating = false)))
      .subscribe({
        next: (event) => {
          this.createForm.reset(
            {
              title: '',
              description: '',
              category: 'technology',
              coverImage: '',
              premiumOnly: true
            },
            { emitEvent: false }
          );
          void this.router.navigate(['/live', event.id]);
        },
        error: (error) => {
          this.createError = error.error?.detail || 'The live room could not be created right now.';
        }
      });
  }

  deleteLiveRoom(event: LiveEvent): void {
    if (!this.isOwnedByCurrentEditor(event)) {
      return;
    }

    const confirmed = window.confirm(
      `Delete "${event.title}"? This will remove the room and all its live messages.`
    );
    if (!confirmed) {
      return;
    }

    this.deletingEventId = event.id;

    this.liveEventsService
      .deleteLiveEvent(event.id)
      .pipe(finalize(() => (this.deletingEventId = null)))
      .subscribe({
        next: () => {
          this.liveEvents = this.liveEvents.filter((item) => item.id !== event.id);
        },
        error: (error) => {
          this.error = error.error?.detail || 'The live room could not be deleted right now.';
        }
      });
  }

  private loadLiveEvents(): void {
    this.loading = true;
    this.error = '';

    this.liveEventsService
      .getLiveEvents()
      .pipe(finalize(() => (this.loading = false)))
      .subscribe({
        next: (events) => {
          this.liveEvents = events;
        },
        error: () => {
          this.error = 'The live hub could not be loaded right now.';
        }
      });
  }
}
