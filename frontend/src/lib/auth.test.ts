import {
  DEMO_PASSWORD,
  DEMO_USERNAME,
  validateCredentials,
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
