import { useEffect, useMemo, useState } from "react";

import { useAuth } from "../app/AuthContext";
import { MetricCard } from "../components/MetricCard";
import { Panel } from "../components/Panel";
import {
  downloadProfilesCsv,
  fetchReportOverview,
  type ProfilePerformanceItem,
  type ReportOverview,
  type TrendPoint,
} from "../lib/api";

const dayOptions = [7, 14, 30, 60];

function TrendRows({ trend }: { trend: TrendPoint[] }) {
  const maxReviews = useMemo(
    () => Math.max(...trend.map((item) => item.reviews_received), 1),
    [trend],
  );

  return (
    <div className="space-y-3">
      {trend.map((point) => (
        <article
          key={point.date}
          className="rounded-3xl border border-ink/10 bg-sand/45 p-4"
        >
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <h3 className="text-sm font-semibold text-ink">
                {new Date(point.date).toLocaleDateString()}
              </h3>
              <p className="text-xs uppercase tracking-[0.2em] text-ink/45">
                {point.reviews_received} reviews · {point.replies_posted} replies
              </p>
            </div>
            <div className="text-sm text-ink/60">
              Avg rating {point.avg_rating.toFixed(1)}
            </div>
          </div>
          <div className="mt-4 h-3 overflow-hidden rounded-full bg-white">
            <div
              className="h-full rounded-full bg-pine"
              style={{ width: `${(point.reviews_received / maxReviews) * 100}%` }}
            />
          </div>
          <div className="mt-3 flex gap-4 text-xs uppercase tracking-[0.15em] text-ink/55">
            <span>Positive {point.positive_reviews}</span>
            <span>Negative {point.negative_reviews}</span>
          </div>
        </article>
      ))}
    </div>
  );
}

function ProfileRows({ profiles }: { profiles: ProfilePerformanceItem[] }) {
  return (
    <div className="space-y-3">
      {profiles.map((profile) => (
        <article
          key={profile.id}
          className="rounded-3xl border border-ink/10 bg-white/80 p-5"
        >
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div>
              <h3 className="text-base font-semibold">{profile.business_name}</h3>
              <p className="mt-1 text-sm text-ink/55">
                {profile.city ?? "Unknown city"}, {profile.state ?? "Unknown state"} · {profile.brand}
              </p>
            </div>
            <div className="grid gap-1 text-sm text-ink/65 md:text-right">
              <span>{profile.reviews_received} reviews</span>
              <span>{Math.round(profile.response_rate * 100)}% response rate</span>
              <span>{profile.avg_rating.toFixed(1)} avg rating</span>
            </div>
          </div>
          <div className="mt-4 grid gap-3 text-sm text-ink/70 md:grid-cols-3">
            <div className="rounded-2xl bg-sand/50 px-4 py-3">
              Positive {profile.positive_reviews}
            </div>
            <div className="rounded-2xl bg-sand/50 px-4 py-3">
              Negative {profile.negative_reviews}
            </div>
            <div className="rounded-2xl bg-sand/50 px-4 py-3">
              Replies {profile.replies_posted}
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}

export function ReportsPage() {
  const { accessToken } = useAuth();
  const [days, setDays] = useState(30);
  const [overview, setOverview] = useState<ReportOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    if (!accessToken) return;
    fetchReportOverview(accessToken, days)
      .then((response) => {
        setOverview(response);
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load reports"));
  }, [accessToken, days]);

  async function handleDownload() {
    if (!accessToken) return;
    setDownloading(true);
    try {
      const blob = await downloadProfilesCsv(accessToken, days);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `profile-performance-${days}d.csv`;
      link.click();
      window.URL.revokeObjectURL(url);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to export CSV");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <section className="space-y-8">
      {error ? (
        <div className="rounded-3xl border border-rust/20 bg-rust/10 px-5 py-4 text-sm text-rust">
          {error}
        </div>
      ) : null}

      <Panel eyebrow="Reports" title="Review performance and response coverage">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-wrap gap-2">
            {dayOptions.map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setDays(option)}
                className={[
                  "rounded-full border px-4 py-2 text-sm",
                  days === option
                    ? "border-pine bg-pine text-sand"
                    : "border-ink/15 bg-white/70 text-ink",
                ].join(" ")}
              >
                Last {option} days
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={handleDownload}
            disabled={downloading}
            className="rounded-full border border-ink/15 bg-white px-5 py-3 text-sm uppercase tracking-[0.2em] text-ink disabled:opacity-50"
          >
            {downloading ? "Preparing..." : "Export CSV"}
          </button>
        </div>
      </Panel>

      {overview ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              label="Connected Profiles"
              value={String(overview.summary.total_connected_profiles)}
            />
            <MetricCard label="Reviews Received" value={String(overview.summary.reviews_received)} tone="rust" />
            <MetricCard
              label="Positive Reviews"
              value={String(overview.summary.positive_reviews)}
              tone="gold"
            />
            <MetricCard
              label="Network Rating"
              value={overview.summary.average_rating_network.toFixed(1)}
            />
          </div>

          <div className="grid gap-8 xl:grid-cols-[0.85fr_1.15fr]">
            <Panel eyebrow="Trend" title={`Daily review flow for the last ${overview.window_days} days`}>
              <TrendRows trend={overview.trend} />
            </Panel>
            <Panel eyebrow="Branches" title="Profile-level performance">
              <ProfileRows profiles={overview.profiles} />
            </Panel>
          </div>
        </>
      ) : (
        <p className="text-ink/60">Loading reports...</p>
      )}
    </section>
  );
}
