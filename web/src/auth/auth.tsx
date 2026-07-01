import { createContext, use, useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { devLogin, fetchMe, revokeSession } from "@/api/auth";
import type { ActorContext } from "@/api/types";
import { tokenStore } from "@/auth/tokenStore";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthContextValue {
  status: AuthStatus;
  actor: ActorContext | null;
  login: (email: string) => Promise<void>;
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

  const login = useCallback(async (email: string) => {
    const tokens = await devLogin(email);
    tokenStore.setSession(tokens);
    const me = await fetchMe();
    setActor(me);
    setStatus("authenticated");
  }, []);

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
    () => ({ status, actor, login, logout }),
    [status, actor, login, logout],
  );

  return <AuthContext value={value}>{children}</AuthContext>;
}

export function useAuth(): AuthContextValue {
  const value = use(AuthContext);
  if (value === null) throw new Error("useAuth must be used within AuthProvider");
  return value;
}
