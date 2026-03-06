export const AUTH_TOKEN_KEY = "kanban-auth-token";
export const AUTH_TOKEN_VALUE = "kanban-demo-authenticated";

export const DEMO_USERNAME = "user";
export const DEMO_PASSWORD = "password";

export const validateCredentials = (username: string, password: string) =>
  username === DEMO_USERNAME && password === DEMO_PASSWORD;
