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
    pine: "text-pine dark:text-[#8dd7c3]",
    rust: "text-rust dark:text-[#f19a7b]",
    gold: "text-gold dark:text-[#f0c86a]",
  }[tone];

  return (
    <article className="rounded-3xl border border-ink/10 bg-white p-6 shadow-sm dark:shadow-[0_10px_30px_rgba(0,0,0,0.22)]">
      <p className="text-sm uppercase tracking-[0.2em] text-ink/50">{label}</p>
      <p className={`mt-4 font-display text-5xl ${toneClass}`}>{value}</p>
    </article>
  );
}
