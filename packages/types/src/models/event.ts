/** Event-related types matching Django Event model. */
import type { EventTypeValue, RSVPStatusType } from '../constants';

export interface EventListItem {
  id: string;
  title: string;
  event_type: EventTypeValue;
  start_date: string;
  end_date: string | null;
  location: string;
  is_virtual: boolean;
  virtual_link: string;
  organizer: { id: string; full_name: string } | null;
  attendee_count: number;
  max_capacity: number | null;
  is_full: boolean;
  is_recurring: boolean;
  created_at: string;
}

export interface Event extends EventListItem {
  description: string;
  image: string | null;
  registration_required: boolean;
  registration_deadline: string | null;
  cost: string | null;
  notes: string;
  updated_at: string;
  // Nested v2
  rsvps?: EventRSVP[];
}

export interface EventRSVP {
  id: string;
  member: { id: string; full_name: string };
  status: RSVPStatusType;
  responded_at: string;
  guests: number;
}

export interface EventCreateRequest {
  title: string;
  event_type: EventTypeValue;
  start_date: string;
  end_date?: string;
  location?: string;
  description?: string;
  is_virtual?: boolean;
  virtual_link?: string;
  max_capacity?: number;
  registration_required?: boolean;
  registration_deadline?: string;
}
