import type { BoardData } from "@/lib/kanban";
import { getErrorMessage } from "@/lib/apiUtils";

export async function fetchBoard(username: string): Promise<BoardData> {
  const response = await fetch(`/api/kanban/${encodeURIComponent(username)}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }
  return (await response.json()) as BoardData;
}

export async function saveBoard(
  username: string,
  board: BoardData
): Promise<BoardData> {
  const response = await fetch(`/api/kanban/${encodeURIComponent(username)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(board),
  });
  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }
  return (await response.json()) as BoardData;
}
