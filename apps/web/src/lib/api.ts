export const API_BASE_URL = "http://localhost:8000/api/v1";

export type LoginPayload = {
  email: string;
  password: string;
};

export type Membership = {
  tenant_id: string;
  role: string;
  email_alerts_enabled: boolean;
  whatsapp_alerts_enabled: boolean;
  is_active: boolean;
};

export type AuthUser = {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
};

export type AuthResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
  memberships: Membership[];
};

export type RefreshTokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
};

export type SummaryReport = {
  total_connected_profiles: number;
  reviews_received: number;
  positive_reviews: number;
  negative_reviews: number;
  ai_response_rate: number;
  alert_delivery_rate: number;
  average_rating_network: number;
};

export type TrendPoint = {
  date: string;
  reviews_received: number;
  positive_reviews: number;
  negative_reviews: number;
  replies_posted: number;
  avg_rating: number;
};

export type ProfilePerformanceItem = {
  id: string;
  business_name: string;
  brand: string;
  city: string | null;
  state: string | null;
  reviews_received: number;
  positive_reviews: number;
  negative_reviews: number;
  replies_posted: number;
  avg_rating: number;
  response_rate: number;
};

export type Profile = {
  id: string;
  business_name: string;
  city: string | null;
  state: string | null;
  brand: string;
  avg_rating_cached: number;
  total_reviews_cached: number;
  auto_respond_enabled: boolean;
  is_active: boolean;
  last_review_activity_at: string | null;
  primary_local_admin_user_id: string | null;
  primary_local_admin_name: string | null;
};

export type Review = {
  id: string;
  gbp_review_id: string;
  business_name: string;
  reviewer_name: string | null;
  star_rating: number;
  review_text: string | null;
  sentiment: string;
  status: string;
  review_posted_at: string;
  reply_text: string | null;
};

export type ReviewListResponse = {
  items: Review[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type UserListItem = {
  id: string;
  email: string;
  full_name: string;
  phone_number: string | null;
  is_active: boolean;
  role: string;
  email_alerts_enabled: boolean;
  whatsapp_alerts_enabled: boolean;
  last_login_at: string | null;
  joined_at: string;
};

export type UserCreatePayload = {
  email: string;
  full_name: string;
  phone_number?: string;
  role: string;
  password: string;
  email_alerts_enabled: boolean;
  whatsapp_alerts_enabled: boolean;
};

export type UserUpdatePayload = {
  email?: string;
  full_name?: string;
  phone_number?: string;
  role?: string;
  email_alerts_enabled?: boolean;
  whatsapp_alerts_enabled?: boolean;
  is_active?: boolean;
};

export type GoogleAccount = {
  id: string;
  email: string;
  google_account_id: string | null;
  is_active: boolean;
  token_last_refreshed_at: string | null;
  scopes_json: string[];
  created_at: string;
};

export type ReplyTemplate = {
  id: string;
  brand: string;
  sentiment: string;
  template_text: string;
  is_active: boolean;
};

export type ReplyTemplateUpsertPayload = {
  brand: string;
  sentiment: string;
  template_text: string;
  is_active: boolean;
};

export type ProfileUpdatePayload = {
  primary_local_admin_user_id?: string | null;
  auto_respond_enabled?: boolean;
  is_active?: boolean;
};

export type DashboardPayload = {
  summary: SummaryReport;
  profiles: Profile[];
  reviews: Review[];
  users: UserListItem[];
  google_accounts: GoogleAccount[];
  reply_templates: ReplyTemplate[];
  latest_sync: {
    action: string;
    created_at: string;
    metadata_json: Record<string, unknown>;
  } | null;
};

export type ReportOverview = {
  summary: SummaryReport;
  trend: TrendPoint[];
  profiles: ProfilePerformanceItem[];
  window_days: number;
};

export type AuditLogItem = {
  id: string;
  action: string;
  target_type: string;
  target_id: string | null;
  actor_user_id: string | null;
  created_at: string;
  metadata_json: Record<string, unknown>;
};

export type GoogleOAuthStartResponse = {
  authorization_url: string;
};

export type GoogleLoginStartResponse = {
  authorization_url: string;
};

export type GoogleSyncResponse = {
  message: string;
  connected_accounts: number;
  synced_locations: number;
  synced_reviews: number;
  replies_posted: number;
  errors: string[];
};

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const { headers, ...restOptions } = options;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(headers ?? {}),
    },
    ...restOptions,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

async function refreshStoredSession(): Promise<string | null> {
  const { getStoredRefreshToken, updateStoredSessionTokens, clearStoredSession } = await import("./session");
  const refreshToken = getStoredRefreshToken();
  if (!refreshToken) {
    return null;
  }

  try {
    const response = await request<RefreshTokenResponse>("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    updateStoredSessionTokens(response.access_token, response.refresh_token);
    return response.access_token;
  } catch {
    clearStoredSession();
    return null;
  }
}

async function fetchWithAuthResponse(path: string, token: string, options: RequestInit = {}): Promise<Response> {
  const { headers, ...restOptions } = options;
  const authHeaders = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
    ...(headers ?? {}),
  };

  let response = await fetch(`${API_BASE_URL}${path}`, {
    headers: authHeaders,
    ...restOptions,
  });

  if (response.status === 401) {
    const refreshedToken = await refreshStoredSession();
    if (!refreshedToken) {
      const { clearStoredSession } = await import("./session");
      clearStoredSession();
      if (typeof window !== "undefined") {
        window.location.assign("/login");
      }
      return response;
    }

    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        ...authHeaders,
        Authorization: `Bearer ${refreshedToken}`,
      },
      ...restOptions,
    });

    if (response.status === 401) {
      const { clearStoredSession } = await import("./session");
      clearStoredSession();
      if (typeof window !== "undefined") {
        window.location.assign("/login");
      }
    }
  }

  return response;
}

async function requestWithAuth<T>(path: string, token: string, options: RequestInit = {}): Promise<T> {
  const response = await fetchWithAuthResponse(path, token, options);
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export async function login(payload: LoginPayload): Promise<AuthResponse> {
  return request<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchMe(token: string) {
  return requestWithAuth<{ user: AuthUser; memberships: Membership[]; last_login_at: string | null }>("/auth/me", token);
}

export async function fetchDashboard(token: string): Promise<DashboardPayload> {
  return requestWithAuth<DashboardPayload>("/dashboard", token);
}

export async function fetchReportOverview(token: string, days: number): Promise<ReportOverview> {
  return requestWithAuth<ReportOverview>(`/reports/overview?days=${days}`, token);
}

export async function downloadProfilesCsv(token: string, days: number): Promise<Blob> {
  const response = await fetchWithAuthResponse(`/reports/profiles.csv?days=${days}`, token);
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }
  return response.blob();
}

export async function fetchProfiles(token: string): Promise<{ items: Profile[] }> {
  return requestWithAuth<{ items: Profile[] }>("/profiles", token);
}

export async function fetchAuditLogs(token: string): Promise<{ items: AuditLogItem[] }> {
  return requestWithAuth<{ items: AuditLogItem[] }>("/audit-logs", token);
}

export type ReviewFeedQuery = {
  sentiment?: "positive" | "negative";
  profileId?: string;
  page?: number;
  pageSize?: number;
};

export async function fetchReviews(
  token: string,
  query: ReviewFeedQuery = {},
): Promise<ReviewListResponse> {
  const params = new URLSearchParams();
  if (query.sentiment) {
    params.set("sentiment", query.sentiment);
  }
  if (query.profileId) {
    params.set("profile_id", query.profileId);
  }
  if (typeof query.page === "number") {
    params.set("page", String(query.page));
  }
  if (typeof query.pageSize === "number") {
    params.set("page_size", String(query.pageSize));
  }
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return requestWithAuth<ReviewListResponse>(`/reviews${suffix}`, token);
}

export async function fetchUsers(token: string): Promise<{ items: UserListItem[] }> {
  return requestWithAuth<{ items: UserListItem[] }>("/users", token);
}

export async function createUser(token: string, payload: UserCreatePayload): Promise<UserListItem> {
  return requestWithAuth<UserListItem>("/users", token, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateUser(
  token: string,
  userId: string,
  payload: UserUpdatePayload,
): Promise<UserListItem> {
  return requestWithAuth<UserListItem>(`/users/${userId}`, token, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function fetchTemplates(token: string): Promise<{ items: ReplyTemplate[] }> {
  return requestWithAuth<{ items: ReplyTemplate[] }>("/reply-templates", token);
}

export async function createTemplate(
  token: string,
  payload: ReplyTemplateUpsertPayload,
): Promise<ReplyTemplate> {
  return requestWithAuth<ReplyTemplate>("/reply-templates", token, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateTemplate(
  token: string,
  templateId: string,
  payload: ReplyTemplateUpsertPayload,
): Promise<ReplyTemplate> {
  return requestWithAuth<ReplyTemplate>(`/reply-templates/${templateId}`, token, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function fetchGoogleAccounts(token: string): Promise<{ items: GoogleAccount[] }> {
  return requestWithAuth<{ items: GoogleAccount[] }>("/google", token);
}

export async function updateProfile(
  token: string,
  profileId: string,
  payload: ProfileUpdatePayload,
): Promise<Profile> {
  return requestWithAuth<Profile>(`/profiles/${profileId}`, token, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function startDashboardGoogleLogin(): Promise<GoogleLoginStartResponse> {
  return request<GoogleLoginStartResponse>("/auth/google/start", {
    method: "POST",
  });
}

export async function startGoogleOAuth(token: string): Promise<GoogleOAuthStartResponse> {
  return requestWithAuth<GoogleOAuthStartResponse>("/google/oauth/start", token, {
    method: "POST",
  });
}

export async function syncGoogleAccounts(token: string): Promise<GoogleSyncResponse> {
  return requestWithAuth<GoogleSyncResponse>("/google/sync", token, {
    method: "POST",
  });
}
