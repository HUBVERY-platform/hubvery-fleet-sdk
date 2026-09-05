import { test, before, after, beforeEach } from "node:test";
import assert from "node:assert/strict";
import { app } from "./server.js";

let server;
let baseUrl;

before(async () => {
  server = app.listen(0);
  await new Promise((resolve) => server.once("listening", resolve));
  baseUrl = `http://localhost:${server.address().port}`;
});

after(() => {
  server.close();
});

beforeEach(async () => {
  await fetch(`${baseUrl}/__test__/reset`, { method: "POST" });
});

async function json(path, options = {}) {
  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  const body = await response.json().catch(() => null);
  return { status: response.status, body };
}

const validManifest = {
  capability_id: "echo-tool",
  name: "Echo Tool",
  version: "0.1.0",
  modality: "text",
  input_schema: {
    type: "object",
    required: ["message"],
    properties: { message: { type: "string" } },
  },
  output_schema: { type: "object" },
};

test("GET /health returns ok", async () => {
  const { status, body } = await json("/health");
  assert.equal(status, 200);
  assert.deepEqual(body, { status: "ok" });
});

test("registers a valid capability", async () => {
  const { status, body } = await json("/capabilities", {
    method: "POST",
    body: JSON.stringify(validManifest),
  });
  assert.equal(status, 201);
  assert.equal(body.capability_id, "echo-tool");
});

test("rejects an invalid capability manifest with 400", async () => {
  const { status, body } = await json("/capabilities", {
    method: "POST",
    body: JSON.stringify({ name: "Missing required fields" }),
  });
  assert.equal(status, 400);
  assert.match(body.detail, /capability_id/);
});

test("rejects a duplicate capability_id with 409", async () => {
  await json("/capabilities", { method: "POST", body: JSON.stringify(validManifest) });
  const { status } = await json("/capabilities", {
    method: "POST",
    body: JSON.stringify(validManifest),
  });
  assert.equal(status, 409);
});

test("GET /capabilities/:id returns 404 for unknown id", async () => {
  const { status } = await json("/capabilities/does-not-exist");
  assert.equal(status, 404);
});

test("full task lifecycle: submit, poll, complete", async () => {
  await json("/capabilities", { method: "POST", body: JSON.stringify(validManifest) });

  const submitted = await json("/tasks", {
    method: "POST",
    body: JSON.stringify({ capability_id: "echo-tool", input: { message: "hello" } }),
  });
  assert.equal(submitted.status, 202);
  assert.equal(submitted.body.status, "queued");

  const taskId = submitted.body.task_id;

  await new Promise((resolve) => setTimeout(resolve, 300));

  const final = await json(`/tasks/${taskId}`);
  assert.equal(final.status, 200);
  assert.equal(final.body.status, "completed");
  assert.deepEqual(final.body.result, { echo: { message: "hello" } });
});

test("rejects task input that fails the capability's input_schema with 400", async () => {
  await json("/capabilities", { method: "POST", body: JSON.stringify(validManifest) });
  const { status, body } = await json("/tasks", {
    method: "POST",
    body: JSON.stringify({ capability_id: "echo-tool", input: { wrong_field: 1 } }),
  });
  assert.equal(status, 400);
  assert.match(body.detail, /message/);
});

test("rejects a task for an unregistered capability with 404", async () => {
  const { status } = await json("/tasks", {
    method: "POST",
    body: JSON.stringify({ capability_id: "does-not-exist", input: {} }),
  });
  assert.equal(status, 404);
});

test("GET /tasks/:id returns 404 for unknown task", async () => {
  const { status } = await json("/tasks/nonexistent");
  assert.equal(status, 404);
});
