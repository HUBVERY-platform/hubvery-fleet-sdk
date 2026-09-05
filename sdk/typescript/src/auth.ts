import { HubveryAuthError } from "./exceptions.js";

export const DEFAULT_TOKEN_URL = "https://auth.hubvery.com/oauth/token";

interface TokenResponse {
  access_token: string;
  expires_in?: number;
}

/**
 * OAuth2 client credentials flow. Mirrors the Python SDK's TokenManager:
 * an explicit class with a 30 second expiry buffer, rather than baking
 * refresh logic into the fetch call sites.
 */
export class TokenManager {
  private accessToken: string | null = null;
  private expiresAt = 0;

  constructor(
    private readonly clientId: string,
    private readonly clientSecret: string,
    private readonly scopes: string[],
    private readonly tokenUrl: string = DEFAULT_TOKEN_URL
  ) {}

  private tokenIsValid(): boolean {
    // 30 second buffer before expiry to avoid using a token that expires
    // mid-request.
    return this.accessToken !== null && Date.now() < this.expiresAt - 30_000;
  }

  async getToken(fetchImpl: typeof fetch = fetch): Promise<string> {
    if (this.tokenIsValid()) {
      return this.accessToken as string;
    }

    const response = await fetchImpl(this.tokenUrl, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "client_credentials",
        client_id: this.clientId,
        client_secret: this.clientSecret,
        scope: this.scopes.join(" "),
      }),
    });

    if (response.status !== 200) {
      const text = await response.text();
      throw new HubveryAuthError(`Token request failed: ${response.status} ${text}`);
    }

    const payload = (await response.json()) as Partial<TokenResponse>;
    if (!payload.access_token) {
      throw new HubveryAuthError(
        `Token response missing 'access_token': ${JSON.stringify(payload)}`
      );
    }

    this.accessToken = payload.access_token;
    this.expiresAt = Date.now() + (payload.expires_in ?? 3600) * 1000;
    return this.accessToken;
  }
}
