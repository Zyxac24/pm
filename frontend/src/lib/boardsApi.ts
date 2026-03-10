import type { BoardData } from "@/lib/kanban";
import { getToken } from "@/lib/auth";

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

const getErrorMessage = async (response: Response) => {
  try {
    const payload = (await response.json()) as { detail?: string };
    if (payload.detail) return payload.detail;
  } catch {
    // ignore
  }
  return `Request failed with status ${response.status}.`;
};

const authHeaders = () => {
  const token = getToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
};

export const listBoards = async (): Promise<BoardSummary[]> => {
  const response = await fetch("/api/boards", {
    headers: authHeaders(),
    cache: "no-store",
  });
  if (!response.ok) throw new Error(await getErrorMessage(response));
  const data = (await response.json()) as { boards: BoardSummary[] };
  return data.boards;
};

export const createBoard = async (
  name: string,
  description: string = ""
): Promise<BoardDetail> => {
  const response = await fetch("/api/boards", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ name, description }),
  });
  if (!response.ok) throw new Error(await getErrorMessage(response));
  return (await response.json()) as BoardDetail;
};

export const getBoard = async (boardId: number): Promise<BoardDetail> => {
  const response = await fetch(`/api/boards/${boardId}`, {
    headers: authHeaders(),
    cache: "no-store",
  });
  if (!response.ok) throw new Error(await getErrorMessage(response));
  return (await response.json()) as BoardDetail;
};

export const updateBoardData = async (
  boardId: number,
  board: BoardData
): Promise<BoardDetail> => {
  const response = await fetch(`/api/boards/${boardId}`, {
    method: "PUT",
    headers: authHeaders(),
    body: JSON.stringify(board),
  });
  if (!response.ok) throw new Error(await getErrorMessage(response));
  return (await response.json()) as BoardDetail;
};

export const updateBoardMeta = async (
  boardId: number,
  name: string,
  description: string
): Promise<BoardSummary> => {
  const response = await fetch(`/api/boards/${boardId}/meta`, {
    method: "PATCH",
    headers: authHeaders(),
    body: JSON.stringify({ name, description }),
  });
  if (!response.ok) throw new Error(await getErrorMessage(response));
  return (await response.json()) as BoardSummary;
};

export const deleteBoard = async (boardId: number): Promise<void> => {
  const response = await fetch(`/api/boards/${boardId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!response.ok) throw new Error(await getErrorMessage(response));
};
