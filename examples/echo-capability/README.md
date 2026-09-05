# Example: echo capability (Python)

Registers a trivial capability that echoes its input, submits a task to
it, and polls until completion. Demonstrates the full partner
integration lifecycle described in `docs/architecture.md` using the
Python SDK.

## Running

```bash
cd sandbox/mock-orchestrator && npm install && npm start &
cd examples/echo-capability
pip install -r requirements.txt
python run.py
```
