import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FavoritesService } from '../../../core/services/favorites';
import { NewsArticle } from '../../../core/models/news.model';
import { NewsCardComponent } from '../../../shared/components/news-card/news-card';
import { HeaderComponent } from '../../../shared/components/header/header';
import { FooterComponent } from '../../../shared/components/footer/footer';
import { Router } from '@angular/router';

@Component({
  selector: 'app-profile-page',
  standalone: true,
  imports: [CommonModule, NewsCardComponent, HeaderComponent, FooterComponent],
  templateUrl: './profile-page.html',
  styleUrl: './profile-page.css'
})
export class ProfilePageComponent implements OnInit {
  private favoritesService = inject(FavoritesService);
  private router = inject(Router);

  currentUser: any = null;
  savedArticles: NewsArticle[] = [];
  isLoading = true;

  ngOnInit() {
    const userJson = localStorage.getItem('currentUser');
    if (userJson) {
      this.currentUser = JSON.parse(userJson);
      this.loadFavorites();
    } else {
      this.router.navigate(['/login'], { queryParams: { returnUrl: '/profile' }});
    }
  }

  loadFavorites() {
    if (!this.currentUser?.id) return;
    
    this.favoritesService.getFavorites(this.currentUser.id).subscribe({
      next: (articles) => {
        this.savedArticles = articles;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Failed to load favorites', err);
        this.isLoading = false;
      }
    });
  }
}
