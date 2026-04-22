export interface ChatbotEvidence {
  chunk_id: string;
  text: string;
  score: number;
}

export interface ArticleBrief {
  title: string;
  sourceName: string;
  publishedAt: string | null;
  summary: string;
  longSummary: string;
  whyItMatters: string;
  keyPoints: string[];
  people: string[];
  organizations: string[];
  places: string[];
  dates: string[];
  importantNumbers: string[];
  timeline: string[];
  suggestedQuestions: string[];
  limitations: string[];
  blocked: boolean;
}

export interface ChatHistoryTurn {
  role: 'user' | 'assistant';
  content: string;
  mode: 'grounded' | 'general';
}

export interface ChatbotReply {
  mode: 'grounded' | 'general';
  route: string;
  answer: string;
  evidence: ChatbotEvidence[];
  confidence: number;
  limitations: string[];
  cached: boolean;
}

export interface AssistantMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  mode: 'user' | 'grounded' | 'general';
  route?: string;
  evidence?: ChatbotEvidence[];
  confidence?: number;
  limitations?: string[];
  cached?: boolean;
  createdAt: string;
}
