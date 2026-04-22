import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  ArticleBrief,
  ChatHistoryTurn,
  ChatbotReply
} from '../models/chatbot.model';
import { NewsArticle } from '../models/news.model';

@Injectable({
  providedIn: 'root'
})
export class ChatbotService {
  private readonly http = inject(HttpClient);
  private readonly apiBaseUrl = environment.backendApiBaseUrl;

  getArticleBrief(article: NewsArticle): Observable<ArticleBrief> {
    return this.http.post<ArticleBrief>(`${this.apiBaseUrl}/chatbot/article-brief`, {
      article: this.mapArticle(article)
    });
  }

  askChatbot(
    article: NewsArticle,
    message: string,
    history: ChatHistoryTurn[]
  ): Observable<ChatbotReply> {
    return this.http.post<ChatbotReply>(`${this.apiBaseUrl}/chatbot/ask`, {
      article: this.mapArticle(article),
      message,
      history
    });
  }

  private mapArticle(article: NewsArticle) {
    return {
      article_id: article.id,
      title: article.title,
      description: article.description,
      content: article.content,
      image_url: article.imageUrl,
      source_url: article.url,
      source_name: article.sourceName,
      published_at: article.publishedAt,
      category: article.category
    };
  }
}
