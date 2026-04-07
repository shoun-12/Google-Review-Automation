import type { ReactNode } from "react";

export function Panel({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-[2rem] border border-ink/10 bg-white p-8 shadow-sm dark:shadow-[0_10px_30px_rgba(0,0,0,0.22)]">
      <p className="text-sm uppercase tracking-[0.2em] text-rust">{eyebrow}</p>
      <h2 className="mt-3 font-display text-3xl">{title}</h2>
      <div className="mt-6">{children}</div>
    </section>
  );
}
