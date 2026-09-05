# Example: minimal agent (TypeScript)

Registers a small "structured" capability (an order-lookup tool, as a
stand-in for something an agent-like partner might expose) and runs one
task through the full lifecycle, using the TypeScript SDK. Complements
the Python echo-capability example, which uses a plain-text modality
instead.

## Running

```bash
cd sandbox/mock-orchestrator && npm install && npm start &
cd sdk/typescript && npm install && npm run build
cd examples/minimal-agent
npm install
npm start
```
