import { useState, type ReactNode } from "react";
import { NavLink, Route, Routes, useLocation } from "react-router-dom";

import { AuthProvider, useAuth } from "./AuthContext";
import { ProtectedRoute } from "./ProtectedRoute";
import { AuditLogsPage } from "../pages/AuditLogsPage";
import { DashboardPage } from "../pages/DashboardPage";
import { LoginPage } from "../pages/LoginPage";
import { ProfilesPage } from "../pages/ProfilesPage";
import { ReportsPage } from "../pages/ReportsPage";
import { ReviewsPage } from "../pages/ReviewsPage";
import { SettingsPage } from "../pages/SettingsPage";
import { UsersPage } from "../pages/UsersPage";

function IconShell({ children }: { children: ReactNode }) {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8">
      {children}
    </svg>
  );
}

function DashboardIcon() {
  return (
    <IconShell>
      <path d="M4 13.5c0-4.97 3.58-9 8-9v9H4Z" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M12 4.5a8 8 0 1 1-8 8" strokeLinecap="round" strokeLinejoin="round" />
    </IconShell>
  );
}

function ReportsIcon() {
  return (
    <IconShell>
      <path d="M6 18V9" strokeLinecap="round" />
      <path d="M12 18V5" strokeLinecap="round" />
      <path d="M18 18v-7" strokeLinecap="round" />
    </IconShell>
  );
}

function ProfilesIcon() {
  return (
    <IconShell>
      <path d="M4 7h16l-2 5H6L4 7Z" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M7 17a1 1 0 1 0 0 .01" strokeLinecap="round" />
      <path d="M17 17a1 1 0 1 0 0 .01" strokeLinecap="round" />
      <path d="M6 12l-1 4h14" strokeLinecap="round" strokeLinejoin="round" />
    </IconShell>
  );
}

function ReviewsIcon() {
  return (
    <IconShell>
      <path d="M5 5h14v14H5z" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M8 9h8" strokeLinecap="round" />
      <path d="M8 13h8" strokeLinecap="round" />
      <path d="M8 17h5" strokeLinecap="round" />
    </IconShell>
  );
}

function UsersIcon() {
  return (
    <IconShell>
      <path d="M12 12a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M6.5 19a5.5 5.5 0 0 1 11 0" strokeLinecap="round" />
    </IconShell>
  );
}

function SettingsIcon() {
  return (
    <IconShell>
      <path d="M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Z" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M19 12a7 7 0 0 0-.08-1l2.02-1.57-2-3.46-2.43.8a7.06 7.06 0 0 0-1.73-1L14.5 3h-5l-.28 2.77a7.06 7.06 0 0 0-1.73 1l-2.43-.8-2 3.46L5.08 11A7 7 0 0 0 5 12c0 .34.03.67.08 1l-2.02 1.57 2 3.46 2.43-.8c.53.42 1.11.76 1.73 1L9.5 21h5l.28-2.77c.62-.24 1.2-.58 1.73-1l2.43.8 2-3.46L18.92 13c.05-.33.08-.66.08-1Z" strokeLinecap="round" strokeLinejoin="round" />
    </IconShell>
  );
}

function AuditIcon() {
  return (
    <IconShell>
      <path d="M6 5h12v14H6z" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M9 9h6" strokeLinecap="round" />
      <path d="M9 13h6" strokeLinecap="round" />
      <path d="M9 17h4" strokeLinecap="round" />
    </IconShell>
  );
}

function LogoutIcon() {
  return (
    <IconShell>
      <path d="M10 17l5-5-5-5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M15 12H4" strokeLinecap="round" />
      <path d="M12 4h6v16h-6" strokeLinecap="round" strokeLinejoin="round" />
    </IconShell>
  );
}

const links = [
  { to: "/", label: "Dashboard", icon: <DashboardIcon /> },
  { to: "/reports", label: "Reports", icon: <ReportsIcon /> },
  { to: "/profiles", label: "Profiles", icon: <ProfilesIcon /> },
  { to: "/reviews", label: "Reviews", icon: <ReviewsIcon /> },
  { to: "/users", label: "Users", icon: <UsersIcon /> },
  { to: "/settings", label: "Settings", icon: <SettingsIcon /> },
  { to: "/audit-logs", label: "Audit Logs", icon: <AuditIcon /> },
];

function AppShell() {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarExpanded, setSidebarExpanded] = useState(true);
  const { memberships, logout, user } = useAuth();
  const primaryMembership = memberships[0];
  const isMasterAdmin = primaryMembership?.role === "master_admin";
  const visibleLinks = links.filter((link) => {
    if (isMasterAdmin) return true;
    return link.to === "/" || link.to === "/profiles" || link.to === "/reviews";
  });
  const currentPageLabel = visibleLinks.find((link) => location.pathname === link.to)?.label ?? "Workspace";

  return (
    <div className="min-h-screen bg-sand text-ink">
      {sidebarOpen ? (
        <button
          type="button"
          aria-label="Close sidebar overlay"
          className="fixed inset-0 z-30 bg-ink/20 backdrop-blur-sm md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      ) : null}

      <div className="flex min-h-screen w-full">
        <aside
          className={[
            "fixed inset-y-0 left-0 z-40 flex h-screen flex-col border-r border-ink/10 bg-[linear-gradient(180deg,#f8f3ea_0%,#f2eadc_100%)] px-4 py-6 transition-all duration-300",
            sidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0",
            sidebarExpanded ? "w-[16rem] xl:w-[17rem]" : "w-[5.5rem]",
          ].join(" ")}
        >
          <div className={sidebarExpanded ? "flex items-start justify-between gap-3" : "flex flex-col items-center gap-4"}>
            <div className={sidebarExpanded ? "min-w-0" : "flex flex-col items-center"}>
              {sidebarExpanded ? (
                <>
                  <p className="text-xs uppercase tracking-[0.28em] text-rust/80">
                    Internal Operations
                  </p>
                  <p className="mt-4 text-sm leading-6 text-ink/60">{user?.full_name}</p>
                  <p className="text-xs uppercase tracking-[0.18em] text-ink/35">
                    {primaryMembership?.role?.replaceAll("_", " ")}
                  </p>
                </>
              ) : (
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-pine text-sm font-semibold text-sand shadow-[0_10px_24px_rgba(24,69,59,0.18)]">
                  G
                </div>
              )}
            </div>

            <div className={sidebarExpanded ? "flex gap-2" : "flex flex-col items-center gap-3"}>
              <button
                type="button"
                aria-label={sidebarExpanded ? "Collapse sidebar" : "Expand sidebar"}
                className={[
                  "hidden border border-ink/10 bg-white text-sm text-ink/55 transition hover:border-rust hover:text-rust md:block",
                  sidebarExpanded ? "rounded-2xl px-3 py-2" : "h-10 w-10 rounded-full",
                ].join(" ")}
                onClick={() => setSidebarExpanded((current) => !current)}
              >
                {sidebarExpanded ? "<" : ">"}
              </button>
              <button
                type="button"
                aria-label="Close sidebar"
                className="rounded-2xl border border-ink/10 bg-white px-3 py-2 text-sm text-ink/55 transition hover:border-rust hover:text-rust md:hidden"
                onClick={() => setSidebarOpen(false)}
              >
                Close
              </button>
            </div>
          </div>

          <nav className={sidebarExpanded ? "mt-10 grid gap-3" : "mt-8 grid justify-items-center gap-4"}>
            {visibleLinks.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.to === "/"}
                onClick={() => setSidebarOpen(false)}
                title={!sidebarExpanded ? link.label : undefined}
                className={({ isActive }) =>
                  [
                    "group rounded-2xl text-sm font-medium transition-all duration-200",
                    sidebarExpanded
                      ? "flex items-center gap-4 px-4 py-3"
                      : "flex h-12 w-12 items-center justify-center justify-self-center",
                    isActive
                      ? "bg-pine text-sand shadow-[0_12px_30px_rgba(24,69,59,0.2)]"
                      : "text-ink/50 hover:bg-white/80 hover:text-rust",
                  ].join(" ")
                }
              >
                <span className="shrink-0">{link.icon}</span>
                {sidebarExpanded ? <span>{link.label}</span> : null}
              </NavLink>
            ))}
          </nav>

          <button
            type="button"
            onClick={logout}
            title={!sidebarExpanded ? "Sign Out" : undefined}
            className={[
              "mt-auto rounded-2xl text-sm font-medium text-ink/50 transition-all duration-200 hover:bg-white/80 hover:text-rust",
              sidebarExpanded
                ? "flex w-full items-center gap-4 px-4 py-3"
                : "flex h-12 w-12 items-center justify-center self-center",
            ].join(" ")}
          >
            <span className="shrink-0">
              <LogoutIcon />
            </span>
            {sidebarExpanded ? "Sign Out" : null}
          </button>
        </aside>

        <main
          className={[
            "min-w-0 flex-1 px-6 py-8 transition-all duration-300 md:px-8 xl:px-10",
            sidebarExpanded ? "md:ml-[16rem] xl:ml-[17rem]" : "md:ml-[5.5rem]",
          ].join(" ")}
        >
          <header className="mb-8 border-b border-ink/10 pb-6">
            <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
              <div className="min-w-0">
                <p className="text-sm uppercase tracking-[0.3em] text-rust">
                  Internal Operations
                </p>
                <h1 className="mt-3 font-display text-4xl leading-none md:text-5xl">
                  Google Review Automation
                </h1>
                <h2 className="mt-3 text-lg font-medium text-ink/65">{currentPageLabel}</h2>
              </div>

              <button
                type="button"
                aria-label="Open sidebar"
                className="inline-flex w-fit items-center rounded-2xl border border-ink/10 bg-white px-4 py-3 text-sm font-medium transition hover:border-rust hover:text-rust md:hidden"
                onClick={() => setSidebarOpen(true)}
              >
                Menu
              </button>
            </div>
          </header>

          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/profiles" element={<ProfilesPage />} />
            <Route path="/reviews" element={<ReviewsPage />} />
            <Route path="/users" element={<UsersPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/audit-logs" element={<AuditLogsPage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <AppShell />
            </ProtectedRoute>
          }
        />
      </Routes>
    </AuthProvider>
  );
}
