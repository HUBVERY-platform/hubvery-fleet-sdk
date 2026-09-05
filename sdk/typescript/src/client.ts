import { TokenManager, DEFAULT_TOKEN_URL } from "./auth.js";
import { HubveryAPIError } from "./exceptions.js";
import type { CapabilityManifest, ProblemDetails, Task, TaskRequest } from "./models.js";

export const DEFAULT_BASE_URL = "https://api.hubvery.com/v0";

export interface HubveryClientOptions {
  clientId: string;
  clientSecret: string;
  baseUrl?: string;
  tokenUrl?: string;
  scopes?: string[];
  fetchImpl?: typeof fetch;
}

async function raiseForProblemJson(response: Response): Promise<void> {
  if (response.status >= 400) {
    let problem: ProblemDetails | undefined;
    try {
      problem = (await response.json()) as ProblemDetails;
      if (typeof problem?.status !== "number" || typeof problem?.title !== "string") {
        problem = undefined;
      }
    } catch {
      problem = undefined;
    }

    if (!problem) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    throw new HubveryAPIError(problem);
  }
}

/**
 * Client for the HUBVERY Fleet API. Fetch-based, works in Node 18+ and
 * modern browsers. Covers the six operations defined in spec/openapi.yaml.
 */
export class HubveryClient {
  private readonly baseUrl: string;
  private readonly tokens: TokenManager;
  private readonly fetchImpl: typeof fetch;

  constructor(options: HubveryClientOptions) {
    this.baseUrl = options.baseUrl ?? DEFAULT_BASE_URL;
    this.fetchImpl = options.fetchImpl ?? fetch;
    this.tokens = new TokenManager(
      options.clientId,
      options.clientSecret,
      options.scopes ?? ["tasks:submit", "tasks:read"],
      options.tokenUrl ?? DEFAULT_TOKEN_URL
    );
  }

  private async authHeaders(): Promise<Record<string, string>> {
    const token = await this.tokens.getToken(this.fetchImpl);
    return { Authorization: `Bearer ${token}` };
  }

  async getHealth(): Promise<{ status: string }> {
    const response = await this.fetchImpl(`${this.baseUrl}/health`);
    await raiseForProblemJson(response);
    return response.json();
  }

  async listCapabilities(): Promise<CapabilityManifest[]> {
    const response = await this.fetchImpl(`${this.baseUrl}/capabilities`, {
      headers: await this.authHeaders(),
    });
    await raiseForProblemJson(response);
    const body = (await response.json()) as { items: CapabilityManifest[] };
    return body.items;
  }

  async registerCapability(manifest: CapabilityManifest): Promise<CapabilityManifest> {
    const response = await this.fetchImpl(`${this.baseUrl}/capabilities`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(await this.authHeaders()) },
      body: JSON.stringify(manifest),
    });
    await raiseForProblemJson(response);
    return response.json();
  }

  async getCapability(capabilityId: string): Promise<CapabilityManifest> {
    const response = await this.fetchImpl(
      `${this.baseUrl}/capabilities/${encodeURIComponent(capabilityId)}`,
      { headers: await this.authHeaders() }
    );
    await raiseForProblemJson(response);
    return response.json();
  }

  async submitTask(taskRequest: TaskRequest): Promise<Task> {
    const response = await this.fetchImpl(`${this.baseUrl}/tasks`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(await this.authHeaders()) },
      body: JSON.stringify(taskRequest),
    });
    await raiseForProblemJson(response);
    return response.json();
  }

  async getTask(taskId: string): Promise<Task> {
    const response = await this.fetchImpl(
      `${this.baseUrl}/tasks/${encodeURIComponent(taskId)}`,
      { headers: await this.authHeaders() }
    );
    await raiseForProblemJson(response);
    return response.json();
  }
}
