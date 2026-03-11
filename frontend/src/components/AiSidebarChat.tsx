"use client";

import { useState, type FormEvent } from "react";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

type AiSidebarChatProps = {
  messages: ChatMessage[];
  isSending: boolean;
  error: string | null;
  onSend: (question: string) => Promise<void>;
};

export function AiSidebarChat({
  messages,
  isSending,
  error,
  onSend,
}: AiSidebarChatProps) {
  const [question, setQuestion] = useState("");

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || isSending) {
      return;
    }

    setQuestion("");
    await onSend(trimmed);
  };

  return (
    <aside className="h-full rounded-3xl border border-[var(--stroke)] bg-white p-5 shadow-[var(--shadow)]">
      <div className="border-b border-[var(--stroke)] pb-4">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--gray-text)]">
          AI Chat
        </p>
        <h2 className="mt-2 font-display text-xl font-semibold text-[var(--navy-dark)]">
          Sidebar Assistant
        </h2>
        <p className="mt-2 text-sm text-[var(--gray-text)]">
          Ask AI to create, edit, or move cards on your board.
        </p>
      </div>

      <div
        className="mt-4 max-h-[470px] space-y-3 overflow-y-auto pr-1"
        data-testid="ai-chat-messages"
      >
        {messages.length === 0 ? (
          <p className="rounded-2xl border border-dashed border-[var(--stroke)] px-3 py-4 text-sm text-[var(--gray-text)]">
            No messages yet. Start with a task for AI.
          </p>
        ) : null}
        {messages.map((message) => (
          <article
            key={message.id}
            className={
              message.role === "user"
                ? "ml-6 rounded-2xl bg-[var(--primary-blue)]/10 px-3 py-2 text-sm text-[var(--navy-dark)]"
                : "mr-6 rounded-2xl bg-[var(--surface)] px-3 py-2 text-sm text-[var(--navy-dark)]"
            }
          >
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--gray-text)]">
              {message.role === "user" ? "You" : "AI"}
            </p>
            <p className="mt-1 whitespace-pre-wrap">{message.content}</p>
          </article>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="mt-4 space-y-3">
        <label className="block text-xs font-semibold uppercase tracking-[0.16em] text-[var(--gray-text)]">
          Message
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            className="mt-2 min-h-[90px] w-full resize-y rounded-2xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
            placeholder="Ask AI to update your board..."
            aria-label="AI message input"
            disabled={isSending}
            required
          />
        </label>
        {error ? <p className="text-sm text-[var(--secondary-purple)]">{error}</p> : null}
        <button
          type="submit"
          className="rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isSending}
        >
          {isSending ? "Sending..." : "Send"}
        </button>
      </form>
    </aside>
  );
}
