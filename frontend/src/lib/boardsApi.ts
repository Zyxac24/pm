import type { BoardData } from "@/lib/kanban";
import { authHeaders, getErrorMessage } from "@/lib/apiUtils";

export type BoardSummary = {
  board_id: number;
  name: string;
  description: string;
  updated_at: string;
  column_count: number;
  card_count: number;
};

export type BoardDetail = {
  board_id: number;
  name: string;
  description: string;
  board: BoardData;
};

export async function listBoards(): Promise<BoardSummary[]> {
  const response = await fetch("/api/boards", {
    headers: authHeaders(),
    cache: "no-store",
  });
  if (!response.ok) throw new Error(await getErrorMessage(response));
  const data = (await response.json()) as { boards: BoardSummary[] };
  return data.boards;
}

export async function createBoard(
  name: string,
  description: string = ""
): Promise<BoardDetail> {
  const response = await fetch("/api/boards", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ name, description }),
  });
  if (!response.ok) throw new Error(await getErrorMessage(response));
  return (await response.json()) as BoardDetail;
}

export async function getBoard(boardId: number): Promise<BoardDetail> {
  const response = await fetch(`/api/boards/${boardId}`, {
    headers: authHeaders(),
    cache: "no-store",
  });
  if (!response.ok) throw new Error(await getErrorMessage(response));
  return (await response.json()) as BoardDetail;
}

export async function updateBoardData(
  boardId: number,
  board: BoardData
): Promise<BoardDetail> {
  const response = await fetch(`/api/boards/${boardId}`, {
    method: "PUT",
    headers: authHeaders(),
    body: JSON.stringify(board),
  });
  if (!response.ok) throw new Error(await getErrorMessage(response));
  return (await response.json()) as BoardDetail;
}

export async function updateBoardMeta(
  boardId: number,
  name: string,
  description: string
): Promise<BoardSummary> {
  const response = await fetch(`/api/boards/${boardId}/meta`, {
    method: "PATCH",
    headers: authHeaders(),
    body: JSON.stringify({ name, description }),
  });
  if (!response.ok) throw new Error(await getErrorMessage(response));
  return (await response.json()) as BoardSummary;
}

export async function deleteBoard(boardId: number): Promise<void> {
  const response = await fetch(`/api/boards/${boardId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!response.ok) throw new Error(await getErrorMessage(response));
}
