import { createContext, use, useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { devLogin, fetchMe, revokeSession } from "@/api/auth";
import type { ActorContext, TokenResponse } from "@/api/types";
import { tokenStore } from "@/auth/tokenStore";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthContextValue {
  status: AuthStatus;
  actor: ActorContext | null;
  login: (email: string) => Promise<void>;
  /** Finalize a session from tokens obtained outside dev-login (e.g. OIDC). */
  establishSession: (tokens: TokenResponse) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [actor, setActor] = useState<ActorContext | null>(null);

  useEffect(() => {
    let active = true;
    if (!tokenStore.hasSession()) {
      setStatus("unauthenticated");
      return;
    }
    fetchMe()
      .then((me) => {
        if (!active) return;
        setActor(me);
        setStatus("authenticated");
      })
      .catch(() => {
        if (!active) return;
        tokenStore.clear();
        setActor(null);
        setStatus("unauthenticated");
      });
    return () => {
      active = false;
    };
  }, []);

  const establishSession = useCallback(async (tokens: TokenResponse) => {
    tokenStore.setSession(tokens);
    const me = await fetchMe();
    setActor(me);
    setStatus("authenticated");
  }, []);

  const login = useCallback(
    async (email: string) => {
      await establishSession(await devLogin(email));
    },
    [establishSession],
  );

  const logout = useCallback(async () => {
    try {
      await revokeSession();
    } catch {
      /* best effort */
    }
    tokenStore.clear();
    setActor(null);
    setStatus("unauthenticated");
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ status, actor, login, establishSession, logout }),
    [status, actor, login, establishSession, logout],
  );

  return <AuthContext value={value}>{children}</AuthContext>;
}

export function useAuth(): AuthContextValue {
  const value = use(AuthContext);
  if (value === null) throw new Error("useAuth must be used within AuthProvider");
  return value;
}
