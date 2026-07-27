export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8081/api';

export const apiUrl = (path: string) =>
  `${API_BASE_URL.replace(/\/+$/, '')}/${path.replace(/^\/+/, '')}`;

export async function readJson<T>(response: Response): Promise<T | null> {
  try {
    return (await response.json()) as T;
  } catch {
    return null;
  }
}
