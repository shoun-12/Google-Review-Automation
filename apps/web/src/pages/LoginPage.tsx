import { useState, type FormEvent } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "../app/AuthContext";

export function LoginPage() {
  const { accessToken, login } = useAuth();
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("ChangeMe123!");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (accessToken) {
    return <Navigate to="/" replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-sand px-6 py-10 text-ink md:px-8 xl:px-10">
      <div className="grid w-full gap-8 lg:grid-cols-[1.15fr_0.85fr]">
        <section className="rounded-[2.5rem] border border-ink/10 bg-[linear-gradient(135deg,#18453b_0%,#122b25_55%,#0f172a_100%)] p-10 text-sand shadow-xl">
          <p className="text-sm uppercase tracking-[0.3em] text-gold">Private Dashboard</p>
          <h1 className="mt-4 font-display text-5xl leading-tight">
            Review operations for every branch, in one control room.
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-8 text-sand/75">
            This build includes shared internal sign-in for Master Admin and Local Admin users,
            tenant-aware data access, seeded users, profiles, reviews, reply templates, and
            reporting endpoints so development can continue on real application flows instead
            of placeholders.
          </p>
        </section>

        <section className="rounded-[2.5rem] border border-ink/10 bg-white p-8 shadow-xl">
          <p className="text-sm uppercase tracking-[0.3em] text-rust">Sign In</p>
          <h2 className="mt-3 font-display text-4xl">Internal User Access</h2>
          <p className="mt-3 text-sm leading-7 text-ink/60">
            Use this page for both Master Admin and Local Admin accounts.
          </p>
          <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
            <label className="block">
              <span className="mb-2 block text-sm uppercase tracking-[0.2em] text-ink/55">
                Email
              </span>
              <input
                className="w-full rounded-2xl border border-ink/10 bg-sand/40 px-4 py-4 outline-none transition focus:border-pine"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm uppercase tracking-[0.2em] text-ink/55">
                Password
              </span>
              <input
                type="password"
                className="w-full rounded-2xl border border-ink/10 bg-sand/40 px-4 py-4 outline-none transition focus:border-pine"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </label>
            {error ? <p className="text-sm text-rust">{error}</p> : null}
            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-2xl bg-pine px-5 py-4 text-sm uppercase tracking-[0.2em] text-sand transition hover:bg-ink disabled:cursor-not-allowed disabled:opacity-70"
            >
              {submitting ? "Signing In..." : "Sign In"}
            </button>
          </form>
          <div className="mt-8 rounded-2xl border border-ink/10 bg-sand/50 p-4 text-sm leading-7 text-ink/70">
            <p>Default seed master admin:</p>
            <p>`admin@example.com` / `ChangeMe123!`</p>
          </div>
        </section>
      </div>
    </div>
  );
}
