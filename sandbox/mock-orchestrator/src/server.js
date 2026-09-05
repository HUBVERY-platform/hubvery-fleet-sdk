// Local sandbox implementing the HUBVERY Fleet API v0.
//
// This is a mock, not a reference implementation of orchestration.
// It accepts capability registrations and tasks, validates them against
// the real JSON Schemas in spec/schemas, and simulates task completion
// with a canned result. It performs no routing, scoring, or planning.
// Its only purpose is to give partners something to develop against
// without a live HUBVERY environment.

import express from "express";
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import { randomUUID } from "node:crypto";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const schemaDir = join(__dirname, "..", "schemas");

function loadSchema(name) {
  return JSON.parse(readFileSync(join(schemaDir, name), "utf8"));
}

const capabilityManifestSchema = loadSchema("capability-manifest.schema.json");
const taskRequestSchema = loadSchema("task-request.schema.json");

const ajv = new Ajv2020({ allErrors: true, strict: false });
addFormats(ajv);
const validateCapabilityManifest = ajv.compile(capabilityManifestSchema);
const validateTaskRequest = ajv.compile(taskRequestSchema);

const capabilities = new Map();
const tasks = new Map();

const PORT = process.env.PORT || 4000;

function problem(res, status, title, detail, type = "about:blank") {
  res.status(status).type("application/problem+json").json({
    type,
    title,
    status,
    detail,
  });
}

function ajvErrorsToDetail(errors) {
  return errors
    .map((e) => `${e.instancePath || "(root)"} ${e.message}`)
    .join("; ");
}

const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: false }));

app.get("/health", (req, res) => {
  res.json({ status: "ok" });
});

// Mock OAuth2 client-credentials token endpoint. Accepts any non-empty
// client_id and client_secret and issues a fixed fake token. This
// sandbox is for exercising the API surface, not for testing real
// authentication or authorization behavior.
app.post("/oauth/token", (req, res) => {
  const { grant_type, client_id, client_secret } = req.body || {};
  if (grant_type !== "client_credentials" || !client_id || !client_secret) {
    return problem(
      res,
      400,
      "Invalid token request",
      "grant_type must be client_credentials, and client_id/client_secret are required."
    );
  }
  res.json({ access_token: "sandbox-fake-token", token_type: "bearer", expires_in: 3600 });
});

app.get("/capabilities", (req, res) => {
  res.json({ items: Array.from(capabilities.values()) });
});

app.post("/capabilities", (req, res) => {
  const manifest = req.body;

  if (!validateCapabilityManifest(manifest)) {
    return problem(
      res,
      400,
      "Invalid capability manifest",
      ajvErrorsToDetail(validateCapabilityManifest.errors),
      "https://schemas.hubvery.com/v0/capability-manifest.schema.json"
    );
  }

  if (capabilities.has(manifest.capability_id)) {
    return problem(
      res,
      409,
      "Capability already exists",
      `A capability with capability_id "${manifest.capability_id}" is already registered.`
    );
  }

  capabilities.set(manifest.capability_id, manifest);
  res.status(201).json(manifest);
});

app.get("/capabilities/:capability_id", (req, res) => {
  const manifest = capabilities.get(req.params.capability_id);
  if (!manifest) {
    return problem(
      res,
      404,
      "Capability not found",
      `No capability found with id "${req.params.capability_id}".`
    );
  }
  res.json(manifest);
});

app.post("/tasks", (req, res) => {
  const taskRequest = req.body;

  if (!validateTaskRequest(taskRequest)) {
    return problem(
      res,
      400,
      "Invalid task request",
      ajvErrorsToDetail(validateTaskRequest.errors),
      "https://schemas.hubvery.com/v0/task-request.schema.json"
    );
  }

  const manifest = capabilities.get(taskRequest.capability_id);
  if (!manifest) {
    return problem(
      res,
      404,
      "Capability not found",
      `No capability found with id "${taskRequest.capability_id}".`
    );
  }

  const validateInput = ajv.compile(manifest.input_schema);
  if (!validateInput(taskRequest.input)) {
    return problem(
      res,
      400,
      "Task input failed capability validation",
      ajvErrorsToDetail(validateInput.errors)
    );
  }

  const now = new Date().toISOString();
  const task = {
    task_id: `task_${randomUUID()}`,
    capability_id: taskRequest.capability_id,
    status: "queued",
    created_at: now,
    updated_at: now,
    input: taskRequest.input,
    result: null,
    error: null,
  };
  tasks.set(task.task_id, task);

  // Simulate asynchronous execution. A real orchestration engine decides
  // which capability actually runs this and how; this sandbox just
  // marks the task complete after a short delay so partners can exercise
  // the full status lifecycle (queued -> running -> completed).
  setTimeout(() => {
    task.status = "running";
    task.updated_at = new Date().toISOString();
  }, 50);

  setTimeout(() => {
    task.status = "completed";
    task.result = { echo: taskRequest.input };
    task.updated_at = new Date().toISOString();
  }, 200);

  res.status(202).json(task);
});

app.get("/tasks/:task_id", (req, res) => {
  const task = tasks.get(req.params.task_id);
  if (!task) {
    return problem(
      res,
      404,
      "Task not found",
      `No task found with id "${req.params.task_id}".`
    );
  }
  res.json(task);
});

// Reset endpoint for test isolation. Not part of the public API surface,
// exists only so integration tests can start each run from a clean state.
app.post("/__test__/reset", (req, res) => {
  capabilities.clear();
  tasks.clear();
  res.status(204).end();
});

const isEntryPoint = import.meta.url === `file://${process.argv[1]}`;
if (isEntryPoint) {
  app.listen(PORT, () => {
    console.log(`hubvery mock-orchestrator listening on http://localhost:${PORT}`);
  });
}

export { app };
