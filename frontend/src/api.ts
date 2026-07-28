import type { AnalysisResponse, GenerationJob, MusicBrief, PromptResponse } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function parseJson<T>(response: Response): Promise<T> {
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const message = payload?.message ?? payload?.detail ?? "The API request failed.";
    throw new Error(message);
  }
  return payload as T;
}

export async function analyzeImage(file: File): Promise<AnalysisResponse> {
  const form = new FormData();
  form.append("image", file);
  return parseJson<AnalysisResponse>(
    await fetch(`${API_BASE}/api/analyze-image`, {
      method: "POST",
      body: form
    })
  );
}

export async function composePrompt(brief: MusicBrief): Promise<PromptResponse> {
  return parseJson<PromptResponse>(
    await fetch(`${API_BASE}/api/compose-prompt`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(brief)
    })
  );
}

export async function startGeneration(params: {
  imageHash: string;
  brief: MusicBrief;
  prompt: string;
  analysisId: string;
}): Promise<GenerationJob> {
  return parseJson<GenerationJob>(
    await fetch(`${API_BASE}/api/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        image_hash: params.imageHash,
        brief: params.brief,
        prompt: params.prompt,
        analysis_id: params.analysisId,
        client_request_id: crypto.randomUUID()
      })
    })
  );
}

export async function fetchJob(jobId: string): Promise<GenerationJob> {
  return parseJson<GenerationJob>(await fetch(`${API_BASE}/api/jobs/${jobId}`));
}

export async function fetchProvenance(trackId: string): Promise<Record<string, unknown>> {
  return parseJson<Record<string, unknown>>(
    await fetch(`${API_BASE}/api/tracks/${trackId}/provenance`)
  );
}

export function audioUrl(path: string): string {
  return `${API_BASE}${path}`;
}
