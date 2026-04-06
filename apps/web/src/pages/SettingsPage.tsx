import { useEffect, useState, type FormEvent } from "react";

import { useAuth } from "../app/AuthContext";
import { Panel } from "../components/Panel";
import {
  createTemplate,
  fetchGoogleAccounts,
  fetchTemplates,
  updateTemplate,
  type GoogleAccount,
  type ReplyTemplate,
} from "../lib/api";

export function SettingsPage() {
  const { accessToken } = useAuth();
  const [accounts, setAccounts] = useState<GoogleAccount[]>([]);
  const [templates, setTemplates] = useState<ReplyTemplate[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [editingTemplateId, setEditingTemplateId] = useState<string | null>(null);
  const [form, setForm] = useState({
    brand: "maruti",
    sentiment: "negative",
    template_text: "",
    is_active: true,
  });

  async function loadSettings() {
    if (!accessToken) return;

    try {
      const [accountsResponse, templatesResponse] = await Promise.all([
        fetchGoogleAccounts(accessToken),
        fetchTemplates(accessToken),
      ]);
      setAccounts(accountsResponse.items);
      setTemplates(templatesResponse.items);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load settings");
    }
  }

  useEffect(() => {
    void loadSettings();
  }, [accessToken]);

  async function handleTemplateSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken) return;

    try {
      if (editingTemplateId) {
        await updateTemplate(accessToken, editingTemplateId, form);
      } else {
        await createTemplate(accessToken, form);
      }
      setForm({
        brand: "maruti",
        sentiment: "negative",
        template_text: "",
        is_active: true,
      });
      setEditingTemplateId(null);
      await loadSettings();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save template");
    }
  }

  return (
    <div className="grid gap-8 xl:grid-cols-2">
      <Panel eyebrow="Google Accounts" title="Connected account inventory">
        {error ? <p className="text-rust">{error}</p> : null}
        <div className="space-y-4">
          {accounts.map((account) => (
            <article key={account.id} className="rounded-3xl border border-ink/10 bg-sand/40 p-5">
              <h3 className="font-semibold">{account.email}</h3>
              <p className="mt-2 text-sm text-ink/60">{account.google_account_id ?? "No Google ID yet"}</p>
              <p className="mt-2 text-sm text-ink/60">{account.scopes_json.join(", ")}</p>
            </article>
          ))}
        </div>
      </Panel>

      <Panel eyebrow="Templates" title="Reply templates by brand">
        <form className="mb-6 space-y-3" onSubmit={handleTemplateSubmit}>
          <div className="grid gap-3 md:grid-cols-2">
            <select
              className="rounded-2xl border border-ink/10 bg-sand/50 px-4 py-3"
              value={form.brand}
              onChange={(event) => setForm((current) => ({ ...current, brand: event.target.value }))}
            >
              <option value="maruti">Maruti</option>
              <option value="kuttukaran">Kuttukaran</option>
              <option value="other">Other</option>
            </select>
            <select
              className="rounded-2xl border border-ink/10 bg-sand/50 px-4 py-3"
              value={form.sentiment}
              onChange={(event) => setForm((current) => ({ ...current, sentiment: event.target.value }))}
            >
              <option value="negative">Negative</option>
              <option value="positive">Positive</option>
            </select>
          </div>
          <textarea
            className="min-h-32 w-full rounded-2xl border border-ink/10 bg-sand/50 px-4 py-3"
            placeholder="Reply template text"
            value={form.template_text}
            onChange={(event) => setForm((current) => ({ ...current, template_text: event.target.value }))}
          />
          <label className="flex items-center gap-2 text-sm text-ink/65">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(event) => setForm((current) => ({ ...current, is_active: event.target.checked }))}
            />
            Active template
          </label>
          <div className="flex gap-3">
            <button type="submit" className="rounded-full bg-pine px-5 py-3 text-sm uppercase tracking-[0.2em] text-sand">
              {editingTemplateId ? "Update Template" : "Create Template"}
            </button>
            {editingTemplateId ? (
              <button
                type="button"
                className="rounded-full border border-ink/15 px-5 py-3 text-sm uppercase tracking-[0.2em]"
                onClick={() => {
                  setEditingTemplateId(null);
                  setForm({
                    brand: "maruti",
                    sentiment: "negative",
                    template_text: "",
                    is_active: true,
                  });
                }}
              >
                Cancel
              </button>
            ) : null}
          </div>
        </form>
        <div className="space-y-4">
          {templates.map((template) => (
            <article key={template.id} className="rounded-3xl border border-ink/10 bg-white/90 p-5">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold capitalize">
                  {template.brand} · {template.sentiment}
                </h3>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-ink/55">{template.is_active ? "Active" : "Inactive"}</span>
                  <button
                    type="button"
                    className="rounded-full border border-ink/15 px-3 py-1 text-xs uppercase tracking-[0.2em]"
                    onClick={() => {
                      setEditingTemplateId(template.id);
                      setForm({
                        brand: template.brand,
                        sentiment: template.sentiment,
                        template_text: template.template_text,
                        is_active: template.is_active,
                      });
                    }}
                  >
                    Edit
                  </button>
                </div>
              </div>
              <p className="mt-3 text-sm leading-7 text-ink/75">{template.template_text}</p>
            </article>
          ))}
        </div>
      </Panel>
    </div>
  );
}
