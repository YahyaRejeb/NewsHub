import { DatePipe, DecimalPipe, NgFor, NgIf } from '@angular/common';
import {
  Component,
  ElementRef,
  Input,
  OnChanges,
  SimpleChanges,
  ViewChild,
  inject
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import {
  ArticleBrief,
  AssistantMessage,
  ChatHistoryTurn,
  ChatbotReply
} from '../../../core/models/chatbot.model';
import { NewsArticle } from '../../../core/models/news.model';
import { ChatbotService } from '../../../core/services/chatbot';

interface QuickAction {
  label: string;
  prompt: string;
}

@Component({
  selector: 'app-article-assistant-panel',
  standalone: true,
  imports: [DatePipe, DecimalPipe, FormsModule, NgFor, NgIf],
  templateUrl: './article-assistant-panel.html',
  styleUrl: './article-assistant-panel.css'
})
export class ArticleAssistantPanelComponent implements OnChanges {
  @Input({ required: true }) article!: NewsArticle;
  @ViewChild('conversationScroller') private conversationScroller?: ElementRef<HTMLDivElement>;

  private readonly chatbotService = inject(ChatbotService);

  brief: ArticleBrief | null = null;
  messages: AssistantMessage[] = [];
  draft = '';
  loadingBrief = false;
  briefError = '';
  chatError = '';
  sending = false;

  readonly quickActions: QuickAction[] = [
    { label: 'Summarize this', prompt: 'Summarize this article for me.' },
    { label: 'Why does it matter?', prompt: 'Why does this article matter?' },
    { label: 'Key facts', prompt: 'What are the key facts in this story?' },
    { label: 'Explain simply', prompt: 'Explain this article in simple terms.' },
    { label: 'Who is involved?', prompt: 'Who is involved in this article?' }
  ];

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['article']?.currentValue) {
      this.resetPanel();
      this.loadBrief();
    }
  }

  submitMessage(): void {
    const message = this.draft.trim();
    if (!message || this.sending) {
      return;
    }

    this.draft = '';
    this.sendMessage(message);
  }

  askQuickAction(prompt: string): void {
    if (this.sending) {
      return;
    }

    this.sendMessage(prompt);
  }

  applySuggestedQuestion(question: string): void {
    if (this.sending) {
      return;
    }

    this.sendMessage(question);
  }

  trackByMessage(_: number, message: AssistantMessage): string {
    return message.id;
  }

  trackByValue(_: number, value: string): string {
    return value;
  }

  trackByQuickAction(_: number, action: QuickAction): string {
    return action.label;
  }

  trackByEvidence(_: number, evidence: { chunk_id: string }): string {
    return evidence.chunk_id;
  }

  private resetPanel(): void {
    this.brief = null;
    this.messages = [];
    this.draft = '';
    this.loadingBrief = false;
    this.briefError = '';
    this.chatError = '';
    this.sending = false;
  }

  private loadBrief(): void {
    this.loadingBrief = true;
    this.briefError = '';

    this.chatbotService.getArticleBrief(this.article).subscribe({
      next: (brief) => {
        this.brief = brief;
        this.loadingBrief = false;
      },
      error: () => {
        this.brief = this.buildFallbackBrief();
        this.briefError =
          'Using the article preview while the full assistant brief catches up.';
        this.loadingBrief = false;
      }
    });
  }

  private sendMessage(message: string): void {
    const history = this.buildHistory();
    const userMessage = this.createUserMessage(message);
    this.messages = [...this.messages, userMessage];
    this.chatError = '';
    this.sending = true;
    this.scrollConversationToBottom();

    this.chatbotService.askChatbot(this.article, message, history).subscribe({
      next: (reply) => {
        this.messages = [...this.messages, this.createAssistantMessage(reply)];
        this.sending = false;
        this.scrollConversationToBottom();
      },
      error: () => {
        this.messages = [
          ...this.messages,
          {
            id: this.buildId('assistant'),
            role: 'assistant',
            content:
              "I couldn't answer just now. Please try again in a moment, and I'll re-check the article.",
            mode: 'general',
            limitations: ['The assistant request failed before a full response was generated.'],
            createdAt: new Date().toISOString()
          }
        ];
        this.chatError = 'The assistant request failed.';
        this.sending = false;
        this.scrollConversationToBottom();
      }
    });
  }

  private buildHistory(): ChatHistoryTurn[] {
    return this.messages.slice(-6).map((message) => ({
      role: message.role,
      content: message.content,
      mode: message.mode === 'grounded' ? 'grounded' : 'general'
    }));
  }

  private createUserMessage(content: string): AssistantMessage {
    return {
      id: this.buildId('user'),
      role: 'user',
      content,
      mode: 'user',
      createdAt: new Date().toISOString()
    };
  }

  private createAssistantMessage(reply: ChatbotReply): AssistantMessage {
    return {
      id: this.buildId('assistant'),
      role: 'assistant',
      content: reply.answer,
      mode: reply.mode,
      route: reply.route,
      evidence: reply.evidence,
      confidence: reply.confidence,
      limitations: reply.limitations,
      cached: reply.cached,
      createdAt: new Date().toISOString()
    };
  }

  private buildFallbackBrief(): ArticleBrief {
    const summary = this.article.description || this.article.content || this.article.title;
    const longSummary = this.article.content || this.article.description || this.article.title;

    return {
      title: this.article.title,
      sourceName: this.article.sourceName,
      publishedAt: this.article.publishedAt,
      summary,
      longSummary,
      whyItMatters:
        'This story matters because it captures the main development and gives you a quick way to understand the latest update.',
      keyPoints: [summary].filter(Boolean),
      people: [],
      organizations: [],
      places: [],
      dates: [],
      importantNumbers: [],
      timeline: [],
      suggestedQuestions: this.quickActions.map((action) => action.prompt),
      limitations: ['The original article could not be fully processed yet.'],
      blocked: this.article.url === '#'
    };
  }

  private buildId(prefix: string): string {
    return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
  }

  private scrollConversationToBottom(): void {
    queueMicrotask(() => {
      const container = this.conversationScroller?.nativeElement;
      if (!container) {
        return;
      }

      container.scrollTop = container.scrollHeight;
    });
  }
}
