const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    cache: "no-store",
    ...options,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API Error: ${res.status}`);
  }

  return res.json();
}

// ─── Health ───────────────────────────────────────────────────────────

export interface HealthStatus {
  status: string;
  ollama_running: boolean;
  llm_model_ready: boolean;
  embedding_model_ready: boolean;
  vector_store_count: number;
  database_ready: boolean;
}

export async function getHealth(): Promise<HealthStatus> {
  return fetchAPI<HealthStatus>("/health");
}

// ─── Patients ─────────────────────────────────────────────────────────

export interface Patient {
  id: string;
  age?: number;
  gender?: string;
  risk_factors: string[];
  notes?: string;
  created_at: string;
  session_count: number;
}

export interface PatientCreate {
  name?: string;
  age?: number;
  gender?: string;
  risk_factors: string[];
  notes?: string;
}

export async function getPatients(): Promise<Patient[]> {
  return fetchAPI<Patient[]>("/patients");
}

export async function createPatient(data: PatientCreate): Promise<Patient> {
  return fetchAPI<Patient>("/patients", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function deletePatient(id: string): Promise<void> {
  await fetch(`${API_BASE}/patients/${id}`, { method: "DELETE" });
}

// ─── Sessions ─────────────────────────────────────────────────────────

export interface Session {
  id: string;
  patient_id: string;
  symptoms?: string;
  diagnosis?: string;
  therapy_used?: string;
  duration_minutes?: number;
  pain_score_before?: number;
  pain_score_after?: number;
  notes?: string;
  status: string;
  created_at: string;
}

export interface SessionCreate {
  patient_id: string;
  symptoms?: string;
  vitals?: Record<string, string>;
  diagnosis?: string;
  therapy_used?: string;
  machine_settings?: Record<string, string>;
  duration_minutes?: number;
  pain_score_before?: number;
  pain_score_after?: number;
  notes?: string;
}

export async function getSessions(patientId?: string): Promise<Session[]> {
  const query = patientId ? `?patient_id=${patientId}` : "";
  return fetchAPI<Session[]>(`/sessions${query}`);
}

export async function createSession(data: SessionCreate): Promise<Session> {
  return fetchAPI<Session>("/sessions", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ─── Advisor ──────────────────────────────────────────────────────────

export interface IntakeForm {
  patient_id?: string;
  age?: number;
  gender?: string;
  diagnosis: string;
  pain_scale?: number;
  condition_phase?: string;
  body_area?: string;
  symptoms?: string;
  risk_factors: string[];
  additional_notes?: string;
}

export interface SuggestionResponse {
  id: string;
  suggestion: string;
  source_chunks: Record<string, unknown>[];
  is_safe: boolean;
  warning_message?: string;
  blocked_protocols: string[];
  query: string;
}

export async function getSuggestion(
  intake: IntakeForm
): Promise<SuggestionResponse> {
  return fetchAPI<SuggestionResponse>("/advisor/suggest", {
    method: "POST",
    body: JSON.stringify(intake),
  });
}

export interface StreamMetadata {
  source_chunks: Record<string, unknown>[];
  is_safe: boolean;
  blocked_protocols: string[];
  warning_message?: string;
  query: string;
}

export function streamSuggestion(
  intake: IntakeForm,
  onToken: (token: string) => void,
  onDone: () => void,
  onError: (error: string) => void,
  onMetadata?: (meta: StreamMetadata) => void
): AbortController {
  const controller = new AbortController();

  fetch(`${API_BASE}/advisor/suggest/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(intake),
    signal: controller.signal,
  })
    .then(async (response) => {
      const reader = response.body?.getReader();
      if (!reader) return;

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.__metadata__ && data.payload && onMetadata) {
                // Final metadata event — parse the nested JSON payload
                const meta: StreamMetadata = JSON.parse(data.payload);
                onMetadata(meta);
              } else if (data.token) {
                onToken(data.token);
              } else if (data.done) {
                onDone();
              } else if (data.error) {
                onError(data.error);
              }
            } catch {
              // skip malformed JSON
            }
          }
        }
      }
      onDone();
    })
    .catch((err) => {
      if (err.name !== "AbortError") onError(err.message);
    });

  return controller;
}


// ─── Safety ───────────────────────────────────────────────────────────

export interface SafetyCheckResponse {
  is_safe: boolean;
  blocked_protocols: string[];
  conflicts: Record<string, unknown>[];
  warning_message?: string;
}

export async function checkSafety(
  riskFactors: string[],
  suggestedProtocol?: string
): Promise<SafetyCheckResponse> {
  return fetchAPI<SafetyCheckResponse>("/advisor/check-safety", {
    method: "POST",
    body: JSON.stringify({
      risk_factors: riskFactors,
      suggested_protocol: suggestedProtocol,
    }),
  });
}

// ─── RAG ──────────────────────────────────────────────────────────────

export interface SearchResult {
  content: string;
  score: number;
  source_file: string;
  page_number?: number;
  document_type?: string;
}

export async function searchKnowledgeBase(
  query: string,
  topK = 10
): Promise<SearchResult[]> {
  return fetchAPI<SearchResult[]>("/rag/search", {
    method: "POST",
    body: JSON.stringify({ query, top_k: topK }),
  });
}

export interface UploadStatus {
  id: number;
  filename: string;
  total_chunks: number;
  ingested_chunks: number;
  extract_images: number;
  safe_mode: number;
  status: "pending" | "parsing" | "processing" | "complete" | "failed" | "cancelled";
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export async function uploadDocument(file: File, documentType: string = "clinical_guide", extractImages: boolean = true): Promise<{ status: string, ingestion_id: number, message: string }> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("document_type", documentType);
  formData.append("extract_images", extractImages.toString());

  const res = await fetch(`${API_BASE}/rag/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API Error: ${res.status}`);
  }

  return res.json();
}

export async function getUploads(): Promise<UploadStatus[]> {
  return fetchAPI<UploadStatus[]>("/rag/uploads");
}

export async function deleteUpload(id: number, purgeVectors: boolean = false): Promise<{status: string}> {
  return fetchAPI<{status: string}>(`/rag/uploads/${id}?purge_vectors=${purgeVectors}`, { method: "DELETE" });
}

export async function retryUpload(
  id: number, 
  extractImages?: boolean, 
  safeMode?: boolean
): Promise<{status: string, ingestion_id: number}> {
  const query = new URLSearchParams();
  if (extractImages !== undefined) query.append("extract_images", extractImages.toString());
  if (safeMode !== undefined) query.append("safe_mode", safeMode.toString());
  const queryString = query.toString() ? `?${query.toString()}` : "";
  
  return fetchAPI<{status: string, ingestion_id: number}>(`/rag/uploads/${id}/retry${queryString}`, { method: "POST" });
}

export interface SystemConfig {
  llm_model: string;
  vision_model: string;
  embedding_model: string;
}

export async function getConfig(): Promise<SystemConfig> {
  return fetchAPI<SystemConfig>("/config");
}

export async function updateConfig(data: {llm_model: string, vision_model: string}): Promise<{status: string}> {
  return fetchAPI<{status: string}>("/config", {
    method: "POST",
    body: JSON.stringify(data)
  });
}

export async function getRagStatus(): Promise<{
  total_chunks: number;
  is_ingested: boolean;
}> {
  return fetchAPI("/rag/status");
}
