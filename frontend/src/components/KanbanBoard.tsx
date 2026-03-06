"use client";

import { useEffect, useMemo, useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { DEMO_USERNAME } from "@/lib/auth";
import { AiSidebarChat, type ChatMessage } from "@/components/AiSidebarChat";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { createId, initialData, moveCard, type BoardData } from "@/lib/kanban";
import { sendAiChat } from "@/lib/aiChatApi";
import { fetchBoard, saveBoard } from "@/lib/kanbanApi";

export const KanbanBoard = () => {
  const [board, setBoard] = useState<BoardData | null>(null);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatError, setChatError] = useState<string | null>(null);
  const [isChatSending, setIsChatSending] = useState(false);

  const loadBoard = async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const remoteBoard = await fetchBoard(DEMO_USERNAME);
      setBoard(remoteBoard);
      setSyncError(null);
    } catch {
      setBoard(initialData);
      setLoadError("Could not load board from backend. Showing local snapshot.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadBoard();
  }, []);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  const cardsById = useMemo(() => board?.cards ?? {}, [board?.cards]);

  const persistBoard = async (nextBoard: BoardData) => {
    try {
      const savedBoard = await saveBoard(DEMO_USERNAME, nextBoard);
      setBoard(savedBoard);
      setSyncError(null);
    } catch {
      setSyncError("Could not sync latest changes with backend.");
    }
  };

  const applyBoardUpdate = (updater: (previous: BoardData) => BoardData) => {
    setBoard((previous) => {
      if (!previous) {
        return previous;
      }
      const next = updater(previous);
      void persistBoard(next);
      return next;
    });
  };

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!over || active.id === over.id) {
      return;
    }

    applyBoardUpdate((previous) => ({
      ...previous,
      columns: moveCard(
        previous.columns,
        active.id as string,
        over.id as string
      ),
    }));
  };

  const handleRenameColumn = (columnId: string, title: string) => {
    applyBoardUpdate((previous) => ({
      ...previous,
      columns: previous.columns.map((column) =>
        column.id === columnId ? { ...column, title } : column
      ),
    }));
  };

  const handleAddCard = (columnId: string, title: string, details: string) => {
    const id = createId("card");
    applyBoardUpdate((previous) => ({
      ...previous,
      cards: {
        ...previous.cards,
        [id]: { id, title, details: details || "No details yet." },
      },
      columns: previous.columns.map((column) =>
        column.id === columnId
          ? { ...column, cardIds: [...column.cardIds, id] }
          : column
      ),
    }));
  };

  const handleDeleteCard = (columnId: string, cardId: string) => {
    applyBoardUpdate((previous) => {
      return {
        ...previous,
        cards: Object.fromEntries(
          Object.entries(previous.cards).filter(([id]) => id !== cardId)
        ),
        columns: previous.columns.map((column) =>
          column.id === columnId
            ? {
                ...column,
                cardIds: column.cardIds.filter((id) => id !== cardId),
              }
            : column
        ),
      };
    });
  };

  const handleUpdateCard = (cardId: string, title: string, details: string) => {
    applyBoardUpdate((previous) => ({
      ...previous,
      cards: {
        ...previous.cards,
        [cardId]: {
          ...previous.cards[cardId],
          title,
          details,
        },
      },
    }));
  };

  const handleSendAiMessage = async (question: string) => {
    if (!board) {
      return;
    }

    const history = chatMessages.map(({ role, content }) => ({ role, content }));
    setChatError(null);
    setIsChatSending(true);
    setChatMessages((previous) => [
      ...previous,
      { id: createId("msg"), role: "user", content: question },
    ]);

    try {
      const aiResult = await sendAiChat(DEMO_USERNAME, question, history);
      setBoard(aiResult.board);
      setSyncError(null);
      setChatMessages((previous) => [
        ...previous,
        {
          id: createId("msg"),
          role: "assistant",
          content: aiResult.message,
        },
      ]);
    } catch {
      setChatError("Could not get AI response from backend.");
    } finally {
      setIsChatSending(false);
    }
  };

  if (isLoading || !board) {
    return (
      <main className="mx-auto flex min-h-screen max-w-xl items-center justify-center px-6">
        <p className="text-sm text-[var(--gray-text)]">Loading board...</p>
      </main>
    );
  }

  const activeCard = activeCardId ? cardsById[activeCardId] : null;

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1500px] flex-col gap-10 px-6 pb-16 pt-12">
        <header className="flex flex-col gap-6 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                Single Board Kanban
              </p>
              <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
                Kanban Studio
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--gray-text)]">
                Keep momentum visible. Rename columns, drag cards between stages,
                and capture quick notes without getting buried in settings.
              </p>
            </div>
            <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-4">
              <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                Focus
              </p>
              <p className="mt-2 text-lg font-semibold text-[var(--primary-blue)]">
                One board. Five columns. Zero clutter.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            {board.columns.map((column) => (
              <div
                key={column.id}
                className="flex items-center gap-2 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]"
              >
                <span className="h-2 w-2 rounded-full bg-[var(--accent-yellow)]" />
                {column.title}
              </div>
            ))}
          </div>
          {loadError ? (
            <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--gray-text)]">
              <span>{loadError}</span>
              <button
                type="button"
                onClick={() => void loadBoard()}
                className="rounded-full border border-[var(--stroke)] px-3 py-1 text-xs font-semibold uppercase tracking-wide text-[var(--primary-blue)] transition hover:border-[var(--primary-blue)]"
              >
                Retry
              </button>
            </div>
          ) : null}
          {syncError ? (
            <p className="text-sm font-medium text-[var(--secondary-purple)]">
              {syncError}
            </p>
          ) : null}
        </header>

        <section className="grid gap-6 2xl:grid-cols-[minmax(0,1fr)_360px]">
          <div>
            <DndContext
              sensors={sensors}
              collisionDetection={closestCorners}
              onDragStart={handleDragStart}
              onDragEnd={handleDragEnd}
            >
              <section className="grid gap-6 lg:grid-cols-5">
                {board.columns.map((column) => (
                  <KanbanColumn
                    key={column.id}
                    column={column}
                    cards={column.cardIds.map((cardId) => board.cards[cardId])}
                    onRename={handleRenameColumn}
                    onAddCard={handleAddCard}
                    onDeleteCard={handleDeleteCard}
                    onUpdateCard={handleUpdateCard}
                  />
                ))}
              </section>
              <DragOverlay>
                {activeCard ? (
                  <div className="w-[260px]">
                    <KanbanCardPreview card={activeCard} />
                  </div>
                ) : null}
              </DragOverlay>
            </DndContext>
          </div>
          <AiSidebarChat
            messages={chatMessages}
            isSending={isChatSending}
            error={chatError}
            onSend={handleSendAiMessage}
          />
        </section>
      </main>
    </div>
  );
};
