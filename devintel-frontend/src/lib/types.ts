export interface User {
  id: number;
  email: string | null;
  full_name: string | null;
  github_username: string | null;
  avatar_url: string | null;
  is_verified: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RefreshResponse {
  access_token: string;
  token_type: string;
}

export interface ApiError {
  detail: string;
  errors?: Array<{ field: string; message: string }>;
}

export interface SignupPayload {
  email: string;
  password: string;
  full_name?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}
