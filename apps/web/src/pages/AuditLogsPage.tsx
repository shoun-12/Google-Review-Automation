import { useEffect, useState } from "react";

import { useAuth } from "../app/AuthContext";
import { Panel } from "../components/Panel";
import { fetchAuditLogs, type AuditLogItem } from "../lib/api";

function formatLabel(value: string) {
  return value.replaceAll("_", " ").replaceAll(".", " ");
}

function formatMetadataValue(value: unknown): string {
  if (value === null || value === undefined) return "Not set";
  if (Array.isArray(value)) return value.length ? value.join(", ") : "None";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export function AuditLogsPage() {
  const { accessToken } = useAuth();
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    fetchAuditLogs(accessToken)
      .then((response) => {
        setLogs(response.items);
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load audit logs"));
  }, [accessToken]);

  return (
    <Panel eyebrow="Audit" title="Operational event history">
      {error ? <p className="mb-4 text-rust">{error}</p> : null}
      <div className="space-y-4">
        {!logs.length && !error ? (
          <div className="rounded-3xl border border-dashed border-ink/15 bg-sand/35 p-6 text-sm text-ink/60">
            No audit activity has been recorded yet.
          </div>
        ) : null}
        {logs.map((log) => (
          <article key={log.id} className="rounded-3xl border border-ink/10 bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <h3 className="text-base font-semibold capitalize">{formatLabel(log.action)}</h3>
                <p className="mt-1 text-sm text-ink/55">
                  {formatLabel(log.target_type)}
                  {log.target_id ? ` · ${log.target_id}` : ""}
                </p>
              </div>
              <p className="text-sm text-ink/55">{new Date(log.created_at).toLocaleString()}</p>
            </div>
            {Object.keys(log.metadata_json).length ? (
              <div className="mt-4 rounded-2xl bg-sand/50 p-4">
                <div className="grid gap-3 md:grid-cols-2">
                  {Object.entries(log.metadata_json).map(([key, value]) => (
                    <div key={key} className="rounded-2xl bg-white/80 px-4 py-3">
                      <p className="text-xs uppercase tracking-[0.18em] text-ink/45">
                        {formatLabel(key)}
                      </p>
                      <p className="mt-2 break-words text-sm leading-6 text-ink/70">
                        {formatMetadataValue(value)}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </article>
        ))}
      </div>
    </Panel>
  );
}
