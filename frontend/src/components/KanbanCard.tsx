import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import clsx from "clsx";
import { FormEvent, useEffect, useState } from "react";
import type { Card } from "@/lib/kanban";

type KanbanCardProps = {
  card: Card;
  onDelete: (cardId: string) => void;
  onUpdate: (cardId: string, title: string, details: string) => void;
};

export const KanbanCard = ({ card, onDelete, onUpdate }: KanbanCardProps) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: card.id });
  const [isEditing, setIsEditing] = useState(false);
  const [draftTitle, setDraftTitle] = useState(card.title);
  const [draftDetails, setDraftDetails] = useState(card.details);

  useEffect(() => {
    setDraftTitle(card.title);
    setDraftDetails(card.details);
  }, [card.id, card.title, card.details]);

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const handleCancel = () => {
    setDraftTitle(card.title);
    setDraftDetails(card.details);
    setIsEditing(false);
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const nextTitle = draftTitle.trim();
    if (!nextTitle) {
      return;
    }

    if (nextTitle !== card.title || draftDetails !== card.details) {
      onUpdate(card.id, nextTitle, draftDetails);
    }
    setIsEditing(false);
  };

  const dragBindings = isEditing ? {} : { ...attributes, ...listeners };

  return (
    <article
      ref={setNodeRef}
      style={style}
      className={clsx(
        "rounded-2xl border border-transparent bg-white px-4 py-4 shadow-[0_12px_24px_rgba(3,33,71,0.08)]",
        "transition-all duration-150",
        isDragging && "opacity-60 shadow-[0_18px_32px_rgba(3,33,71,0.16)]"
      )}
      data-testid={`card-${card.id}`}
      {...dragBindings}
    >
      <div className="w-full">
        {isEditing ? (
          <form className="w-full" onSubmit={handleSubmit}>
            <label className="sr-only" htmlFor={`card-title-${card.id}`}>
              Card title
            </label>
            <input
              id={`card-title-${card.id}`}
              value={draftTitle}
              onChange={(event) => setDraftTitle(event.target.value)}
              className="w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm font-semibold text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)]"
              aria-label="Card title"
              required
            />
            <label className="sr-only" htmlFor={`card-details-${card.id}`}>
              Card details
            </label>
            <textarea
              id={`card-details-${card.id}`}
              value={draftDetails}
              onChange={(event) => setDraftDetails(event.target.value)}
              className="mt-2 min-h-[88px] w-full resize-y rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm leading-6 text-[var(--gray-text)] outline-none focus:border-[var(--primary-blue)]"
              aria-label="Card details"
            />
            <div className="mt-3 flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={handleCancel}
                className="rounded-full border border-[var(--stroke)] px-3 py-1 text-xs font-semibold text-[var(--gray-text)] transition hover:border-[var(--navy-dark)] hover:text-[var(--navy-dark)]"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="rounded-full border border-[var(--secondary-purple)] bg-[var(--secondary-purple)] px-3 py-1 text-xs font-semibold text-white transition hover:brightness-110"
              >
                Save
              </button>
            </div>
          </form>
        ) : (
          <div className="w-full">
            <div className="min-w-0">
              <h4 className="font-display text-base font-semibold text-[var(--navy-dark)]">
                {card.title}
              </h4>
              <p className="mt-2 text-sm leading-6 text-[var(--gray-text)]">
                {card.details}
              </p>
            </div>
            <div className="mt-3 flex w-full flex-wrap items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => setIsEditing(true)}
                className="rounded-full border border-transparent px-2 py-1 text-xs font-semibold text-[var(--gray-text)] transition hover:border-[var(--stroke)] hover:text-[var(--navy-dark)]"
                aria-label={`Edit ${card.title}`}
              >
                Edit
              </button>
              <button
                type="button"
                onClick={() => onDelete(card.id)}
                className="rounded-full border border-transparent px-2 py-1 text-xs font-semibold text-[var(--gray-text)] transition hover:border-[var(--stroke)] hover:text-[var(--navy-dark)]"
                aria-label={`Delete ${card.title}`}
              >
                Remove
              </button>
            </div>
          </div>
        )}
      </div>
    </article>
  );
};
