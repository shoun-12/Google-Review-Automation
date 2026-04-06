import { useEffect, useState, type FormEvent } from "react";

import { Panel } from "../components/Panel";
import { useAuth } from "../app/AuthContext";
import { createUser, fetchUsers, updateUser, type UserListItem } from "../lib/api";

export function UsersPage() {
  const { accessToken } = useAuth();
  const [users, setUsers] = useState<UserListItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [savingUserId, setSavingUserId] = useState<string | null>(null);
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    phone_number: "",
    role: "local_admin",
    password: "ChangeMe123!",
  });

  async function loadUsers() {
    if (!accessToken) return;
    try {
      const response = await fetchUsers(accessToken);
      setUsers(response.items);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load users");
    }
  }

  useEffect(() => {
    void loadUsers();
  }, [accessToken]);

  async function handleCreateUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken) return;
    try {
      await createUser(accessToken, {
        ...form,
        email_alerts_enabled: false,
        whatsapp_alerts_enabled: false,
      });
      setForm({
        full_name: "",
        email: "",
        phone_number: "",
        role: "local_admin",
        password: "ChangeMe123!",
      });
      await loadUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create user");
    }
  }

  async function handleToggleStatus(user: UserListItem) {
    if (!accessToken) return;
    setSavingUserId(user.id);
    try {
      await updateUser(accessToken, user.id, { is_active: !user.is_active });
      await loadUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update user");
    } finally {
      setSavingUserId(null);
    }
  }

  return (
    <div className="grid gap-8 xl:grid-cols-[0.9fr_1.1fr]">
      <Panel eyebrow="Invite" title="Create internal users">
        <form className="space-y-4" onSubmit={handleCreateUser}>
          <input
            className="w-full rounded-2xl border border-ink/10 bg-sand/50 px-4 py-3"
            placeholder="Full name"
            value={form.full_name}
            onChange={(event) => setForm((current) => ({ ...current, full_name: event.target.value }))}
          />
          <input
            className="w-full rounded-2xl border border-ink/10 bg-sand/50 px-4 py-3"
            placeholder="Email"
            value={form.email}
            onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
          />
          <input
            className="w-full rounded-2xl border border-ink/10 bg-sand/50 px-4 py-3"
            placeholder="Phone number"
            value={form.phone_number}
            onChange={(event) => setForm((current) => ({ ...current, phone_number: event.target.value }))}
          />
          <select
            className="w-full rounded-2xl border border-ink/10 bg-sand/50 px-4 py-3"
            value={form.role}
            onChange={(event) => setForm((current) => ({ ...current, role: event.target.value }))}
          >
            <option value="local_admin">Local Admin</option>
            <option value="master_admin">Master Admin</option>
          </select>
          <input
            className="w-full rounded-2xl border border-ink/10 bg-sand/50 px-4 py-3"
            placeholder="Temporary password"
            value={form.password}
            onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
          />
          <button type="submit" className="rounded-full bg-pine px-5 py-3 text-sm uppercase tracking-[0.2em] text-sand">
            Create User
          </button>
        </form>
      </Panel>

      <Panel eyebrow="Users" title="Tenant access and branch ownership">
        {error ? <p className="mb-4 text-rust">{error}</p> : null}
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-ink/10 text-ink/50">
              <tr>
                <th className="pb-3">Name</th>
                <th className="pb-3">Email</th>
                <th className="pb-3">Role</th>
                <th className="pb-3">Alerts</th>
                <th className="pb-3">Status</th>
                <th className="pb-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="border-b border-ink/5">
                  <td className="py-4">{user.full_name}</td>
                  <td className="py-4">{user.email}</td>
                  <td className="py-4 capitalize">{user.role.replaceAll("_", " ")}</td>
                  <td className="py-4">
                    {user.email_alerts_enabled ? "Email" : ""}
                    {user.email_alerts_enabled && user.whatsapp_alerts_enabled ? " + " : ""}
                    {user.whatsapp_alerts_enabled ? "WhatsApp" : ""}
                    {!user.email_alerts_enabled && !user.whatsapp_alerts_enabled ? "Off" : ""}
                  </td>
                  <td className="py-4">{user.is_active ? "Active" : "Suspended"}</td>
                  <td className="py-4">
                    <button
                      type="button"
                      disabled={savingUserId === user.id}
                      onClick={() => void handleToggleStatus(user)}
                      className="rounded-full border border-ink/15 px-4 py-2 text-xs uppercase tracking-[0.2em]"
                    >
                      {user.is_active ? "Suspend" : "Reactivate"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}
