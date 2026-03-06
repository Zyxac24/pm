import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/KanbanBoard";
import { initialData, type BoardData } from "@/lib/kanban";

const jsonResponse = (payload: unknown) =>
  new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });

const getFirstColumn = async () => (await screen.findAllByTestId(/column-/i))[0];
const cloneBoard = (board: BoardData) => JSON.parse(JSON.stringify(board)) as BoardData;

describe("KanbanBoard", () => {
  let aiChatResponse: unknown;

  beforeEach(() => {
    aiChatResponse = {
      message: "Sure, I can help.",
      patchApplied: false,
      board: cloneBoard(initialData),
    };

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
          return jsonResponse(parsedBody);
        }
        return jsonResponse(cloneBoard(initialData));
      })
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders five columns", async () => {
    render(<KanbanBoard />);
    expect(await screen.findAllByTestId(/column-/i)).toHaveLength(5);
  });

  it("renames a column", async () => {
    render(<KanbanBoard />);
    const column = await getFirstColumn();
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Name");
    expect(input).toHaveValue("New Name");
  });

  it("adds and removes a card", async () => {
    render(<KanbanBoard />);
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
    render(<KanbanBoard />);
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
    render(<KanbanBoard />);
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

    render(<KanbanBoard />);
    await screen.findAllByTestId(/column-/i);

    const input = screen.getByLabelText("AI message input");
    await userEvent.type(input, "Update first card");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    expect(await screen.findByRole("heading", { name: "Patched by AI" })).toBeInTheDocument();
    expect(screen.getByText("Patched details")).toBeInTheDocument();
  });
});
