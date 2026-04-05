import { DatePipe, NgIf, TitleCasePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { NewsCategory } from '../../../core/models/category.model';
import { NewsArticle } from '../../../core/models/news.model';
import { FavoritesService } from '../../../core/services/favorites';
import { NewsService } from '../../../core/services/news';
import { HeaderComponent } from '../../../shared/components/header/header';

@Component({
  selector: 'app-news-details-page',
  standalone: true,
  imports: [DatePipe, HeaderComponent, NgIf, RouterLink, TitleCasePipe],
  templateUrl: './news-details-page.html',
  styleUrl: './news-details-page.css'
})
export class NewsDetailsPageComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly newsService = inject(NewsService);
  private readonly favoritesService = inject(FavoritesService);

  article: NewsArticle | null = null;
  loading = true;
  error = '';
  saveError = '';
  isSaving = false;
  isSaved = false;

  ngOnInit(): void {
    const articleId = this.route.snapshot.paramMap.get('id');
    const categoryParam = this.route.snapshot.queryParamMap.get('category') as
      | Exclude<NewsCategory, 'all'>
      | null;
    const stateArticle = (window.history.state?.article as NewsArticle | undefined) ?? null;

    if (!articleId) {
      this.error = 'Article not found.';
      this.loading = false;
      return;
    }

    if (stateArticle && stateArticle.id === articleId) {
      this.article = stateArticle;
      this.loading = false;
      this.loadSavedState();
      return;
    }

    this.newsService.getArticleById(articleId, categoryParam ?? undefined).subscribe({
      next: (article) => {
        this.article = article;
        this.error = article ? '' : 'Article not found.';
        this.loading = false;
        this.loadSavedState();
      },
      error: () => {
        this.error = 'Unable to load article details right now.';
        this.loading = false;
      }
    });
  }

  toggleSaveArticle(): void {
    if (!this.article) {
      return;
    }

    const userId = this.getCurrentUserId();
    if (!userId) {
      this.router.navigate(['/login']);
      return;
    }

    if (!this.article.url || this.article.url === '#') {
      this.saveError = 'This article cannot be saved because the source URL is missing.';
      return;
    }

    this.saveError = '';
    this.isSaving = true;

    if (this.isSaved) {
      this.favoritesService.removeArticle(userId, this.article.url).subscribe({
        next: () => {
          this.isSaved = false;
          this.isSaving = false;
        },
        error: () => {
          this.saveError = 'Unable to remove the article right now.';
          this.isSaving = false;
        }
      });
      return;
    }

    this.favoritesService.saveArticle(userId, this.article).subscribe({
      next: () => {
        this.isSaved = true;
        this.isSaving = false;
      },
      error: () => {
        this.saveError = 'Unable to save the article right now.';
        this.isSaving = false;
      }
    });
  }

  private getCurrentUserId(): number | null {
    const storedUser = localStorage.getItem('currentUser');
    if (!storedUser) {
      return null;
    }

    try {
      const parsed = JSON.parse(storedUser) as { id?: unknown };
      const numericId = typeof parsed.id === 'number' ? parsed.id : Number(parsed.id);
      return Number.isFinite(numericId) ? numericId : null;
    } catch {
      return null;
    }
  }

  private loadSavedState(): void {
    const userId = this.getCurrentUserId();
    if (!this.article || !userId || !this.article.url || this.article.url === '#') {
      this.isSaved = false;
      return;
    }

    this.favoritesService.isArticleSaved(userId, this.article.url).subscribe((saved) => {
      this.isSaved = saved;
    });
  }
}
