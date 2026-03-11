import type { BoardData } from "@/lib/kanban";
import { authHeaders, getErrorMessage } from "@/lib/apiUtils";

export type AiHistoryMessage = {
  role: "user" | "assistant";
  content: string;
};

export type AiChatResult = {
  message: string;
  patchApplied: boolean;
  board: BoardData;
};

export async function sendAiChatForBoard(
  boardId: number,
  question: string,
  history: AiHistoryMessage[]
): Promise<AiChatResult> {
  const response = await fetch(`/api/ai/chat/${boardId}`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ question, history }),
  });
  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }
  return (await response.json()) as AiChatResult;
}

// Legacy API (kept for backward compatibility)
export async function sendAiChat(
  username: string,
  question: string,
  history: AiHistoryMessage[]
): Promise<AiChatResult> {
  const response = await fetch(
    `/api/ai/chat/legacy/${encodeURIComponent(username)}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, history }),
    }
  );
  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }
  return (await response.json()) as AiChatResult;
}
