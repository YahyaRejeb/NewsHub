export interface UserProfile {
  id: number;
  full_name: string;
  email: string;
  interests: PreferredNewsCategory[];
}

export type PremiumPlan = 'monthly' | 'annual';

export interface PremiumMembership {
  isPremium: boolean;
  premiumPlan: PremiumPlan | null;
  premiumSince: string | null;
  paymentLast4?: string | null;
}

export interface UserSession extends UserProfile, PremiumMembership {}

export type PreferredNewsCategory =
  | 'technology'
  | 'business'
  | 'politics'
  | 'science'
  | 'entertainment'
  | 'sports'
  | 'health';

export interface UpdateProfilePayload {
  full_name: string;
  email: string;
  current_password?: string;
  new_password?: string;
}

export interface UpdateProfileResponse {
  message: string;
  user: UserProfile;
}

export interface PremiumCheckoutPayload {
  plan: PremiumPlan;
  cardholderName: string;
  cardNumber: string;
  expiry: string;
  cvc: string;
}
