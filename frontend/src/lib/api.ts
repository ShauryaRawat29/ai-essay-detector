import type { AnalysisResult, ApiErrorBody, HealthResponse } from "./types";

// Empty string -> same-origin rewrite proxy (see next.config.ts).
const BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/+$/, "");

export function apiBaseUrl(): string {
  return BASE_URL;
}

export class ApiError extends Error {
  code: string;

  constructor(message: string, code: string) {
    super(message);
    this.name = "ApiError";
    this.code = code;
  }
}

export async function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const res = await fetch(`${BASE_URL}/api/v1/health`, { signal });
  if (!res.ok) {
    throw new Error(`Backend health check failed (${res.status})`);
  }
  return (await res.json()) as HealthResponse;
}

export async function analyzeEssay(
  text: string,
  signal?: AbortSignal,
): Promise<AnalysisResult> {
  const res = await fetch(`${BASE_URL}/api/v1/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
    signal,
  });
  if (!res.ok) {
    const body = await parseError(res);
    throw new ApiError(body.error.message, body.error.code);
  }
  return (await res.json()) as AnalysisResult;
}

export async function parseError(res: Response): Promise<ApiErrorBody> {
  try {
    return (await res.json()) as ApiErrorBody;
  } catch {
    return { error: { code: "INTERNAL_ERROR", message: `Unexpected response (${res.status})` } };
  }
}