import { initialData } from "@/lib/kanban";
import { fetchBoard, saveBoard } from "@/lib/kanbanApi";

const jsonResponse = (status: number, payload: unknown) =>
  new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });

describe("kanbanApi", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("loads board for user", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, initialData));

    const board = await fetchBoard("user");

    expect(board.columns).toHaveLength(5);
  });

  it("saves board for user", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, initialData));

    const board = await saveBoard("user", initialData);

    expect(board.cards["card-1"].title).toBe("Align roadmap themes");
  });

  it("throws API detail message for errors", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(404, { detail: "User 'missing' does not exist." })
    );

    await expect(fetchBoard("missing")).rejects.toThrow("does not exist");
  });
});
