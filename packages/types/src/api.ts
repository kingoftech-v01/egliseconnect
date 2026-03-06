/** Common API response types. */

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  error?: string;
  detail?: string;
  [field: string]: unknown;
}

export interface DashboardActivity {
  id: string;
  type: 'member' | 'donation' | 'event' | 'help';
  description: string;
  name: string;
  time: string;
}

export interface DashboardUpcomingEvent {
  id: string;
  title: string;
  date: string;
  type: string;
  attendees: number;
}

export interface DashboardGivingTrend {
  month: string;
  amount: number;
  pct: number;
}

export interface DashboardStats {
  members: {
    total: number;
    active: number;
    new_this_month: number;
    growth_rate: number;
  };
  donations: {
    total_this_month: string;
    total_this_year: string;
    count_this_month: number;
    average: string;
  };
  events: {
    upcoming_count: number;
    this_month_count: number;
    total_attendees_this_month: number;
  };
  attendance: {
    average_rate: number;
    last_sunday_count: number;
  };
  volunteers: {
    active_count: number;
    hours_this_month: number;
  };
  help_requests: {
    open_count: number;
    resolved_this_month: number;
  };
  recent_activities: DashboardActivity[];
  upcoming_events: DashboardUpcomingEvent[];
  giving_trends: DashboardGivingTrend[];
}
