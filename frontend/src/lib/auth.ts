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

const API_BASE = "";

const getErrorMessage = async (response: Response) => {
  try {
    const payload = (await response.json()) as { detail?: string };
    if (payload.detail) return payload.detail;
  } catch {
    // ignore
  }
  return `Request failed with status ${response.status}.`;
};

export const registerUser = async (
  username: string,
  password: string
): Promise<LoginResponse> => {
  const response = await fetch(`${API_BASE}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) throw new Error(await getErrorMessage(response));
  return (await response.json()) as LoginResponse;
};

export const loginUser = async (
  username: string,
  password: string
): Promise<LoginResponse> => {
  const response = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) throw new Error(await getErrorMessage(response));
  return (await response.json()) as LoginResponse;
};

export const fetchProfile = async (token: string): Promise<UserProfile> => {
  const response = await fetch(`${API_BASE}/api/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error(await getErrorMessage(response));
  return (await response.json()) as UserProfile;
};

export const saveSession = (data: LoginResponse) => {
  window.localStorage.setItem(AUTH_TOKEN_KEY, data.token);
  window.localStorage.setItem(AUTH_USERNAME_KEY, data.username);
  window.localStorage.setItem(AUTH_USER_ID_KEY, String(data.user_id));
};

export const clearSession = () => {
  window.localStorage.removeItem(AUTH_TOKEN_KEY);
  window.localStorage.removeItem(AUTH_USERNAME_KEY);
  window.localStorage.removeItem(AUTH_USER_ID_KEY);
};

export const getToken = () => window.localStorage.getItem(AUTH_TOKEN_KEY);
export const getUsername = () => window.localStorage.getItem(AUTH_USERNAME_KEY);
export const getUserId = () => {
  const id = window.localStorage.getItem(AUTH_USER_ID_KEY);
  return id ? parseInt(id, 10) : null;
};
