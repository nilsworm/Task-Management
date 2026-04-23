const BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000"

export class ApiError extends Error {
  readonly status: number
  constructor(status: number, message: string) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  })

  if (!res.ok) {
    let message = res.statusText
    try {
      const body = await res.json() as { detail?: string }
      if (body.detail) message = String(body.detail)
    } catch {
      // non-JSON error body — keep statusText
    }
    throw new ApiError(res.status, message)
  }

  // 204 No Content has no body
  if (res.status === 204) return undefined as T

  return res.json() as Promise<T>
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path)
}

export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
}

export function apiPatch<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: "PATCH", body: JSON.stringify(body) })
}

export function apiDelete(path: string): Promise<void> {
  return request<void>(path, { method: "DELETE" })
}
