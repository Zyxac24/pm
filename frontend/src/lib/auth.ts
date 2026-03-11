import { getErrorMessage } from "@/lib/apiUtils";

export const AUTH_TOKEN_KEY = "kanban-auth-token";
export const AUTH_USERNAME_KEY = "kanban-username";
export const AUTH_USER_ID_KEY = "kanban-user-id";

// Legacy demo credentials (still supported via legacy endpoints)
export const AUTH_TOKEN_VALUE = "kanban-demo-authenticated";
export const DEMO_USERNAME = "user";
export const DEMO_PASSWORD = "password";

export const validateCredentials = (username: string, password: string) =>
  username === DEMO_USERNAME && password === DEMO_PASSWORD;

export type LoginResponse = {
  token: string;
  username: string;
  user_id: number;
};

export type UserProfile = {
  user_id: number;
  username: string;
  created_at: string;
};

export async function registerUser(
  username: string,
  password: string
): Promise<LoginResponse> {
  const response = await fetch("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) throw new Error(await getErrorMessage(response));
  return (await response.json()) as LoginResponse;
}

export async function loginUser(
  username: string,
  password: string
): Promise<LoginResponse> {
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) throw new Error(await getErrorMessage(response));
  return (await response.json()) as LoginResponse;
}

export async function fetchProfile(token: string): Promise<UserProfile> {
  const response = await fetch("/api/auth/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error(await getErrorMessage(response));
  return (await response.json()) as UserProfile;
}

export function saveSession(data: LoginResponse): void {
  window.localStorage.setItem(AUTH_TOKEN_KEY, data.token);
  window.localStorage.setItem(AUTH_USERNAME_KEY, data.username);
  window.localStorage.setItem(AUTH_USER_ID_KEY, String(data.user_id));
}

export function clearSession(): void {
  window.localStorage.removeItem(AUTH_TOKEN_KEY);
  window.localStorage.removeItem(AUTH_USERNAME_KEY);
  window.localStorage.removeItem(AUTH_USER_ID_KEY);
}

export function getToken(): string | null {
  return window.localStorage.getItem(AUTH_TOKEN_KEY);
}

export function getUsername(): string | null {
  return window.localStorage.getItem(AUTH_USERNAME_KEY);
}

export function getUserId(): number | null {
  const id = window.localStorage.getItem(AUTH_USER_ID_KEY);
  return id ? parseInt(id, 10) : null;
}
