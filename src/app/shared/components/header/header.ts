import { DOCUMENT, CommonModule } from '@angular/common';
import { Component, OnInit, inject, HostListener } from '@angular/core';
import { RouterLink, Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth/auth';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [RouterLink, CommonModule],
  templateUrl: './header.html',
  styleUrl: './header.css'
})
export class HeaderComponent implements OnInit {
  private readonly document = inject(DOCUMENT);
  private router = inject(Router);
  private authService = inject(AuthService);
  private readonly storageKey = 'f-news-theme';

  isDarkMode = false;
  currentUser: any = null;
  showProfileDropdown = false;

  ngOnInit(): void {
    const storedTheme = localStorage.getItem(this.storageKey);
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const resolvedTheme = storedTheme ?? (prefersDark ? 'dark' : 'light');

    this.isDarkMode = resolvedTheme === 'dark';
    this.applyTheme();

    this.authService.currentUser$.subscribe(user => {
      this.currentUser = user;
    });
  }

  logout(): void {
    this.authService.logout();
    this.showProfileDropdown = false;
    this.router.navigate(['/']);
  }

  toggleProfileDropdown(): void {
    this.showProfileDropdown = !this.showProfileDropdown;
  }

  closeDropdown(): void {
    this.showProfileDropdown = false;
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    const target = event.target as HTMLElement;
    if (!target.closest('.profile-box-container')) {
      this.closeDropdown();
    }
  }

  toggleTheme(): void {
    this.isDarkMode = !this.isDarkMode;
    this.applyTheme();
    localStorage.setItem(this.storageKey, this.isDarkMode ? 'dark' : 'light');
  }

  private applyTheme(): void {
    this.document.documentElement.setAttribute('data-theme', this.isDarkMode ? 'dark' : 'light');
  }
}