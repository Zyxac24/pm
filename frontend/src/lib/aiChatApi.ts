import type { BoardData } from "@/lib/kanban";
import { getToken } from "@/lib/auth";

export type AiHistoryMessage = {
  role: "user" | "assistant";
  content: string;
};

export type AiChatResult = {
  message: string;
  patchApplied: boolean;
  board: BoardData;
};

const getErrorMessage = async (response: Response) => {
  try {
    const payload = (await response.json()) as { detail?: string };
    if (payload.detail) {
      return payload.detail;
    }
  } catch {
    // Ignore JSON parsing errors and use fallback below.
  }
  return `Request failed with status ${response.status}.`;
};

export const sendAiChatForBoard = async (
  boardId: number,
  question: string,
  history: AiHistoryMessage[]
): Promise<AiChatResult> => {
  const token = getToken();
  const response = await fetch(`/api/ai/chat/${boardId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ question, history }),
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return (await response.json()) as AiChatResult;
};

// Legacy API (kept for backward compatibility)
export const sendAiChat = async (
  username: string,
  question: string,
  history: AiHistoryMessage[]
): Promise<AiChatResult> => {
  const response = await fetch(`/api/ai/chat/legacy/${encodeURIComponent(username)}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question, history }),
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return (await response.json()) as AiChatResult;
};
