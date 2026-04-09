import { useEffect, useMemo, useState, type FormEvent } from "react";

import { Panel } from "../components/Panel";
import { useAuth } from "../app/AuthContext";
import { createUser, fetchUsers, updateUser, type UserListItem } from "../lib/api";

export function UsersPage() {
  const { accessToken, memberships } = useAuth();
  const isMasterAdmin = useMemo(
    () => memberships.some((membership) => membership.role === "master_admin"),
    [memberships],
  );
  const [users, setUsers] = useState<UserListItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [savingUserId, setSavingUserId] = useState<string | null>(null);
  const [editUser, setEditUser] = useState<UserListItem | null>(null);
  const [editForm, setEditForm] = useState({
    email: "",
    full_name: "",
    phone_number: "",
    role: "local_admin",
    email_alerts_enabled: false,
    whatsapp_alerts_enabled: false,
    is_active: true,
  });
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

  function openEditUser(user: UserListItem) {
    setEditUser(user);
    setEditForm({
      email: user.email,
      full_name: user.full_name,
      phone_number: user.phone_number ?? "",
      role: user.role,
      email_alerts_enabled: user.email_alerts_enabled,
      whatsapp_alerts_enabled: user.whatsapp_alerts_enabled,
      is_active: user.is_active,
    });
  }

  function closeEditUser() {
    setEditUser(null);
  }

  async function handleUpdateUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken || !editUser) return;
    setSavingUserId(editUser.id);
    try {
      await updateUser(accessToken, editUser.id, {
        email: editForm.email,
        full_name: editForm.full_name,
        phone_number: editForm.phone_number.trim() || undefined,
        role: editForm.role,
        email_alerts_enabled: editForm.email_alerts_enabled,
        whatsapp_alerts_enabled: editForm.whatsapp_alerts_enabled,
        is_active: editForm.is_active,
      });
      closeEditUser();
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
                    <div className="flex flex-wrap gap-2">
                      {isMasterAdmin ? (
                        <button
                          type="button"
                          onClick={() => openEditUser(user)}
                          className="rounded-full border border-ink/15 px-4 py-2 text-xs uppercase tracking-[0.2em] transition hover:border-pine hover:text-pine"
                        >
                          Edit
                        </button>
                      ) : null}
                      <button
                        type="button"
                        disabled={savingUserId === user.id}
                        onClick={() => void handleToggleStatus(user)}
                        className="rounded-full border border-ink/15 px-4 py-2 text-xs uppercase tracking-[0.2em] transition hover:border-rust hover:text-rust disabled:opacity-70"
                      >
                        {user.is_active ? "Suspend" : "Reactivate"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      {editUser ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 px-4 py-8 backdrop-blur-sm">
          <div className="w-full max-w-xl rounded-[2rem] border border-ink/10 bg-sand p-6 shadow-2xl">
            <div className="mb-6 flex items-start justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-rust">Edit user</p>
                <h3 className="mt-2 font-display text-3xl">{editUser.full_name}</h3>
                <p className="mt-1 text-sm text-ink/55">{editUser.email}</p>
              </div>
              <button
                type="button"
                onClick={closeEditUser}
                className="rounded-full border border-ink/10 px-3 py-2 text-xs uppercase tracking-[0.2em] transition hover:border-rust hover:text-rust"
              >
                Close
              </button>
            </div>

            <form className="grid gap-4" onSubmit={handleUpdateUser}>
              <label className="grid gap-2 text-sm text-ink/65">
                Email
                <input
                  className="rounded-2xl border border-ink/10 bg-white px-4 py-3 outline-none focus:border-pine dark:bg-ink/5"
                  value={editForm.email}
                  onChange={(event) =>
                    setEditForm((current) => ({ ...current, email: event.target.value }))
                  }
                />
              </label>
              <label className="grid gap-2 text-sm text-ink/65">
                Full name
                <input
                  className="rounded-2xl border border-ink/10 bg-white px-4 py-3 outline-none focus:border-pine dark:bg-ink/5"
                  value={editForm.full_name}
                  onChange={(event) =>
                    setEditForm((current) => ({ ...current, full_name: event.target.value }))
                  }
                />
              </label>
              <label className="grid gap-2 text-sm text-ink/65">
                Phone number
                <input
                  className="rounded-2xl border border-ink/10 bg-white px-4 py-3 outline-none focus:border-pine dark:bg-ink/5"
                  value={editForm.phone_number}
                  onChange={(event) =>
                    setEditForm((current) => ({ ...current, phone_number: event.target.value }))
                  }
                />
              </label>
              <label className="grid gap-2 text-sm text-ink/65">
                Role
                <select
                  className="rounded-2xl border border-ink/10 bg-white px-4 py-3 outline-none focus:border-pine dark:bg-ink/5"
                  value={editForm.role}
                  onChange={(event) => setEditForm((current) => ({ ...current, role: event.target.value }))}
                >
                  <option value="local_admin">Local Admin</option>
                  <option value="master_admin">Master Admin</option>
                </select>
              </label>
              <div className="grid gap-3 rounded-2xl border border-ink/10 bg-white/70 p-4 dark:bg-ink/5">
                <label className="flex items-center justify-between gap-4 text-sm text-ink/65">
                  Email alerts
                  <input
                    type="checkbox"
                    checked={editForm.email_alerts_enabled}
                    onChange={(event) =>
                      setEditForm((current) => ({
                        ...current,
                        email_alerts_enabled: event.target.checked,
                      }))
                    }
                  />
                </label>
                <label className="flex items-center justify-between gap-4 text-sm text-ink/65">
                  WhatsApp alerts
                  <input
                    type="checkbox"
                    checked={editForm.whatsapp_alerts_enabled}
                    onChange={(event) =>
                      setEditForm((current) => ({
                        ...current,
                        whatsapp_alerts_enabled: event.target.checked,
                      }))
                    }
                  />
                </label>
                <label className="flex items-center justify-between gap-4 text-sm text-ink/65">
                  Active
                  <input
                    type="checkbox"
                    checked={editForm.is_active}
                    onChange={(event) =>
                      setEditForm((current) => ({
                        ...current,
                        is_active: event.target.checked,
                      }))
                    }
                  />
                </label>
              </div>

              <div className="mt-2 flex flex-wrap justify-end gap-3">
                <button
                  type="button"
                  onClick={closeEditUser}
                  className="rounded-full border border-ink/15 px-5 py-3 text-xs uppercase tracking-[0.2em] transition hover:border-rust hover:text-rust"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingUserId === editUser.id}
                  className="rounded-full bg-pine px-5 py-3 text-xs uppercase tracking-[0.2em] text-sand transition hover:bg-ink disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {savingUserId === editUser.id ? "Saving..." : "Save changes"}
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </div>
  );
}
