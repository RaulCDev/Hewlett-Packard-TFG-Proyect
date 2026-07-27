export interface Game {
  appId: string;
  title: string;
  url: string;
  imgUrl: string;
  released?: string;
  reviewSummary?: string | null;
  originalPrice?: string | null;
  discountedPrice?: string | null;
}

export interface IntegrationStatus {
  service: 'google' | 'rapidapi';
  configured: boolean;
  source?: 'rapidapi' | 'fixture';
  missingCredentials: string[];
  fallbackReason?: 'missing_credentials' | 'live_api_unavailable';
}
