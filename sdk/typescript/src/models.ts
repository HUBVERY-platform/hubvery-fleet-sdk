// Types mirroring spec/schemas/*.schema.json. Kept in sync with the
// Python SDK's models.py; both should match the same schema files.

export type Modality =
  | "text"
  | "image"
  | "audio"
  | "video"
  | "structured"
  | "multimodal";

export type TaskStatus =
  | "queued"
  | "running"
  | "requires_input"
  | "completed"
  | "failed"
  | "cancelled";

export interface Constraints {
  max_input_bytes?: number;
  timeout_seconds?: number;
  supports_human_in_the_loop?: boolean;
}

export interface CapabilityManifest {
  capability_id: string;
  name: string;
  description?: string;
  version: string;
  modality: Modality;
  input_schema: Record<string, unknown>;
  output_schema: Record<string, unknown>;
  constraints?: Constraints;
  auth_scopes?: string[];
}

export interface TaskRequest {
  capability_id: string;
  input: Record<string, unknown>;
  callback_url?: string;
  idempotency_key?: string;
}

export interface ProblemDetails {
  type: string;
  title: string;
  status: number;
  detail?: string;
  instance?: string;
  code?: string;
}

export interface Task {
  task_id: string;
  capability_id: string;
  status: TaskStatus;
  created_at: string;
  updated_at: string;
  input?: Record<string, unknown>;
  result?: Record<string, unknown> | null;
  error?: ProblemDetails | null;
}
