import { useEffect, useState } from "react";

import { useAuth } from "../app/AuthContext";
import { MetricCard } from "../components/MetricCard";
import { Panel } from "../components/Panel";
import {
  fetchDashboard,
  fetchProfiles,
  fetchReportOverview,
  fetchReviews,
  startGoogleOAuth,
  syncGoogleAccounts,
  type DashboardPayload,
  type GoogleSyncResponse,
  type Profile,
  type ProfilePerformanceItem,
  type ReportOverview,
  type ReviewListResponse,
  type TrendPoint,
} from "../lib/api";

const REVIEW_PAGE_SIZE = 5;

function TrendGraph({ trend }: { trend: TrendPoint[] }) {
  const safeTrend = trend.length
    ? trend
    : [
        {
          date: new Date().toISOString(),
          reviews_received: 0,
          positive_reviews: 0,
          negative_reviews: 0,
          replies_posted: 0,
          avg_rating: 0,
        },
      ];
  const latestPoint = safeTrend.at(-1);
  const totalReviews = safeTrend.reduce((sum, point) => sum + point.reviews_received, 0);
  const peakDayReviews = Math.max(...safeTrend.map((point) => point.reviews_received), 0);
  const maxReviews = Math.max(...safeTrend.map((point) => point.reviews_received), 1);
  const points = safeTrend.map((point, index) => {
    const x = safeTrend.length === 1 ? 0 : (index / (safeTrend.length - 1)) * 100;
    const y = 100 - (point.reviews_received / maxReviews) * 100;
    return `${x},${y}`;
  });
  const areaPoints = [`0,100`, ...points, `100,100`].join(" ");
  const linePoints = points.join(" ");

  return (
    <div className="rounded-[1.75rem] border border-ink/10 bg-[linear-gradient(180deg,#173b35_0%,#102620_100%)] p-5 text-sand">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.25em] text-sand/55">Review Trend</p>
          <p className="mt-2 font-display text-4xl">{latestPoint?.reviews_received ?? 0}</p>
          <p className="mt-1 text-sm text-sand/65">
            reviews on the most recent tracked day
          </p>
        </div>
        <div className="text-right text-sm text-sand/65">
          <p>Last {safeTrend.length} days</p>
          <p>{totalReviews} total reviews in this window</p>
        </div>
      </div>
      <div className="mt-6">
        <svg viewBox="0 0 100 100" className="h-48 w-full overflow-visible">
          <defs>
            <linearGradient id="dashboardArea" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="rgba(216, 180, 79, 0.8)" />
              <stop offset="100%" stopColor="rgba(216, 180, 79, 0.08)" />
            </linearGradient>
          </defs>
          <polyline
            points={areaPoints}
            fill="url(#dashboardArea)"
            stroke="none"
          />
          <polyline
            points={linePoints}
            fill="none"
            stroke="#f1c15d"
            strokeWidth="2.5"
            strokeLinejoin="round"
            strokeLinecap="round"
          />
        </svg>
      </div>
      <div className="mt-2 grid grid-cols-3 gap-3 text-xs uppercase tracking-[0.18em] text-sand/55">
        <span>{safeTrend[0] ? new Date(safeTrend[0].date).toLocaleDateString() : ""}</span>
        <span className="text-center">Peak day: {peakDayReviews}</span>
        <span className="text-right">
          {latestPoint ? new Date(latestPoint.date).toLocaleDateString() : ""}
        </span>
      </div>
    </div>
  );
}

function SentimentSplit({
  positiveReviews,
  negativeReviews,
  responseRate,
}: {
  positiveReviews: number;
  negativeReviews: number;
  responseRate: number;
}) {
  const total = Math.max(positiveReviews + negativeReviews, 1);
  const positiveWidth = (positiveReviews / total) * 100;
  const negativeWidth = (negativeReviews / total) * 100;

  return (
    <div className="space-y-5 rounded-[1.75rem] border border-ink/10 bg-sand/45 p-5">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.25em] text-ink/45">Sentiment Mix</p>
          <p className="mt-2 font-display text-4xl text-ink">{positiveReviews + negativeReviews}</p>
          <p className="mt-1 text-sm text-ink/60">reviews in the network pulse</p>
        </div>
        <div className="rounded-full bg-white px-4 py-2 text-xs uppercase tracking-[0.2em] text-pine">
          {Math.round(responseRate * 100)}% replied
        </div>
      </div>
      <div className="h-5 overflow-hidden rounded-full bg-white">
        <div className="flex h-full w-full">
          <div className="bg-pine" style={{ width: `${positiveWidth}%` }} />
          <div className="bg-rust" style={{ width: `${negativeWidth}%` }} />
        </div>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-2xl bg-white px-4 py-4">
          <p className="text-xs uppercase tracking-[0.2em] text-ink/45">Positive</p>
          <p className="mt-2 text-2xl font-semibold text-pine">{positiveReviews}</p>
        </div>
        <div className="rounded-2xl bg-white px-4 py-4">
          <p className="text-xs uppercase tracking-[0.2em] text-ink/45">Negative</p>
          <p className="mt-2 text-2xl font-semibold text-rust">{negativeReviews}</p>
        </div>
      </div>
    </div>
  );
}

function BranchPerformance({ profiles }: { profiles: ProfilePerformanceItem[] }) {
  const maxReviews = Math.max(...profiles.map((profile) => profile.reviews_received), 1);

  if (!profiles.length) {
    return (
      <div className="rounded-3xl border border-dashed border-ink/15 bg-sand/35 p-6 text-sm text-ink/60">
        No review activity is available for this window yet.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {profiles.slice(0, 5).map((profile) => (
        <article key={profile.id} className="rounded-3xl border border-ink/10 bg-white/80 p-4">
          <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <h3 className="font-semibold">{profile.business_name}</h3>
              <p className="text-sm text-ink/55">
                {profile.city ?? "Unknown city"}, {profile.state ?? "Unknown state"} · {profile.brand}
              </p>
            </div>
            <div className="text-sm text-ink/65 md:text-right">
              {profile.reviews_received} reviews · {Math.round(profile.response_rate * 100)}% response
            </div>
          </div>
          <div className="mt-4 h-3 overflow-hidden rounded-full bg-sand">
            <div
              className="h-full rounded-full bg-[linear-gradient(90deg,#18453b_0%,#c7922f_100%)]"
              style={{ width: `${(profile.reviews_received / maxReviews) * 100}%` }}
            />
          </div>
        </article>
      ))}
    </div>
  );
}

export function DashboardPage() {
  const { accessToken, memberships } = useAuth();
  const isMasterAdmin = memberships[0]?.role === "master_admin";
  const [dashboard, setDashboard] = useState<DashboardPayload | null>(null);
  const [overview, setOverview] = useState<ReportOverview | null>(null);
  const [branchProfiles, setBranchProfiles] = useState<Profile[]>([]);
  const [reviewFeed, setReviewFeed] = useState<ReviewListResponse | null>(null);
  const [reviewPage, setReviewPage] = useState(1);
  const [reviewSentiment, setReviewSentiment] = useState<"all" | "positive" | "negative">("all");
  const [reviewBranchId, setReviewBranchId] = useState("all");
  const [error, setError] = useState<string | null>(null);
  const [syncResult, setSyncResult] = useState<GoogleSyncResponse | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncToasts, setSyncToasts] = useState<string[]>([]);

  async function loadDashboard() {
    if (!accessToken) return;
    try {
      const payload = await fetchDashboard(accessToken);
      setDashboard(payload);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard");
    }
  }

  async function loadOverview() {
    if (!accessToken) return;
    try {
      const payload = await fetchReportOverview(accessToken, 14);
      setOverview(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load analytics");
    }
  }

  async function loadBranchProfiles() {
    if (!accessToken) return;
    try {
      const payload = await fetchProfiles(accessToken);
      setBranchProfiles(payload.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load branches");
    }
  }

  async function loadReviewFeed() {
    if (!accessToken) return;
    try {
      const payload = await fetchReviews(accessToken, {
        sentiment: reviewSentiment === "all" ? undefined : reviewSentiment,
        profileId: reviewBranchId === "all" ? undefined : reviewBranchId,
        page: reviewPage,
        pageSize: REVIEW_PAGE_SIZE,
      });
      setReviewFeed(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load reviews");
    }
  }

  useEffect(() => {
    void loadDashboard();
  }, [accessToken]);

  useEffect(() => {
    void loadOverview();
  }, [accessToken]);

  useEffect(() => {
    void loadBranchProfiles();
  }, [accessToken]);

  useEffect(() => {
    void loadReviewFeed();
  }, [accessToken, reviewPage, reviewSentiment, reviewBranchId]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const status = params.get("google_oauth");
    const message = params.get("message");
    if (!status) return;

    if (status === "success") {
      setActionMessage("Google account connected successfully. Run sync to import locations and reviews.");
      void loadDashboard();
    } else {
      setError(message ?? "Google OAuth failed");
    }

    window.history.replaceState({}, document.title, window.location.pathname);
  }, []);

  async function handleConnectGoogle() {
    if (!accessToken) return;
    try {
      const response = await startGoogleOAuth(accessToken);
      window.location.href = response.authorization_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start Google OAuth");
    }
  }

  async function handleSync() {
    if (!accessToken) return;
    setSyncing(true);
    setError(null);
    try {
      const result = await syncGoogleAccounts(accessToken);
      setSyncResult(result);
      setActionMessage(result.message);
      if (result.errors.length) {
        setSyncToasts(result.errors);
      }
      await loadDashboard();
      await loadOverview();
      await loadReviewFeed();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Google sync failed");
    } finally {
      setSyncing(false);
    }
  }

  useEffect(() => {
    if (!syncToasts.length) {
      return;
    }

    const timer = window.setTimeout(() => {
      setSyncToasts([]);
    }, 7000);

    return () => window.clearTimeout(timer);
  }, [syncToasts]);

  const reviewPulse = overview?.trend ?? [];
  const activeReviewPage = reviewFeed?.page ?? reviewPage;
  const activeReviewPageSize = reviewFeed?.page_size ?? REVIEW_PAGE_SIZE;
  const reviewRangeStart = reviewFeed?.total
    ? (activeReviewPage - 1) * activeReviewPageSize + 1
    : 0;
  const reviewRangeEnd = reviewFeed?.total
    ? Math.min(activeReviewPage * activeReviewPageSize, reviewFeed.total)
    : 0;

  function handleReviewSentimentChange(next: "all" | "positive" | "negative") {
    setReviewPage(1);
    setReviewSentiment(next);
  }

  function handleReviewBranchChange(next: string) {
    setReviewPage(1);
    setReviewBranchId(next);
  }

  if (!dashboard) {
    return <p className="text-ink/60">{error ?? "Loading dashboard..."}</p>;
  }

  return (
    <section className="space-y-8">
      {syncToasts.length ? (
        <div className="fixed right-4 top-4 z-50 flex w-[min(28rem,calc(100vw-2rem))] flex-col gap-3">
          {syncToasts.map((message, index) => (
            <div
              key={`${message}-${index}`}
              className="max-w-full overflow-hidden rounded-3xl border border-rust/25 bg-rust/10 px-5 py-4 text-sm leading-6 text-rust shadow-xl backdrop-blur-sm"
            >
              <div className="flex items-start justify-between gap-4">
                <p className="min-w-0 flex-1 break-all whitespace-pre-wrap">{message}</p>
                <button
                  type="button"
                  aria-label="Dismiss notification"
                  onClick={() => setSyncToasts((current) => current.filter((_, itemIndex) => itemIndex !== index))}
                  className="text-xs uppercase tracking-[0.2em] text-rust/70 transition hover:text-rust"
                >
                  Dismiss
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : null}

      {error ? (
        <div className="rounded-3xl border border-rust/20 bg-rust/10 px-5 py-4 text-sm text-rust">
          {error}
        </div>
      ) : null}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Connected Profiles"
          value={String(dashboard.summary.total_connected_profiles)}
        />
        <MetricCard label="Reviews Synced" value={String(dashboard.summary.reviews_received)} tone="rust" />
        <MetricCard
          label="AI Response Rate"
          value={`${Math.round(dashboard.summary.ai_response_rate * 100)}%`}
          tone="gold"
        />
        <MetricCard
          label="Network Rating"
          value={dashboard.summary.average_rating_network.toFixed(1)}
        />
      </div>

      {overview ? (
        <div className="grid gap-8 xl:grid-cols-[1.1fr_0.9fr]">
          <Panel
            eyebrow="Analytics"
            title={
              isMasterAdmin
                ? "Network momentum over the last two weeks"
                : "Your branch momentum over the last two weeks"
            }
          >
            <TrendGraph trend={reviewPulse} />
          </Panel>
          <Panel
            eyebrow="Pulse"
            title={
              isMasterAdmin
                ? "Sentiment and response coverage"
                : "Sentiment and response coverage for your profiles"
            }
          >
            <SentimentSplit
              positiveReviews={overview.summary.positive_reviews}
              negativeReviews={overview.summary.negative_reviews}
              responseRate={overview.summary.ai_response_rate}
            />
          </Panel>
        </div>
      ) : null}

      {overview ? (
        <Panel
          eyebrow={isMasterAdmin ? "Branch Ranking" : "Your Locations"}
          title={
            isMasterAdmin
              ? "Which locations are drawing the most review traffic"
              : "How your assigned locations are performing"
          }
        >
          <BranchPerformance profiles={overview.profiles} />
        </Panel>
      ) : null}

      <Panel eyebrow="Google Integration" title="Connect accounts and sync from the homepage">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="max-w-2xl text-sm leading-7 text-ink/70">
              {isMasterAdmin
                ? "Connect Google Business Profile here, then run a sync to import locations, fetch reviews, and post automated replies. Positive replies use Gemini when `GEMINI_API_KEY` is configured; otherwise the backend falls back to a basic thank-you response."
                : "Run a sync to refresh the branches assigned to you. Reviews and replies for those locations will update from Google during sync."}
            </div>
            <div className="flex flex-wrap gap-3">
              {isMasterAdmin ? (
                <button
                  type="button"
                  onClick={handleConnectGoogle}
                  className="rounded-full bg-pine px-5 py-3 text-sm uppercase tracking-[0.2em] text-sand"
                >
                  Connect Google
                </button>
              ) : null}
              <button
                type="button"
                onClick={handleSync}
                disabled={syncing}
                className="rounded-full border border-ink/15 bg-white px-5 py-3 text-sm uppercase tracking-[0.2em] text-ink disabled:opacity-50"
              >
                {syncing ? "Syncing..." : "Sync GBP"}
              </button>
            </div>
          </div>
          {actionMessage ? <p className="mt-5 text-sm text-pine">{actionMessage}</p> : null}
          {dashboard.latest_sync ? (
            <div className="mt-5 rounded-3xl border border-ink/10 bg-sand/45 px-5 py-4 text-sm text-ink/70">
              Last sync: {new Date(dashboard.latest_sync.created_at).toLocaleString()} ·{" "}
              {dashboard.latest_sync.action.replaceAll(".", " ")}
            </div>
          ) : null}
        {syncResult ? (
          <div className="mt-6 space-y-4">
            <div className="grid gap-4 md:grid-cols-4">
              <MetricCard label="Accounts" value={String(syncResult.connected_accounts)} />
              <MetricCard label="Locations" value={String(syncResult.synced_locations)} tone="rust" />
              <MetricCard label="Reviews" value={String(syncResult.synced_reviews)} tone="gold" />
              <MetricCard label="Replies" value={String(syncResult.replies_posted)} />
            </div>
          </div>
        ) : null}
      </Panel>

      <div className="grid gap-8 xl:grid-cols-[1.1fr_0.9fr]">
        <Panel eyebrow="Profiles" title="Network visibility by branch">
          <div className="space-y-4">
            {dashboard.profiles.map((profile) => (
              <article
                key={profile.id}
                className="flex flex-col justify-between gap-3 rounded-3xl border border-ink/10 bg-sand/45 p-5 md:flex-row md:items-center"
              >
                <div>
                  <h3 className="text-lg font-semibold">{profile.business_name}</h3>
                  <p className="text-sm text-ink/60">
                    {profile.city}, {profile.state} · {profile.brand}
                  </p>
                </div>
                <div className="grid gap-2 text-sm text-ink/70 md:text-right">
                  <span>Rating {profile.avg_rating_cached.toFixed(1)}</span>
                  <span>{profile.total_reviews_cached} reviews</span>
                  <span>{profile.primary_local_admin_name ?? "Unassigned"}</span>
                </div>
              </article>
            ))}
          </div>
        </Panel>

        <Panel eyebrow="Reviews" title="Most recent customer signals">
          <div className="mb-5 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="flex flex-nowrap gap-2 overflow-x-auto pb-1">
              {[
                { key: "all", label: "All" },
                { key: "positive", label: "Positive" },
                { key: "negative", label: "Negative" },
              ].map((option) => {
                const active = reviewSentiment === option.key;
                return (
                  <button
                    key={option.key}
                    type="button"
                    onClick={() => handleReviewSentimentChange(option.key as "all" | "positive" | "negative")}
                    className={[
                      "shrink-0 rounded-full border px-4 py-2 text-sm transition",
                      active
                        ? "border-pine bg-pine text-sand shadow-sm"
                        : "border-ink/15 bg-white/70 text-ink hover:border-pine/40 hover:bg-pine/10",
                    ].join(" ")}
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>
            <label className="flex flex-col gap-2 text-sm text-ink/65 lg:min-w-72">
              <span className="text-xs uppercase tracking-[0.2em] text-ink/45">Branch</span>
              <select
                value={reviewBranchId}
                onChange={(event) => handleReviewBranchChange(event.target.value)}
                className="rounded-2xl border border-ink/15 bg-white/80 px-4 py-3 text-sm text-ink outline-none transition focus:border-pine"
              >
                <option value="all">All branches</option>
                {branchProfiles.map((profile) => (
                  <option key={profile.id} value={profile.id}>
                    {profile.business_name}
                    {profile.city ? ` · ${profile.city}` : ""}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {reviewFeed ? (
            <>
              {reviewFeed.items.length ? (
                <div className="space-y-4">
                  {reviewFeed.items.map((review) => (
                    <article key={review.id} className="rounded-3xl border border-ink/10 bg-white/70 p-5">
                      <div className="flex items-center justify-between gap-4">
                        <h3 className="font-semibold">{review.business_name}</h3>
                        <span className="text-sm uppercase tracking-[0.2em] text-rust">
                          {review.sentiment}
                        </span>
                      </div>
                      <p className="mt-2 text-sm text-ink/55">
                        {review.reviewer_name ?? "Anonymous"} · {review.star_rating} stars
                      </p>
                      <p className="mt-3 text-sm leading-7 text-ink/75">{review.review_text}</p>
                      {review.reply_text ? (
                        <p className="mt-3 rounded-2xl bg-pine/8 px-4 py-3 text-sm text-pine">
                          Reply: {review.reply_text}
                        </p>
                      ) : null}
                    </article>
                  ))}
                </div>
              ) : (
                <div className="rounded-3xl border border-dashed border-ink/15 bg-sand/35 p-6 text-sm text-ink/60">
                  No reviews match the current filters.
                </div>
              )}

              <div className="mt-6 flex flex-col gap-3 border-t border-ink/10 pt-4 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm text-ink/55">
                  {reviewFeed.total
                    ? `Showing ${reviewRangeStart}-${reviewRangeEnd} of ${reviewFeed.total} reviews`
                    : "No reviews available for the selected filters"}
                </p>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setReviewPage((current) => Math.max(1, current - 1))}
                    disabled={reviewFeed.page <= 1}
                    className="rounded-full border border-ink/15 bg-white px-4 py-2 text-sm uppercase tracking-[0.2em] text-ink transition hover:border-pine hover:bg-pine/10 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    Prev
                  </button>
                  <span className="rounded-full border border-ink/10 bg-sand/45 px-4 py-2 text-xs uppercase tracking-[0.2em] text-ink/60">
                    Page {reviewFeed.page} of {reviewFeed.total_pages || 1}
                  </span>
                  <button
                    type="button"
                    onClick={() => setReviewPage((current) => current + 1)}
                    disabled={reviewFeed.total_pages === 0 || reviewFeed.page >= reviewFeed.total_pages}
                    className="rounded-full border border-ink/15 bg-white px-4 py-2 text-sm uppercase tracking-[0.2em] text-ink transition hover:border-pine hover:bg-pine/10 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    Next
                  </button>
                </div>
              </div>
            </>
          ) : (
            <p className="text-sm text-ink/60">Loading reviews...</p>
          )}
        </Panel>
      </div>
    </section>
  );
}
