import { describe, it, expect, vi, beforeEach } from "vitest"
import { ApiError, apiGet, apiPost, apiPatch, apiDelete } from "../client"

function mockFetch(status: number, body: unknown): void {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: status >= 200 && status < 300,
      status,
      statusText: status === 200 ? "OK" : "Error",
      json: () => Promise.resolve(body),
    } as Response),
  )
}

beforeEach(() => {
  vi.unstubAllGlobals()
})

describe("apiGet", () => {
  it("returns parsed JSON on 200", async () => {
    mockFetch(200, { id: "1", name: "Test" })
    const result = await apiGet<{ id: string; name: string }>("/tasks")
    expect(result).toEqual({ id: "1", name: "Test" })
  })

  it("throws ApiError with status on 404", async () => {
    mockFetch(404, { detail: "Not found" })
    await expect(apiGet("/tasks/missing")).rejects.toMatchObject({
      name: "ApiError",
      status: 404,
      message: "Not found",
    })
  })

  it("throws ApiError with status on 422", async () => {
    mockFetch(422, { detail: "Validation error" })
    await expect(apiGet("/tasks")).rejects.toBeInstanceOf(ApiError)
  })

  it("uses the detail field from error body as message", async () => {
    mockFetch(409, { detail: "Cannot delete active sprint" })
    const err = await apiGet("/sprints/1").catch((e: unknown) => e)
    expect(err).toBeInstanceOf(ApiError)
    expect((err as ApiError).message).toBe("Cannot delete active sprint")
  })
})

describe("apiPost", () => {
  it("sends POST with JSON body and returns response", async () => {
    mockFetch(201, { id: "abc" })
    const result = await apiPost<{ id: string }>("/tasks", { title: "New Task" })
    expect(result).toEqual({ id: "abc" })

    const fetchMock = vi.mocked(fetch)
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/tasks"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ title: "New Task" }),
      }),
    )
  })

  it("sends POST without body when no body given", async () => {
    mockFetch(200, {})
    await apiPost("/sprints/1/start")
    const fetchMock = vi.mocked(fetch)
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/sprints/1/start"),
      expect.objectContaining({ method: "POST", body: undefined }),
    )
  })
})

describe("apiPatch", () => {
  it("sends PATCH with JSON body", async () => {
    mockFetch(200, { id: "1", title: "Updated" })
    await apiPatch("/tasks/1", { title: "Updated" })
    const fetchMock = vi.mocked(fetch)
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/tasks/1"),
      expect.objectContaining({ method: "PATCH" }),
    )
  })
})

describe("apiDelete", () => {
  it("returns undefined on 204", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 204,
        statusText: "No Content",
        json: () => Promise.resolve(undefined),
      } as Response),
    )
    const result = await apiDelete("/tasks/1")
    expect(result).toBeUndefined()
  })

  it("throws ApiError on 404", async () => {
    mockFetch(404, { detail: "Task not found" })
    await expect(apiDelete("/tasks/missing")).rejects.toBeInstanceOf(ApiError)
  })
})
