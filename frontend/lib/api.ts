import type { AuditEvent, AuditInput, AuditReport, AuditRequest, AuditResponse, DiscoveryEvent, DiscoveryRequest, DiscoveryResult, ValidationResult, ApiError } from "./types/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message: string =
      body?.message ||
      (Array.isArray(body?.detail)
        ? body.detail.map((d: { msg: string }) => d.msg).join("; ")
        : body?.detail) ||
      res.statusText ||
      "An unexpected error occurred.";
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

export async function validateAuditInput(input: AuditInput): Promise<ValidationResult> {
  const res = await fetch(`${API_URL}/api/v1/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  return handleResponse<ValidationResult>(res);
}

export async function runDiscovery(req: DiscoveryRequest): Promise<DiscoveryResult> {
  const res = await fetch(`${API_URL}/api/v1/discovery`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    signal: AbortSignal.timeout(90_000),
    body: JSON.stringify(req),
  });
  return handleResponse<DiscoveryResult>(res);
}

export async function streamDiscovery(
  req: DiscoveryRequest,
  onProgress: (event: DiscoveryEvent) => void,
): Promise<DiscoveryResult> {
  const res = await fetch(`${API_URL}/api/v1/discovery/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    signal: AbortSignal.timeout(150_000),
    body: JSON.stringify(req),
  });

  if (!res.ok || !res.body) {
    const body = await res.json().catch(() => null);
    const message: string =
      body?.message ||
      (Array.isArray(body?.detail)
        ? body.detail.map((d: { msg: string }) => d.msg).join("; ")
        : body?.detail) ||
      res.statusText ||
      "Discovery failed.";
    throw new Error(message);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result: DiscoveryResult | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";
    for (const chunk of chunks) {
      const line = chunk.replace(/^data: /, "").trim();
      if (!line) continue;
      const event = JSON.parse(line);
      if (event.type === "complete") result = event.result as DiscoveryResult;
      else onProgress(event as DiscoveryEvent);
    }
  }

  if (!result) throw new Error("Stream ended without a result.");
  return result;
}

export async function runAudit(req: AuditRequest): Promise<AuditReport> {
  const res = await fetch(`${API_URL}/api/v1/audit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    signal: AbortSignal.timeout(90_000),
    body: JSON.stringify(req),
  });
  const data = await handleResponse<AuditResponse>(res);
  return data.report;
}

export async function streamAudit(
  req: AuditRequest,
  onProgress: (event: AuditEvent) => void,
): Promise<AuditReport> {
  const res = await fetch(`${API_URL}/api/v1/audit/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    signal: AbortSignal.timeout(300_000),
    body: JSON.stringify(req),
  });

  if (!res.ok || !res.body) {
    const body = await res.json().catch(() => null);
    const message: string =
      body?.message ||
      (Array.isArray(body?.detail)
        ? body.detail.map((d: { msg: string }) => d.msg).join("; ")
        : body?.detail) ||
      res.statusText ||
      "Audit failed.";
    throw new Error(message);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result: AuditReport | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";
    for (const chunk of chunks) {
      const line = chunk.replace(/^data: /, "").trim();
      if (!line) continue;
      const event = JSON.parse(line) as AuditEvent;
      if (event.type === "complete") result = event.result ?? null;
      else onProgress(event);
    }
  }

  if (!result) throw new Error("Stream ended without a result.");
  return result;
}
