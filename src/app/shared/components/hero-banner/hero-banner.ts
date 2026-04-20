import { AuthService } from '../../../core/services/auth/auth';
import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-hero-banner',
  standalone: true,
  imports: [RouterLink, CommonModule],
  templateUrl: './hero-banner.html',
  styleUrl: './hero-banner.css'
})
export class HeroBannerComponent implements OnInit {
  private authService = inject(AuthService);
  isLoggedIn = false;

  ngOnInit(): void {
    this.authService.currentUser$.subscribe(user => {
      this.isLoggedIn = !!user;
    });
  }
}