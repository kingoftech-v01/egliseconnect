/** Donation-related types matching Django Donation model. */
import type { DonationTypeValue, PaymentMethodType } from '../constants';

export interface DonationListItem {
  id: string;
  donation_number: string;
  member: { id: string; full_name: string } | null;
  amount: string;
  donation_type: DonationTypeValue;
  payment_method: PaymentMethodType;
  date: string;
  is_anonymous: boolean;
  is_recurring: boolean;
  campaign: { id: string; name: string } | null;
  created_at: string;
}

export interface Donation extends DonationListItem {
  notes: string;
  receipt_number: string | null;
  receipt_issued: boolean;
  receipt_issued_date: string | null;
  updated_at: string;
}

export interface Campaign {
  id: string;
  name: string;
  description: string;
  goal_amount: string;
  raised_amount: string;
  start_date: string;
  end_date: string | null;
  is_active: boolean;
  donation_count: number;
  progress_percentage: number;
}

export interface TaxReceipt {
  id: string;
  receipt_number: string;
  member: { id: string; full_name: string };
  year: number;
  total_amount: string;
  issued_date: string;
  pdf_url: string | null;
}

export interface DonationCreateRequest {
  member_id?: string;
  amount: string;
  donation_type: DonationTypeValue;
  payment_method: PaymentMethodType;
  date: string;
  is_anonymous?: boolean;
  campaign_id?: string;
  notes?: string;
}

export interface DonationStats {
  total_this_month: string;
  total_this_year: string;
  donation_count: number;
  average_amount: string;
  by_type: { type: DonationTypeValue; total: string; count: number }[];
  monthly_trend: { month: string; total: string }[];
}
