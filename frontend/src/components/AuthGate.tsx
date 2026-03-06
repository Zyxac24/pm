"use client";

import { useEffect, useState, type FormEvent } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import {
  AUTH_TOKEN_KEY,
  AUTH_TOKEN_VALUE,
  validateCredentials,
} from "@/lib/auth";

type AuthState = "checking" | "unauthenticated" | "authenticated";

const initialFormState = {
  username: "",
  password: "",
};

export const AuthGate = () => {
  const [authState, setAuthState] = useState<AuthState>("checking");
  const [formState, setFormState] = useState(initialFormState);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = window.localStorage.getItem(AUTH_TOKEN_KEY);
    setAuthState(token === AUTH_TOKEN_VALUE ? "authenticated" : "unauthenticated");
  }, []);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!validateCredentials(formState.username, formState.password)) {
      setError("Invalid credentials. Use user/password.");
      return;
    }

    window.localStorage.setItem(AUTH_TOKEN_KEY, AUTH_TOKEN_VALUE);
    setError("");
    setFormState(initialFormState);
    setAuthState("authenticated");
  };

  const handleLogout = () => {
    window.localStorage.removeItem(AUTH_TOKEN_KEY);
    setAuthState("unauthenticated");
  };

  if (authState === "checking") {
    return (
      <main className="mx-auto flex min-h-screen max-w-xl items-center justify-center px-6">
        <p className="text-sm text-[var(--gray-text)]">Loading login...</p>
      </main>
    );
  }

  if (authState === "authenticated") {
    return (
      <>
        <div className="mx-auto flex w-full max-w-[1500px] justify-end px-6 pt-6">
          <button
            type="button"
            onClick={handleLogout}
            className="rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] transition hover:text-[var(--navy-dark)]"
          >
            Log out
          </button>
        </div>
        <KanbanBoard />
      </>
    );
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-xl items-center px-6">
      <section className="w-full rounded-3xl border border-[var(--stroke)] bg-white p-8 shadow-[var(--shadow)]">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[var(--gray-text)]">
          Access
        </p>
        <h1 className="mt-3 font-display text-3xl font-semibold text-[var(--navy-dark)]">
          Sign in to view your Kanban board
        </h1>
        <p className="mt-3 text-sm text-[var(--gray-text)]">
          Use demo credentials: <strong>user</strong> / <strong>password</strong>
        </p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <label className="block text-xs font-semibold uppercase tracking-[0.18em] text-[var(--gray-text)]">
            Username
            <input
              value={formState.username}
              onChange={(event) =>
                setFormState((prev) => ({ ...prev, username: event.target.value }))
              }
              className="mt-2 w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
              autoComplete="username"
              required
            />
          </label>

          <label className="block text-xs font-semibold uppercase tracking-[0.18em] text-[var(--gray-text)]">
            Password
            <input
              value={formState.password}
              onChange={(event) =>
                setFormState((prev) => ({ ...prev, password: event.target.value }))
              }
              type="password"
              className="mt-2 w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
              autoComplete="current-password"
              required
            />
          </label>

          {error ? (
            <p className="text-sm font-medium text-[var(--secondary-purple)]" role="alert">
              {error}
            </p>
          ) : null}

          <button
            type="submit"
            className="rounded-full bg-[var(--secondary-purple)] px-5 py-2 text-xs font-semibold uppercase tracking-wide text-white transition hover:brightness-110"
          >
            Log in
          </button>
        </form>
      </section>
    </main>
  );
};
