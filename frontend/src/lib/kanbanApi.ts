import type { BoardData } from "@/lib/kanban";

const getErrorMessage = async (response: Response) => {
  try {
    const payload = (await response.json()) as { detail?: string };
    if (payload.detail) {
      return payload.detail;
    }
  } catch {
    // Ignore JSON parsing errors and fall back.
  }
  return `Request failed with status ${response.status}.`;
};

export const fetchBoard = async (username: string): Promise<BoardData> => {
  const response = await fetch(`/api/kanban/${encodeURIComponent(username)}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }
  return (await response.json()) as BoardData;
};

export const saveBoard = async (
  username: string,
  board: BoardData
): Promise<BoardData> => {
  const response = await fetch(`/api/kanban/${encodeURIComponent(username)}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(board),
  });
  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }
  return (await response.json()) as BoardData;
};
