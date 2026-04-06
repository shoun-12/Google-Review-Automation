import { useEffect, useState } from "react";

import { useAuth } from "../app/AuthContext";
import { Panel } from "../components/Panel";
import { fetchReviews, type Review } from "../lib/api";

export function ReviewsPage() {
  const { accessToken } = useAuth();
  const [reviews, setReviews] = useState<Review[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    fetchReviews(accessToken)
      .then((response) => setReviews(response.items))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load reviews"));
  }, [accessToken]);

  return (
    <Panel eyebrow="Reviews" title="Review feed">
      {error ? <p className="text-rust">{error}</p> : null}
      <div className="space-y-4">
        {reviews.map((review) => (
          <article key={review.id} className="rounded-3xl border border-ink/10 bg-sand/40 p-5">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h3 className="font-semibold">{review.business_name}</h3>
                <p className="text-sm text-ink/55">
                  {review.reviewer_name ?? "Anonymous"} · {review.star_rating} stars
                </p>
              </div>
              <div className="text-right text-sm">
                <p className="uppercase tracking-[0.2em] text-rust">{review.sentiment}</p>
                <p className="text-ink/55">{review.status}</p>
              </div>
            </div>
            <p className="mt-3 text-sm leading-7 text-ink/75">{review.review_text}</p>
            {review.reply_text ? (
              <p className="mt-3 rounded-2xl bg-pine/8 px-4 py-3 text-sm text-pine">
                Reply: {review.reply_text}
              </p>
            ) : null}
          </article>
        ))}
      </div>
    </Panel>
  );
}
