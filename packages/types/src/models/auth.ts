/** Auth-related types matching Django API v2 responses. */

export interface AuthUser {
  id: number;
  email: string;
}

export interface MemberProfile {
  id: string;
  member_number: string;
  first_name: string;
  last_name: string;
  full_name: string;
  email: string;
  phone: string;
  role: string;
  membership_status: string;
  photo: string | null;
  has_full_access: boolean;
  is_staff_member: boolean;
  two_factor_enabled: boolean;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  password_confirm: string;
  first_name?: string;
  last_name?: string;
  invitation_code?: string;
}

export interface LoginResponse extends AuthTokens {
  user: AuthUser;
  member: MemberProfile | null;
}

export interface RegisterResponse extends LoginResponse {}

export interface MeResponse {
  user: AuthUser;
  member: MemberProfile | null;
}

export interface RefreshRequest {
  refresh: string;
}

export interface RefreshResponse {
  access: string;
  refresh?: string;
}

export interface LogoutRequest {
  refresh: string;
}

export interface MeUpdateRequest {
  first_name?: string;
  last_name?: string;
  phone?: string;
  phone_secondary?: string;
  birth_date?: string;
  address?: string;
  city?: string;
  province?: string;
  postal_code?: string;
  family_status?: string;
}
