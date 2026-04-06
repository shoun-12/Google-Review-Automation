import { useEffect, useState } from "react";

import { useAuth } from "../app/AuthContext";
import { Panel } from "../components/Panel";
import {
  fetchProfiles,
  fetchUsers,
  updateProfile,
  type Profile,
  type UserListItem,
} from "../lib/api";

export function ProfilesPage() {
  const { accessToken, memberships } = useAuth();
  const isMasterAdmin = memberships[0]?.role === "master_admin";
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [localAdmins, setLocalAdmins] = useState<UserListItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [savingId, setSavingId] = useState<string | null>(null);

  async function loadData() {
    if (!accessToken) return;
    try {
      const profilesResponse = await fetchProfiles(accessToken);
      setProfiles(profilesResponse.items);
      if (isMasterAdmin) {
        const usersResponse = await fetchUsers(accessToken);
        setLocalAdmins(usersResponse.items.filter((user) => user.role === "local_admin"));
      } else {
        setLocalAdmins([]);
      }
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load profiles");
    }
  }

  useEffect(() => {
    void loadData();
  }, [accessToken, isMasterAdmin]);

  async function handleAssignment(profileId: string, adminId: string) {
    if (!accessToken) return;
    setSavingId(profileId);
    try {
      await updateProfile(accessToken, profileId, {
        primary_local_admin_user_id: adminId || null,
      });
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update profile");
    } finally {
      setSavingId(null);
    }
  }

  async function handleToggle(profile: Profile, field: "auto_respond_enabled" | "is_active") {
    if (!accessToken) return;
    setSavingId(profile.id);
    try {
      await updateProfile(accessToken, profile.id, {
        [field]: !profile[field],
      });
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update profile");
    } finally {
      setSavingId(null);
    }
  }

  return (
    <Panel eyebrow="Profiles" title="Branch ownership and response controls">
      {error ? <p className="mb-4 text-rust">{error}</p> : null}
      <div className="space-y-4">
        {profiles.map((profile) => (
          <article key={profile.id} className="rounded-3xl border border-ink/10 bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div>
                <h3 className="text-lg font-semibold">{profile.business_name}</h3>
                <p className="mt-1 text-sm text-ink/55">
                  {profile.city}, {profile.state} · {profile.brand}
                </p>
                <p className="mt-2 text-sm text-ink/65">
                  Rating {profile.avg_rating_cached.toFixed(1)} · {profile.total_reviews_cached} reviews
                </p>
              </div>
              {isMasterAdmin ? (
                <div className="grid gap-3 md:min-w-72">
                  <label className="text-sm text-ink/65">
                    Local Admin
                    <select
                      className="mt-2 w-full rounded-2xl border border-ink/10 bg-sand/50 px-4 py-3"
                      value={profile.primary_local_admin_user_id ?? ""}
                      onChange={(event) => void handleAssignment(profile.id, event.target.value)}
                      disabled={savingId === profile.id}
                    >
                      <option value="">Unassigned</option>
                      {localAdmins.map((user) => (
                        <option key={user.id} value={user.id}>
                          {user.full_name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={() => void handleToggle(profile, "auto_respond_enabled")}
                      className="rounded-full border border-ink/15 px-4 py-2 text-sm"
                    >
                      Auto Reply: {profile.auto_respond_enabled ? "On" : "Off"}
                    </button>
                    <button
                      type="button"
                      onClick={() => void handleToggle(profile, "is_active")}
                      className="rounded-full border border-ink/15 px-4 py-2 text-sm"
                    >
                      Status: {profile.is_active ? "Active" : "Inactive"}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="grid gap-2 text-sm text-ink/70 md:text-right">
                  <span>{profile.primary_local_admin_name ?? "Assigned locally"}</span>
                  <span>Auto Reply: {profile.auto_respond_enabled ? "On" : "Off"}</span>
                  <span>Status: {profile.is_active ? "Active" : "Inactive"}</span>
                </div>
              )}
            </div>
          </article>
        ))}
      </div>
    </Panel>
  );
}
