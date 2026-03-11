"use client";

import { useEffect, useState, type FormEvent } from "react";
import {
  listBoards,
  createBoard,
  deleteBoard,
  type BoardSummary,
} from "@/lib/boardsApi";

type BoardSelectorProps = {
  onSelectBoard: (boardId: number) => void;
};

export function BoardSelector({ onSelectBoard }: BoardSelectorProps) {
  const [boards, setBoards] = useState<BoardSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newBoardName, setNewBoardName] = useState("");
  const [newBoardDescription, setNewBoardDescription] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  const loadBoards = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await listBoards();
      setBoards(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load boards.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadBoards();
  }, []);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!newBoardName.trim()) return;
    setIsCreating(true);
    try {
      const created = await createBoard(newBoardName.trim(), newBoardDescription.trim());
      setNewBoardName("");
      setNewBoardDescription("");
      setShowCreateForm(false);
      onSelectBoard(created.board_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create board.");
    } finally {
      setIsCreating(false);
    }
  };

  const handleDelete = async (boardId: number, boardName: string) => {
    if (!window.confirm(`Delete "${boardName}"? This action cannot be undone.`)) return;
    try {
      await deleteBoard(boardId);
      setBoards((prev) => prev.filter((b) => b.board_id !== boardId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete board.");
    }
  };

  if (isLoading) {
    return (
      <main className="mx-auto flex min-h-screen max-w-2xl items-center justify-center px-6">
        <p className="text-sm text-[var(--gray-text)]">Loading boards...</p>
      </main>
    );
  }

  return (
    <main className="relative mx-auto flex min-h-screen max-w-2xl flex-col gap-8 px-6 pb-16 pt-12">
      <header className="rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
          Project Manager
        </p>
        <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
          Your Boards
        </h1>
        <p className="mt-3 text-sm leading-6 text-[var(--gray-text)]">
          Select a board to open, or create a new one to get started.
        </p>
      </header>

      {error ? (
        <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--secondary-purple)]">
          {error}
        </div>
      ) : null}

      <div className="flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
          {boards.length} {boards.length === 1 ? "board" : "boards"}
        </h2>
        <button
          type="button"
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="rounded-full bg-[var(--primary-blue)] px-5 py-2 text-xs font-semibold uppercase tracking-wide text-white transition hover:brightness-110"
        >
          {showCreateForm ? "Cancel" : "New Board"}
        </button>
      </div>

      {showCreateForm ? (
        <form
          onSubmit={handleCreate}
          className="rounded-2xl border border-[var(--stroke)] bg-white p-6 shadow-[var(--shadow)]"
        >
          <label className="block text-xs font-semibold uppercase tracking-[0.18em] text-[var(--gray-text)]">
            Board Name
            <input
              value={newBoardName}
              onChange={(e) => setNewBoardName(e.target.value)}
              className="mt-2 w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
              placeholder="e.g. Sprint Board"
              required
              maxLength={100}
            />
          </label>
          <label className="mt-4 block text-xs font-semibold uppercase tracking-[0.18em] text-[var(--gray-text)]">
            Description
            <input
              value={newBoardDescription}
              onChange={(e) => setNewBoardDescription(e.target.value)}
              className="mt-2 w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
              placeholder="Optional description"
              maxLength={500}
            />
          </label>
          <button
            type="submit"
            disabled={isCreating}
            className="mt-4 rounded-full bg-[var(--secondary-purple)] px-5 py-2 text-xs font-semibold uppercase tracking-wide text-white transition hover:brightness-110 disabled:opacity-50"
          >
            {isCreating ? "Creating..." : "Create Board"}
          </button>
        </form>
      ) : null}

      <div className="grid gap-4">
        {boards.length === 0 ? (
          <div className="rounded-2xl border-2 border-dashed border-[var(--stroke)] p-8 text-center">
            <p className="text-sm text-[var(--gray-text)]">
              No boards yet. Create your first board to get started.
            </p>
          </div>
        ) : (
          boards.map((board) => (
            <div
              key={board.board_id}
              className="group flex items-center justify-between rounded-2xl border border-[var(--stroke)] bg-white p-5 shadow-[var(--shadow)] transition hover:border-[var(--primary-blue)]"
            >
              <button
                type="button"
                onClick={() => onSelectBoard(board.board_id)}
                className="flex-1 text-left"
              >
                <h3 className="font-display text-lg font-semibold text-[var(--navy-dark)]">
                  {board.name}
                </h3>
                {board.description ? (
                  <p className="mt-1 text-sm text-[var(--gray-text)]">
                    {board.description}
                  </p>
                ) : null}
                <div className="mt-2 flex gap-4 text-xs text-[var(--gray-text)]">
                  <span>{board.column_count} columns</span>
                  <span>{board.card_count} cards</span>
                  <span>
                    Updated{" "}
                    {new Date(board.updated_at).toLocaleDateString()}
                  </span>
                </div>
              </button>
              <button
                type="button"
                onClick={() => handleDelete(board.board_id, board.name)}
                className="ml-4 rounded-full border border-[var(--stroke)] px-3 py-1 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] opacity-0 transition hover:border-[var(--secondary-purple)] hover:text-[var(--secondary-purple)] group-hover:opacity-100"
              >
                Delete
              </button>
            </div>
          ))
        )}
      </div>
    </main>
  );
}
