/** Member-related types matching Django Member model. */
import type { Role, MembershipStatusType, FamilyStatusType, ProvinceType, PrivacyLevelType } from '../constants';

export interface MemberListItem {
  id: string;
  member_number: string;
  first_name: string;
  last_name: string;
  full_name: string;
  email: string;
  phone: string;
  role: Role;
  membership_status: MembershipStatusType;
  photo: string | null;
  is_active: boolean;
  joined_date: string | null;
  created_at: string;
}

export interface Member extends MemberListItem {
  phone_secondary: string;
  birth_date: string | null;
  address: string;
  city: string;
  province: ProvinceType | '';
  postal_code: string;
  family_status: FamilyStatusType | '';
  gender: string;
  notes: string;
  emergency_contact_name: string;
  emergency_contact_phone: string;
  baptism_date: string | null;
  salvation_date: string | null;
  all_roles: Role[];
  has_full_access: boolean;
  is_staff_member: boolean;
  two_factor_enabled: boolean;
  updated_at: string;
  // Nested relations (v2)
  groups?: GroupMembership[];
  family?: FamilyInfo | null;
  privacy_settings?: PrivacySettings | null;
}

export interface GroupMembership {
  id: string;
  group_id: string;
  group_name: string;
  group_type: string;
  role_in_group: string;
  joined_at: string;
}

export interface FamilyInfo {
  id: string;
  name: string;
  members: FamilyMember[];
}

export interface FamilyMember {
  id: string;
  member_id: string;
  full_name: string;
  relationship: string;
}

export interface PrivacySettings {
  email_visible: PrivacyLevelType;
  phone_visible: PrivacyLevelType;
  address_visible: PrivacyLevelType;
  birthday_visible: PrivacyLevelType;
}

export interface Group {
  id: string;
  name: string;
  group_type: string;
  description: string;
  leader: MemberListItem | null;
  member_count: number;
  is_active: boolean;
  meeting_day: string;
  meeting_time: string;
  meeting_location: string;
  created_at: string;
}

export interface Department {
  id: string;
  name: string;
  description: string;
  leader: MemberListItem | null;
  member_count: number;
  is_active: boolean;
}

export interface MemberCreateRequest {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  role?: string;
  birth_date?: string;
  address?: string;
  city?: string;
  province?: string;
  postal_code?: string;
  family_status?: string;
}

export interface MemberUpdateRequest extends Partial<MemberCreateRequest> {}
