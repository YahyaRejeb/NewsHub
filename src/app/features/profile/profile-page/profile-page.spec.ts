import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { AuthService } from '../../../core/services/auth/auth';
import { FavoritesService } from '../../../core/services/favorites';
import { ProfileService } from '../../../core/services/profile';
import { ProfilePageComponent } from './profile-page';

describe('ProfilePageComponent', () => {
  let component: ProfilePageComponent;
  let fixture: ComponentFixture<ProfilePageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProfilePageComponent],
      providers: [
        provideRouter([]),
        {
          provide: AuthService,
          useValue: {
            currentUserValue: { id: 1, full_name: 'Jane Doe', email: 'jane@example.com', interests: [] },
            currentUser$: of({ id: 1, full_name: 'Jane Doe', email: 'jane@example.com', interests: [] }),
            setCurrentUser: jasmine.createSpy('setCurrentUser')
          }
        },
        {
          provide: FavoritesService,
          useValue: {
            getFavorites: () => of([])
          }
        },
        {
          provide: ProfileService,
          useValue: {
            getProfile: () => of({ id: 1, full_name: 'Jane Doe', email: 'jane@example.com', interests: [] }),
            updateProfile: () =>
              of({
                message: 'Profile updated successfully',
                user: { id: 1, full_name: 'Jane Doe', email: 'jane@example.com', interests: [] }
              })
          }
        }
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ProfilePageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
