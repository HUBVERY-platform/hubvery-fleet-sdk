// These tests run the SDK against a real instance of the mock
// orchestrator (sandbox/mock-orchestrator), started as an actual HTTP
// server for the duration of the suite. No HTTP calls are mocked here;
// this is deliberately the opposite of the unit-test style used for
// isolated method logic, and exists to catch integration bugs that
// mocked tests structurally cannot: schema mismatches between the SDK
// and the real server, serialization issues, and actual network
// behavior.

import { test, before, after, beforeEach } from "node:test";
import assert from "node:assert/strict";
import { HubveryClient } from "../src/client.js";
import { HubveryAPIError } from "../src/exceptions.js";
import type { CapabilityManifest } from "../src/models.js";

const { app } = await import("../../../sandbox/mock-orchestrator/src/server.js");

let server: import("node:http").Server;
let baseUrl: string;
let client: HubveryClient;

before(async () => {
  server = app.listen(0);
  await new Promise<void>((resolve) => server.once("listening", resolve));
  const address = server.address();
  const port = typeof address === "object" && address ? address.port : 0;
  baseUrl = `http://localhost:${port}`;
  client = new HubveryClient({
    clientId: "id",
    clientSecret: "secret",
    baseUrl,
    tokenUrl: `${baseUrl}/oauth/token`,
  });
});

after(() => {
  server.close();
});

beforeEach(async () => {
  await fetch(`${baseUrl}/__test__/reset`, { method: "POST" });
});

const echoManifest: CapabilityManifest = {
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

test("getHealth against a real running server", async () => {
  const health = await client.getHealth();
  assert.deepEqual(health, { status: "ok" });
});

test("register a capability and read it back", async () => {
  const registered = await client.registerCapability(echoManifest);
  assert.equal(registered.capability_id, "echo-tool");

  const fetched = await client.getCapability("echo-tool");
  assert.equal(fetched.name, "Echo Tool");
});

test("registering a duplicate capability throws HubveryAPIError with status 409", async () => {
  await client.registerCapability(echoManifest);
  await assert.rejects(
    () => client.registerCapability(echoManifest),
    (error: unknown) => {
      assert.ok(error instanceof HubveryAPIError);
      assert.equal(error.status, 409);
      return true;
    }
  );
});

test("full task lifecycle against the real server: submit, poll, completed", async () => {
  await client.registerCapability(echoManifest);

  const submitted = await client.submitTask({
    capability_id: "echo-tool",
    input: { message: "hello" },
  });
  assert.equal(submitted.status, "queued");

  await new Promise((resolve) => setTimeout(resolve, 300));

  const finished = await client.getTask(submitted.task_id);
  assert.equal(finished.status, "completed");
  assert.deepEqual(finished.result, { echo: { message: "hello" } });
});

test("submitting invalid task input surfaces the server's real validation error", async () => {
  await client.registerCapability(echoManifest);

  await assert.rejects(
    () =>
      client.submitTask({
        capability_id: "echo-tool",
        input: { wrong_field: 1 },
      }),
    (error: unknown) => {
      assert.ok(error instanceof HubveryAPIError);
      assert.equal(error.status, 400);
      return true;
    }
  );
});

test("listCapabilities reflects what was actually registered", async () => {
  await client.registerCapability(echoManifest);
  const items = await client.listCapabilities();
  assert.equal(items.length, 1);
  assert.equal(items[0].capability_id, "echo-tool");
});
