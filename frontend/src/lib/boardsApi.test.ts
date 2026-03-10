import { listBoards, createBoard, getBoard, updateBoardData, deleteBoard } from "@/lib/boardsApi";
import type { BoardData } from "@/lib/kanban";

const jsonResponse = (status: number, payload: unknown) =>
  new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });

const sampleBoard: BoardData = {
  columns: [{ id: "col-1", title: "To Do", cardIds: [] }],
  cards: {},
};

describe("boardsApi", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    vi.stubGlobal("localStorage", {
      getItem: vi.fn((key: string) => {
        if (key === "kanban-auth-token") return "test-jwt-token";
        return null;
      }),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("lists boards", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, {
        boards: [
          { board_id: 1, name: "Board A", description: "", updated_at: "2026-01-01", column_count: 3, card_count: 5 },
        ],
      })
    );

    const boards = await listBoards();
    expect(boards).toHaveLength(1);
    expect(boards[0].name).toBe("Board A");
  });

  it("creates a board", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(201, { board_id: 2, name: "New Board", description: "Desc", board: sampleBoard })
    );

    const result = await createBoard("New Board", "Desc");
    expect(result.board_id).toBe(2);
    expect(result.name).toBe("New Board");
  });

  it("gets a board by id", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, { board_id: 1, name: "Board", description: "", board: sampleBoard })
    );

    const result = await getBoard(1);
    expect(result.board.columns).toHaveLength(1);
  });

  it("updates board data", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, { board_id: 1, name: "Board", description: "", board: sampleBoard })
    );

    const result = await updateBoardData(1, sampleBoard);
    expect(result.board_id).toBe(1);
  });

  it("deletes a board", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(new Response(null, { status: 204 }));

    await expect(deleteBoard(1)).resolves.toBeUndefined();
  });

  it("includes auth header in requests", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, { boards: [] })
    );

    await listBoards();

    const call = vi.mocked(fetch).mock.calls[0];
    const options = call[1] as RequestInit;
    expect((options.headers as Record<string, string>)["Authorization"]).toBe("Bearer test-jwt-token");
  });

  it("throws on 401 unauthorized", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(401, { detail: "Authentication required." })
    );

    await expect(listBoards()).rejects.toThrow("Authentication required.");
  });

  it("throws on 404 not found", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(404, { detail: "Board 999 does not exist." })
    );

    await expect(getBoard(999)).rejects.toThrow("does not exist");
  });
});
