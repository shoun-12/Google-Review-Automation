export function MetricCard({
  label,
  value,
  tone = "pine",
}: {
  label: string;
  value: string;
  tone?: "pine" | "rust" | "gold";
}) {
  const toneClass = {
    pine: "text-pine",
    rust: "text-rust",
    gold: "text-gold",
  }[tone];

  return (
    <article className="rounded-3xl border border-ink/10 bg-white p-6 shadow-sm">
      <p className="text-sm uppercase tracking-[0.2em] text-ink/50">{label}</p>
      <p className={`mt-4 font-display text-5xl ${toneClass}`}>{value}</p>
    </article>
  );
}
