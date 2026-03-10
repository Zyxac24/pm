import {
  DEMO_PASSWORD,
  DEMO_USERNAME,
  validateCredentials,
  saveSession,
  clearSession,
  getToken,
  getUsername,
  getUserId,
  AUTH_TOKEN_KEY,
  AUTH_USERNAME_KEY,
  AUTH_USER_ID_KEY,
} from "@/lib/auth";

describe("validateCredentials", () => {
  it("accepts demo credentials", () => {
    expect(validateCredentials(DEMO_USERNAME, DEMO_PASSWORD)).toBe(true);
  });

  it("rejects invalid username", () => {
    expect(validateCredentials("admin", DEMO_PASSWORD)).toBe(false);
  });

  it("rejects invalid password", () => {
    expect(validateCredentials(DEMO_USERNAME, "admin")).toBe(false);
  });
});

describe("session management", () => {
  let store: Record<string, string>;

  beforeEach(() => {
    store = {};
    vi.stubGlobal("localStorage", {
      getItem: vi.fn((key: string) => store[key] ?? null),
      setItem: vi.fn((key: string, value: string) => { store[key] = value; }),
      removeItem: vi.fn((key: string) => { delete store[key]; }),
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("saves and retrieves session data", () => {
    saveSession({ token: "jwt-token-123", username: "alice", user_id: 42 });

    expect(getToken()).toBe("jwt-token-123");
    expect(getUsername()).toBe("alice");
    expect(getUserId()).toBe(42);
  });

  it("clears session data", () => {
    saveSession({ token: "jwt-token-123", username: "alice", user_id: 42 });
    clearSession();

    expect(getToken()).toBeNull();
    expect(getUsername()).toBeNull();
    expect(getUserId()).toBeNull();
  });

  it("returns null for missing user id", () => {
    expect(getUserId()).toBeNull();
  });
});
