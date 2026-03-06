/**
 * Type-safe API client for EgliseConnect backend.
 * Handles JWT auth, token refresh, and request/response typing.
 */
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  RefreshResponse,
  LogoutRequest,
  MeResponse,
  MeUpdateRequest,
  PaginatedResponse,
  ApiError,
} from '@egliseconnect/types';

export interface ApiClientConfig {
  baseUrl: string;
  getAccessToken: () => string | null;
  getRefreshToken: () => string | null;
  onTokenRefreshed: (access: string, refresh?: string) => void;
  onAuthError: () => void;
}

export class ApiClient {
  private config: ApiClientConfig;
  private refreshPromise: Promise<string | null> | null = null;

  constructor(config: ApiClientConfig) {
    this.config = config;
  }

  private async request<T>(
    path: string,
    options: RequestInit = {},
  ): Promise<T> {
    const url = `${this.config.baseUrl}${path}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    const token = this.config.getAccessToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.status === 401 && token) {
      const newToken = await this.refreshAccessToken();
      if (newToken) {
        headers['Authorization'] = `Bearer ${newToken}`;
        const retryResponse = await fetch(url, { ...options, headers });
        if (!retryResponse.ok) {
          throw await this.parseError(retryResponse);
        }
        return retryResponse.json() as Promise<T>;
      }
      this.config.onAuthError();
      throw new ApiClientError('Session expired', 401);
    }

    if (!response.ok) {
      throw await this.parseError(response);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json() as Promise<T>;
  }

  private async refreshAccessToken(): Promise<string | null> {
    if (this.refreshPromise) return this.refreshPromise;

    this.refreshPromise = (async () => {
      const refreshToken = this.config.getRefreshToken();
      if (!refreshToken) return null;

      try {
        const response = await fetch(
          `${this.config.baseUrl}/api/v2/auth/refresh/`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh: refreshToken }),
          },
        );

        if (!response.ok) return null;

        const data: RefreshResponse = await response.json();
        this.config.onTokenRefreshed(data.access, data.refresh);
        return data.access;
      } catch {
        return null;
      } finally {
        this.refreshPromise = null;
      }
    })();

    return this.refreshPromise;
  }

  private async parseError(response: Response): Promise<ApiClientError> {
    try {
      const data: ApiError = await response.json();
      return new ApiClientError(
        data.error || data.detail || 'Request failed',
        response.status,
        data,
      );
    } catch {
      return new ApiClientError('Request failed', response.status);
    }
  }

  // ─── HTTP Methods ────────────────────────────────────────────────────────

  async get<T>(path: string): Promise<T> {
    return this.request<T>(path);
  }

  async post<T>(path: string, data?: unknown): Promise<T> {
    return this.request<T>(path, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async patch<T>(path: string, data: unknown): Promise<T> {
    return this.request<T>(path, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async put<T>(path: string, data: unknown): Promise<T> {
    return this.request<T>(path, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async delete<T = void>(path: string): Promise<T> {
    return this.request<T>(path, { method: 'DELETE' });
  }

  // ─── Auth Endpoints ──────────────────────────────────────────────────────

  auth = {
    login: (data: LoginRequest): Promise<LoginResponse> =>
      this.post('/api/v2/auth/login/', data),

    register: (data: RegisterRequest): Promise<RegisterResponse> =>
      this.post('/api/v2/auth/register/', data),

    logout: (data: LogoutRequest): Promise<void> =>
      this.post('/api/v2/auth/logout/', data),

    me: (): Promise<MeResponse> =>
      this.get('/api/v2/auth/me/'),

    updateMe: (data: MeUpdateRequest): Promise<MeResponse> =>
      this.patch('/api/v2/auth/me/', data),

    refresh: (refreshToken: string): Promise<RefreshResponse> =>
      this.post('/api/v2/auth/refresh/', { refresh: refreshToken }),
  };

  // ─── Members Endpoints ───────────────────────────────────────────────────

  members = {
    list: (params?: string): Promise<PaginatedResponse<unknown>> =>
      this.get(`/api/v1/members/members/${params ? `?${params}` : ''}`),

    get: (id: string): Promise<unknown> =>
      this.get(`/api/v1/members/members/${id}/`),

    create: (data: unknown): Promise<unknown> =>
      this.post('/api/v1/members/members/', data),

    update: (id: string, data: unknown): Promise<unknown> =>
      this.patch(`/api/v1/members/members/${id}/`, data),

    delete: (id: string): Promise<void> =>
      this.delete(`/api/v1/members/members/${id}/`),
  };

  // ─── Donations Endpoints ─────────────────────────────────────────────────

  donations = {
    list: (params?: string): Promise<PaginatedResponse<unknown>> =>
      this.get(`/api/v1/donations/donations/${params ? `?${params}` : ''}`),

    get: (id: string): Promise<unknown> =>
      this.get(`/api/v1/donations/donations/${id}/`),

    create: (data: unknown): Promise<unknown> =>
      this.post('/api/v1/donations/donations/', data),

    update: (id: string, data: unknown): Promise<unknown> =>
      this.patch(`/api/v1/donations/donations/${id}/`, data),

    delete: (id: string): Promise<void> =>
      this.delete(`/api/v1/donations/donations/${id}/`),
  };

  // ─── Events Endpoints ────────────────────────────────────────────────────

  events = {
    list: (params?: string): Promise<PaginatedResponse<unknown>> =>
      this.get(`/api/v1/events/events/${params ? `?${params}` : ''}`),

    get: (id: string): Promise<unknown> =>
      this.get(`/api/v1/events/events/${id}/`),

    create: (data: unknown): Promise<unknown> =>
      this.post('/api/v1/events/events/', data),

    update: (id: string, data: unknown): Promise<unknown> =>
      this.patch(`/api/v1/events/events/${id}/`, data),

    delete: (id: string): Promise<void> =>
      this.delete(`/api/v1/events/events/${id}/`),
  };

  // ─── Dashboard ───────────────────────────────────────────────────────────

  dashboard = {
    stats: (): Promise<unknown> =>
      this.get('/api/v2/core/dashboard/'),
  };

  // ─── Volunteers Endpoints ─────────────────────────────────────────────────

  volunteers = {
    positions: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/volunteers/positions/${params ? `?${params}` : ''}`),
      get: (id: string): Promise<unknown> =>
        this.get(`/api/v1/volunteers/positions/${id}/`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/volunteers/positions/', data),
      update: (id: string, data: unknown): Promise<unknown> =>
        this.patch(`/api/v1/volunteers/positions/${id}/`, data),
      delete: (id: string): Promise<void> =>
        this.delete(`/api/v1/volunteers/positions/${id}/`),
    },
    schedules: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/volunteers/schedules/${params ? `?${params}` : ''}`),
      get: (id: string): Promise<unknown> =>
        this.get(`/api/v1/volunteers/schedules/${id}/`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/volunteers/schedules/', data),
      mySchedule: (): Promise<unknown[]> =>
        this.get('/api/v1/volunteers/schedules/my-schedule/'),
      confirm: (id: string): Promise<unknown> =>
        this.post(`/api/v1/volunteers/schedules/${id}/confirm/`),
    },
    availability: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/volunteers/availability/${params ? `?${params}` : ''}`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/volunteers/availability/', data),
      update: (id: string, data: unknown): Promise<unknown> =>
        this.patch(`/api/v1/volunteers/availability/${id}/`, data),
      delete: (id: string): Promise<void> =>
        this.delete(`/api/v1/volunteers/availability/${id}/`),
    },
    swapRequests: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/volunteers/swap-requests/${params ? `?${params}` : ''}`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/volunteers/swap-requests/', data),
    },
  };

  // ─── Communication Endpoints ──────────────────────────────────────────────

  communication = {
    newsletters: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/communication/newsletters/${params ? `?${params}` : ''}`),
      get: (id: string): Promise<unknown> =>
        this.get(`/api/v1/communication/newsletters/${id}/`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/communication/newsletters/', data),
      update: (id: string, data: unknown): Promise<unknown> =>
        this.patch(`/api/v1/communication/newsletters/${id}/`, data),
      send: (id: string): Promise<unknown> =>
        this.post(`/api/v1/communication/newsletters/${id}/send/`),
    },
    notifications: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/communication/notifications/${params ? `?${params}` : ''}`),
      markRead: (id: string): Promise<unknown> =>
        this.post(`/api/v1/communication/notifications/${id}/mark-read/`),
      unreadCount: (): Promise<{ count: number }> =>
        this.get('/api/v1/communication/notifications/unread_count/'),
    },
    sms: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/communication/sms/${params ? `?${params}` : ''}`),
      send: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/communication/sms/', data),
    },
    directMessages: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/communication/direct-messages/${params ? `?${params}` : ''}`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/communication/direct-messages/', data),
      markRead: (id: string): Promise<unknown> =>
        this.post(`/api/v1/communication/direct-messages/${id}/mark-read/`),
    },
    templates: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/communication/email-templates/${params ? `?${params}` : ''}`),
      get: (id: string): Promise<unknown> =>
        this.get(`/api/v1/communication/email-templates/${id}/`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/communication/email-templates/', data),
      update: (id: string, data: unknown): Promise<unknown> =>
        this.patch(`/api/v1/communication/email-templates/${id}/`, data),
    },
    automations: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/communication/automations/${params ? `?${params}` : ''}`),
      get: (id: string): Promise<unknown> =>
        this.get(`/api/v1/communication/automations/${id}/`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/communication/automations/', data),
      update: (id: string, data: unknown): Promise<unknown> =>
        this.patch(`/api/v1/communication/automations/${id}/`, data),
    },
  };

  // ─── Help Requests Endpoints ──────────────────────────────────────────────

  helpRequests = {
    list: (params?: string): Promise<PaginatedResponse<unknown>> =>
      this.get(`/api/v1/help-requests/requests/${params ? `?${params}` : ''}`),
    get: (id: string): Promise<unknown> =>
      this.get(`/api/v1/help-requests/requests/${id}/`),
    create: (data: unknown): Promise<unknown> =>
      this.post('/api/v1/help-requests/requests/', data),
    update: (id: string, data: unknown): Promise<unknown> =>
      this.patch(`/api/v1/help-requests/requests/${id}/`, data),
    assign: (id: string, data: unknown): Promise<unknown> =>
      this.post(`/api/v1/help-requests/requests/${id}/assign/`, data),
    resolve: (id: string, data: unknown): Promise<unknown> =>
      this.post(`/api/v1/help-requests/requests/${id}/resolve/`, data),
    comment: (id: string, data: unknown): Promise<unknown> =>
      this.post(`/api/v1/help-requests/requests/${id}/comment/`, data),
    myRequests: (params?: string): Promise<PaginatedResponse<unknown>> =>
      this.get(`/api/v1/help-requests/requests/my_requests/${params ? `?${params}` : ''}`),
    categories: {
      list: (): Promise<unknown[]> =>
        this.get('/api/v1/help-requests/categories/'),
    },
    prayerRequests: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/help-requests/prayer-requests/${params ? `?${params}` : ''}`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/help-requests/prayer-requests/', data),
      wall: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/help-requests/prayer-requests/wall/${params ? `?${params}` : ''}`),
    },
    pastoralCare: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/help-requests/pastoral-care/${params ? `?${params}` : ''}`),
      get: (id: string): Promise<unknown> =>
        this.get(`/api/v1/help-requests/pastoral-care/${id}/`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/help-requests/pastoral-care/', data),
    },
    careTeams: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/help-requests/care-teams/${params ? `?${params}` : ''}`),
      get: (id: string): Promise<unknown> =>
        this.get(`/api/v1/help-requests/care-teams/${id}/`),
    },
    benevolence: {
      funds: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/help-requests/benevolence-funds/${params ? `?${params}` : ''}`),
      requests: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/help-requests/benevolence-requests/${params ? `?${params}` : ''}`),
      createRequest: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/help-requests/benevolence-requests/', data),
    },
    mealTrains: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/help-requests/meal-trains/${params ? `?${params}` : ''}`),
      get: (id: string): Promise<unknown> =>
        this.get(`/api/v1/help-requests/meal-trains/${id}/`),
      signup: (id: string, data: unknown): Promise<unknown> =>
        this.post(`/api/v1/help-requests/meal-signups/`, data),
    },
  };

  // ─── Reports Endpoints ────────────────────────────────────────────────────

  reports = {
    dashboard: {
      members: (): Promise<unknown> =>
        this.get('/api/v1/reports/dashboard/members/'),
      donations: (): Promise<unknown> =>
        this.get('/api/v1/reports/dashboard/donations/'),
      events: (): Promise<unknown> =>
        this.get('/api/v1/reports/dashboard/events/'),
      volunteers: (): Promise<unknown> =>
        this.get('/api/v1/reports/dashboard/volunteers/'),
      helpRequests: (): Promise<unknown> =>
        this.get('/api/v1/reports/dashboard/help_requests/'),
    },
    attendance: (params?: string): Promise<unknown> =>
      this.get(`/api/v1/reports/reports/attendance/${params ? `?${params}` : ''}`),
    donationReport: (year: number): Promise<unknown> =>
      this.get(`/api/v1/reports/reports/donations/${year}/`),
    volunteerReport: (): Promise<unknown> =>
      this.get('/api/v1/reports/reports/volunteers/'),
    schedules: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/reports/schedules/${params ? `?${params}` : ''}`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/reports/schedules/', data),
    },
    saved: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/reports/saved-reports/${params ? `?${params}` : ''}`),
      get: (id: string): Promise<unknown> =>
        this.get(`/api/v1/reports/saved-reports/${id}/`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/reports/saved-reports/', data),
    },
  };

  // ─── Onboarding Endpoints ─────────────────────────────────────────────────

  onboarding = {
    status: (): Promise<unknown> =>
      this.get('/api/v1/onboarding/status/'),
    stats: (): Promise<unknown> =>
      this.get('/api/v1/onboarding/stats/'),
    courses: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/onboarding/courses/${params ? `?${params}` : ''}`),
      get: (id: string): Promise<unknown> =>
        this.get(`/api/v1/onboarding/courses/${id}/`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/onboarding/courses/', data),
      update: (id: string, data: unknown): Promise<unknown> =>
        this.patch(`/api/v1/onboarding/courses/${id}/`, data),
    },
    trainings: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/onboarding/trainings/${params ? `?${params}` : ''}`),
      get: (id: string): Promise<unknown> =>
        this.get(`/api/v1/onboarding/trainings/${id}/`),
    },
    interviews: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/onboarding/interviews/${params ? `?${params}` : ''}`),
      get: (id: string): Promise<unknown> =>
        this.get(`/api/v1/onboarding/interviews/${id}/`),
      accept: (id: string): Promise<unknown> =>
        this.post(`/api/v1/onboarding/interviews/${id}/accept/`),
      counterPropose: (id: string, data: unknown): Promise<unknown> =>
        this.post(`/api/v1/onboarding/interviews/${id}/counter_propose/`, data),
    },
    invitations: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/onboarding/invitation-codes/${params ? `?${params}` : ''}`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/onboarding/invitation-codes/', data),
    },
    mentors: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/onboarding/mentors/${params ? `?${params}` : ''}`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/onboarding/mentors/', data),
    },
    documents: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/onboarding/documents/${params ? `?${params}` : ''}`),
      sign: (id: string, data: unknown): Promise<unknown> =>
        this.post(`/api/v1/onboarding/signatures/${id}/sign/`, data),
    },
    quiz: {
      get: (id: string): Promise<unknown> =>
        this.get(`/api/v1/onboarding/quizzes/${id}/`),
      submit: (id: string, data: unknown): Promise<unknown> =>
        this.post(`/api/v1/onboarding/quiz-attempts/${id}/submit/`, data),
    },
  };

  // ─── Attendance Endpoints ─────────────────────────────────────────────────

  attendance = {
    sessions: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/attendance/sessions/${params ? `?${params}` : ''}`),
      get: (id: string): Promise<unknown> =>
        this.get(`/api/v1/attendance/sessions/${id}/`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/attendance/sessions/', data),
      update: (id: string, data: unknown): Promise<unknown> =>
        this.patch(`/api/v1/attendance/sessions/${id}/`, data),
    },
    checkIn: (data: { qr_code: string; session_id: string }): Promise<unknown> =>
      this.post('/api/v1/attendance/checkin/', data),
    checkOut: (data: { member_id: string; session_id: string }): Promise<unknown> =>
      this.post('/api/v1/attendance/checkout/', data),
    familyCheckIn: (data: unknown): Promise<unknown> =>
      this.post('/api/v1/attendance/family-checkin/', data),
    qrCode: {
      mine: (): Promise<unknown> =>
        this.get('/api/v1/attendance/qr-codes/'),
      regenerate: (id: string): Promise<unknown> =>
        this.post(`/api/v1/attendance/qr-codes/${id}/regenerate/`),
    },
    alerts: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/attendance/alerts/${params ? `?${params}` : ''}`),
      acknowledge: (id: string): Promise<unknown> =>
        this.post(`/api/v1/attendance/alerts/${id}/acknowledge/`),
    },
    visitors: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/attendance/visitors/${params ? `?${params}` : ''}`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/attendance/visitors/', data),
    },
    analytics: {
      trends: (params?: string): Promise<unknown> =>
        this.get(`/api/v1/attendance/analytics/trends/${params ? `?${params}` : ''}`),
      averageByType: (): Promise<unknown> =>
        this.get('/api/v1/attendance/analytics/average_by_type/'),
      memberRate: (memberId: string): Promise<unknown> =>
        this.get(`/api/v1/attendance/analytics/member_rate/?member_id=${memberId}`),
    },
  };

  // ─── Payments Endpoints ───────────────────────────────────────────────────

  payments = {
    list: (params?: string): Promise<PaginatedResponse<unknown>> =>
      this.get(`/api/v1/payments/payments/${params ? `?${params}` : ''}`),
    createIntent: (data: unknown): Promise<unknown> =>
      this.post('/api/v1/payments/payments/create_intent/', data),
    recurring: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/payments/recurring/${params ? `?${params}` : ''}`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/payments/recurring/create_subscription/', data),
      cancel: (id: string): Promise<unknown> =>
        this.post(`/api/v1/payments/recurring/${id}/cancel/`),
    },
    statements: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/payments/statements/${params ? `?${params}` : ''}`),
    },
    goals: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/payments/goals/${params ? `?${params}` : ''}`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/payments/goals/', data),
      progress: (id: string): Promise<unknown> =>
        this.get(`/api/v1/payments/goals/${id}/progress/`),
    },
    plans: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/payments/plans/${params ? `?${params}` : ''}`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/payments/plans/create_plan/', data),
    },
    campaigns: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/payments/campaigns/${params ? `?${params}` : ''}`),
      get: (id: string): Promise<unknown> =>
        this.get(`/api/v1/payments/campaigns/${id}/`),
    },
  };

  // ─── Worship Endpoints ────────────────────────────────────────────────────

  worship = {
    services: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/worship/services/${params ? `?${params}` : ''}`),
      get: (id: string): Promise<unknown> =>
        this.get(`/api/v1/worship/services/${id}/`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/worship/services/', data),
      update: (id: string, data: unknown): Promise<unknown> =>
        this.patch(`/api/v1/worship/services/${id}/`, data),
    },
    sections: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/worship/sections/${params ? `?${params}` : ''}`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/worship/sections/', data),
      update: (id: string, data: unknown): Promise<unknown> =>
        this.patch(`/api/v1/worship/sections/${id}/`, data),
    },
    assignments: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/worship/assignments/${params ? `?${params}` : ''}`),
      myAssignments: (): Promise<unknown[]> =>
        this.get('/api/v1/worship/assignments/my-assignments/'),
      confirm: (id: string): Promise<unknown> =>
        this.post(`/api/v1/worship/assignments/${id}/confirm/`),
      decline: (id: string): Promise<unknown> =>
        this.post(`/api/v1/worship/assignments/${id}/decline/`),
    },
    sermons: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/worship/sermons/${params ? `?${params}` : ''}`),
      get: (id: string): Promise<unknown> =>
        this.get(`/api/v1/worship/sermons/${id}/`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/worship/sermons/', data),
      update: (id: string, data: unknown): Promise<unknown> =>
        this.patch(`/api/v1/worship/sermons/${id}/`, data),
    },
    songs: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/worship/songs/${params ? `?${params}` : ''}`),
      get: (id: string): Promise<unknown> =>
        this.get(`/api/v1/worship/songs/${id}/`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/worship/songs/', data),
      update: (id: string, data: unknown): Promise<unknown> =>
        this.patch(`/api/v1/worship/songs/${id}/`, data),
    },
    setlists: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/worship/setlists/${params ? `?${params}` : ''}`),
      get: (id: string): Promise<unknown> =>
        this.get(`/api/v1/worship/setlists/${id}/`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/worship/setlists/', data),
    },
    rehearsals: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/worship/rehearsals/${params ? `?${params}` : ''}`),
      get: (id: string): Promise<unknown> =>
        this.get(`/api/v1/worship/rehearsals/${id}/`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/worship/rehearsals/', data),
    },
    songRequests: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/worship/song-requests/${params ? `?${params}` : ''}`),
      create: (data: unknown): Promise<unknown> =>
        this.post('/api/v1/worship/song-requests/', data),
    },
    liveStreams: {
      list: (params?: string): Promise<PaginatedResponse<unknown>> =>
        this.get(`/api/v1/worship/livestreams/${params ? `?${params}` : ''}`),
      get: (id: string): Promise<unknown> =>
        this.get(`/api/v1/worship/livestreams/${id}/`),
    },
  };
}

export class ApiClientError extends Error {
  status: number;
  data?: ApiError;

  constructor(message: string, status: number, data?: ApiError) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.data = data;
  }
}
