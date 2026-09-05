// Minimal example of a partner integration using the TypeScript SDK.
//
// Registers a small "structured" capability (an order-lookup tool, as a
// stand-in for something an agent-like partner might expose) and runs
// one task through the full lifecycle, using the TypeScript SDK.
// Complements the Python echo-capability example, which uses a
// plain-text modality instead.
//
// Run against the local sandbox:
//
//   cd sandbox/mock-orchestrator && npm install && npm start &
//   cd sdk/typescript && npm install && npm run build
//   cd examples/minimal-agent
//   npm install
//   npm start

import { HubveryClient } from "@hubvery/fleet-sdk";
import type { CapabilityManifest } from "@hubvery/fleet-sdk";

const BASE_URL = process.env.HUBVERY_BASE_URL ?? "http://localhost:4000";
const TOKEN_URL = process.env.HUBVERY_TOKEN_URL ?? `${BASE_URL}/oauth/token`;

const manifest: CapabilityManifest = {
  capability_id: "order-lookup",
  name: "Order Lookup",
  description:
    "Looks up an order by id and returns its status. Exists to demonstrate a structured-data capability, not to do real work.",
  version: "0.1.0",
  modality: "structured",
  input_schema: {
    type: "object",
    required: ["order_id"],
    properties: { order_id: { type: "string" } },
  },
  output_schema: { type: "object" },
};

async function main(): Promise<number> {
  const client = new HubveryClient({
    clientId: process.env.HUBVERY_CLIENT_ID ?? "example-client",
    clientSecret: process.env.HUBVERY_CLIENT_SECRET ?? "example-secret",
    baseUrl: BASE_URL,
    tokenUrl: TOKEN_URL,
  });

  console.log(`Registering capability against ${BASE_URL} ...`);
  try {
    const registered = await client.registerCapability(manifest);
    console.log(`Registered: ${registered.capability_id} v${registered.version}`);
  } catch (error) {
    console.log(`Registration skipped or failed (${error}); continuing.`);
  }

  console.log("Submitting a task ...");
  let task = await client.submitTask({
    capability_id: "order-lookup",
    input: { order_id: "ord_12345" },
  });
  console.log(`Task ${task.task_id} submitted, status: ${task.status}`);

  const deadline = Date.now() + 5000;
  const terminal = new Set(["completed", "failed", "cancelled"]);
  while (!terminal.has(task.status)) {
    if (Date.now() > deadline) {
      console.error("Task did not reach a terminal state in time.");
      return 1;
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
    task = await client.getTask(task.task_id);
  }

  console.log(`Final status: ${task.status}`);
  console.log("Result:", task.result);
  return 0;
}

main().then((code) => process.exit(code));
