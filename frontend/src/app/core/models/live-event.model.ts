export type LiveEventStatus = 'upcoming' | 'live' | 'ended';

export interface LiveMessage {
  id: number;
  message_type: 'chat' | 'update';
  content: string;
  created_at: string | null;
  user_id: number;
  user_name: string;
}

export interface LiveEvent {
  id: number;
  title: string;
  description: string;
  category: string;
  cover_image: string | null;
  stream_url: string | null;
  status: LiveEventStatus;
  premium_only: boolean;
  viewer_count: number;
  editor_user_id: number | null;
  editor_name: string | null;
  created_at: string | null;
  started_at: string | null;
  ended_at: string | null;
}

export interface LiveEventDetail extends LiveEvent {
  updates: LiveMessage[];
  chat_messages: LiveMessage[];
}

export interface CreateLiveEventPayload {
  title: string;
  description: string;
  category: string;
  cover_image?: string | null;
  stream_url?: string | null;
  premium_only: boolean;
}

export type LiveSocketEvent =
  | {
      type: 'socket_ready';
      clientId: string;
      viewerCount: number;
      status: LiveEventStatus;
      isEditor: boolean;
    }
  | {
      type: 'viewer_count';
      viewerCount: number;
    }
  | {
      type: 'room_status';
      status: LiveEventStatus;
    }
  | {
      type: 'chat_message';
      message: LiveMessage;
    }
  | {
      type: 'live_update';
      message: LiveMessage;
    }
  | {
      type: 'broadcaster_ready';
      senderClientId: string;
    }
  | {
      type: 'viewer_joined';
      senderClientId: string;
    }
  | {
      type: 'offer';
      senderClientId: string;
      sdp: RTCSessionDescriptionInit;
    }
  | {
      type: 'answer';
      senderClientId: string;
      sdp: RTCSessionDescriptionInit;
    }
  | {
      type: 'ice_candidate';
      senderClientId: string;
      candidate: RTCIceCandidateInit;
    }
  | {
      type: 'stream_ended';
    };
