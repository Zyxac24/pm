"use client";

import { useEffect, useState, type FormEvent } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import { BoardSelector } from "@/components/BoardSelector";
import {
  AUTH_TOKEN_KEY,
  clearSession,
  getToken,
  getUsername,
  loginUser,
  registerUser,
  saveSession,
} from "@/lib/auth";

type AuthState = "checking" | "unauthenticated" | "authenticated";
type AuthMode = "login" | "register";

const initialFormState = {
  username: "",
  password: "",
};

export const AuthGate = () => {
  const [authState, setAuthState] = useState<AuthState>("checking");
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [formState, setFormState] = useState(initialFormState);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [username, setUsername] = useState<string | null>(null);
  const [selectedBoardId, setSelectedBoardId] = useState<number | null>(null);

  useEffect(() => {
    const token = getToken();
    if (token) {
      setUsername(getUsername());
      setAuthState("authenticated");
    } else {
      setAuthState("unauthenticated");
    }
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const response =
        authMode === "login"
          ? await loginUser(formState.username, formState.password)
          : await registerUser(formState.username, formState.password);

      saveSession(response);
      setUsername(response.username);
      setFormState(initialFormState);
      setAuthState("authenticated");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogout = () => {
    clearSession();
    setSelectedBoardId(null);
    setAuthState("unauthenticated");
  };

  if (authState === "checking") {
    return (
      <main className="mx-auto flex min-h-screen max-w-xl items-center justify-center px-6">
        <p className="text-sm text-[var(--gray-text)]">Loading...</p>
      </main>
    );
  }

  if (authState === "authenticated") {
    return (
      <>
        <div className="mx-auto flex w-full max-w-[1500px] items-center justify-between px-6 pt-6">
          <p className="text-sm text-[var(--gray-text)]">
            Signed in as <strong className="text-[var(--navy-dark)]">{username}</strong>
          </p>
          <button
            type="button"
            onClick={handleLogout}
            className="rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] transition hover:text-[var(--navy-dark)]"
          >
            Log out
          </button>
        </div>
        {selectedBoardId ? (
          <KanbanBoard
            boardId={selectedBoardId}
            onBack={() => setSelectedBoardId(null)}
          />
        ) : (
          <BoardSelector onSelectBoard={setSelectedBoardId} />
        )}
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
          {authMode === "login" ? "Sign in" : "Create account"}
        </h1>
        <p className="mt-3 text-sm text-[var(--gray-text)]">
          {authMode === "login" ? (
            <>
              Demo credentials: <strong>user</strong> / <strong>password</strong>
            </>
          ) : (
            "Choose a username and password to get started."
          )}
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
              autoComplete={authMode === "login" ? "current-password" : "new-password"}
              required
              minLength={4}
            />
          </label>

          {error ? (
            <p className="text-sm font-medium text-[var(--secondary-purple)]" role="alert">
              {error}
            </p>
          ) : null}

          <div className="flex items-center gap-4">
            <button
              type="submit"
              disabled={isSubmitting}
              className="rounded-full bg-[var(--secondary-purple)] px-5 py-2 text-xs font-semibold uppercase tracking-wide text-white transition hover:brightness-110 disabled:opacity-50"
            >
              {isSubmitting
                ? "Please wait..."
                : authMode === "login"
                  ? "Log in"
                  : "Register"}
            </button>
            <button
              type="button"
              onClick={() => {
                setAuthMode(authMode === "login" ? "register" : "login");
                setError("");
              }}
              className="text-xs font-semibold text-[var(--primary-blue)] hover:underline"
            >
              {authMode === "login"
                ? "Create an account"
                : "Already have an account? Log in"}
            </button>
          </div>
        </form>
      </section>
    </main>
  );
};
