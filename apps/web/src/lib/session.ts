import type { AuthUser, Membership } from "./api";

export type PersistedSession = {
  accessToken: string;
  refreshToken: string;
  user: AuthUser;
  memberships: Membership[];
};

const STORAGE_KEY = "gra_session";
const listeners = new Set<(session: PersistedSession | null) => void>();

let cachedSession: PersistedSession | null | undefined;

function readSessionFromStorage(): PersistedSession | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as PersistedSession;
  } catch {
    window.localStorage.removeItem(STORAGE_KEY);
    return null;
  }
}

function getCachedSession(): PersistedSession | null {
  if (cachedSession === undefined) {
    cachedSession = readSessionFromStorage();
  }
  return cachedSession;
}

function notify(session: PersistedSession | null) {
  for (const listener of listeners) {
    listener(session);
  }
}

export function getStoredSession(): PersistedSession | null {
  return getCachedSession();
}

export function saveStoredSession(session: PersistedSession) {
  cachedSession = session;
  if (typeof window !== "undefined") {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  }
  notify(session);
}

export function updateStoredSessionTokens(accessToken: string, refreshToken: string) {
  const session = getCachedSession();
  if (!session) {
    return;
  }

  saveStoredSession({
    ...session,
    accessToken,
    refreshToken,
  });
}

export function clearStoredSession() {
  cachedSession = null;
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(STORAGE_KEY);
  }
  notify(null);
}

export function subscribeSession(listener: (session: PersistedSession | null) => void) {
  listeners.add(listener);
  listener(getCachedSession());
  return () => {
    listeners.delete(listener);
  };
}

export function getStoredAccessToken() {
  return getCachedSession()?.accessToken ?? null;
}

export function getStoredRefreshToken() {
  return getCachedSession()?.refreshToken ?? null;
}
