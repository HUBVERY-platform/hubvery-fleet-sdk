import type { ProblemDetails } from "./models.js";

/** Raised when the HUBVERY API returns an RFC 7807 problem+json error. */
export class HubveryAPIError extends Error {
  readonly status: number;
  readonly title: string;
  readonly detail?: string;
  readonly code?: string;
  readonly problem: ProblemDetails;

  constructor(problem: ProblemDetails) {
    super(`${problem.status} ${problem.title}: ${problem.detail ?? ""}`.trim());
    this.name = "HubveryAPIError";
    this.problem = problem;
    this.status = problem.status;
    this.title = problem.title;
    this.detail = problem.detail;
    this.code = problem.code;
  }
}

/** Raised when OAuth2 client credentials cannot be exchanged for a token. */
export class HubveryAuthError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "HubveryAuthError";
  }
}
