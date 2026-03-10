import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/KanbanBoard";
import { initialData, type BoardData } from "@/lib/kanban";

const jsonResponse = (payload: unknown, status = 200) =>
  new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });

const boardDetail = (board: BoardData) => ({
  board_id: 1,
  name: "Test Board",
  description: "",
  board,
});

const getFirstColumn = async () => (await screen.findAllByTestId(/column-/i))[0];
const cloneBoard = (board: BoardData) => JSON.parse(JSON.stringify(board)) as BoardData;

describe("KanbanBoard", () => {
  let aiChatResponse: unknown;
  const mockOnBack = vi.fn();

  beforeEach(() => {
    aiChatResponse = {
      message: "Sure, I can help.",
      patchApplied: false,
      board: cloneBoard(initialData),
    };

    // Mock localStorage for auth token
    vi.stubGlobal("localStorage", {
      getItem: vi.fn((key: string) => {
        if (key === "kanban-auth-token") return "mock-jwt-token";
        return null;
      }),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    });

    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url =
          typeof input === "string"
            ? input
            : input instanceof URL
              ? input.toString()
              : input.url;
        const method = init?.method ?? "GET";
        if (method === "POST" && url.includes("/api/ai/chat/")) {
          return jsonResponse(aiChatResponse);
        }
        if (method === "PUT") {
          const parsedBody =
            typeof init?.body === "string" ? JSON.parse(init.body) : cloneBoard(initialData);
          return jsonResponse(boardDetail(parsedBody));
        }
        // GET /api/boards/{id}
        return jsonResponse(boardDetail(cloneBoard(initialData)));
      })
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    mockOnBack.mockReset();
  });

  it("renders columns from board", async () => {
    render(<KanbanBoard boardId={1} onBack={mockOnBack} />);
    expect(await screen.findAllByTestId(/column-/i)).toHaveLength(5);
  });

  it("shows back button", async () => {
    render(<KanbanBoard boardId={1} onBack={mockOnBack} />);
    await screen.findAllByTestId(/column-/i);
    const backButton = screen.getByRole("button", { name: /all boards/i });
    expect(backButton).toBeInTheDocument();
  });

  it("calls onBack when back button is clicked", async () => {
    render(<KanbanBoard boardId={1} onBack={mockOnBack} />);
    await screen.findAllByTestId(/column-/i);
    await userEvent.click(screen.getByRole("button", { name: /all boards/i }));
    expect(mockOnBack).toHaveBeenCalledOnce();
  });

  it("renames a column", async () => {
    render(<KanbanBoard boardId={1} onBack={mockOnBack} />);
    const column = await getFirstColumn();
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Name");
    expect(input).toHaveValue("New Name");
  });

  it("adds and removes a card", async () => {
    render(<KanbanBoard boardId={1} onBack={mockOnBack} />);
    const column = await getFirstColumn();
    const addButton = within(column).getByRole("button", {
      name: /add a card/i,
    });
    await userEvent.click(addButton);

    const titleInput = within(column).getByPlaceholderText(/card title/i);
    await userEvent.type(titleInput, "New card");
    const detailsInput = within(column).getByPlaceholderText(/details/i);
    await userEvent.type(detailsInput, "Notes");

    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    expect(within(column).getByRole("heading", { name: "New card" })).toBeInTheDocument();

    const deleteButton = within(column).getByRole("button", {
      name: /delete new card/i,
    });
    await userEvent.click(deleteButton);

    expect(within(column).queryByText("New card")).not.toBeInTheDocument();
  });

  it("edits a card title and details", async () => {
    render(<KanbanBoard boardId={1} onBack={mockOnBack} />);
    const column = await getFirstColumn();
    const firstCard = within(column).getByTestId("card-card-1");

    await userEvent.click(within(firstCard).getByRole("button", { name: /edit/i }));

    const titleInput = within(firstCard).getByLabelText("Card title");
    await userEvent.clear(titleInput);
    await userEvent.type(titleInput, "Updated card title");

    const detailsInput = within(firstCard).getByLabelText("Card details");
    await userEvent.clear(detailsInput);
    await userEvent.type(detailsInput, "Updated card details");

    await userEvent.click(within(firstCard).getByRole("button", { name: /save/i }));

    expect(
      within(firstCard).getByRole("heading", { name: "Updated card title" })
    ).toBeInTheDocument();
    expect(within(firstCard).getByText("Updated card details")).toBeInTheDocument();
  });

  it("sends chat message and renders AI response", async () => {
    render(<KanbanBoard boardId={1} onBack={mockOnBack} />);
    await screen.findAllByTestId(/column-/i);

    const input = screen.getByLabelText("AI message input");
    await userEvent.type(input, "Plan my next steps");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    expect(await screen.findByText("Plan my next steps")).toBeInTheDocument();
    expect(await screen.findByText("Sure, I can help.")).toBeInTheDocument();
  });

  it("applies AI patch response and refreshes board view", async () => {
    const patchedBoard = cloneBoard(initialData);
    patchedBoard.cards["card-1"] = {
      ...patchedBoard.cards["card-1"],
      title: "Patched by AI",
      details: "Patched details",
    };
    aiChatResponse = {
      message: "Updated card one.",
      patchApplied: true,
      board: patchedBoard,
    };

    render(<KanbanBoard boardId={1} onBack={mockOnBack} />);
    await screen.findAllByTestId(/column-/i);

    const input = screen.getByLabelText("AI message input");
    await userEvent.type(input, "Update first card");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    expect(await screen.findByRole("heading", { name: "Patched by AI" })).toBeInTheDocument();
    expect(screen.getByText("Patched details")).toBeInTheDocument();
  });

  it("displays board name in header", async () => {
    render(<KanbanBoard boardId={1} onBack={mockOnBack} />);
    expect(await screen.findByText("Test Board")).toBeInTheDocument();
  });
});
