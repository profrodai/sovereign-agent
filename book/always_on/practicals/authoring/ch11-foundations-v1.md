## Exposing a tool and permitting a call are separate operations

A registry lists implemented tools. An allowlist names the subset one worker may use. A hostile
instruction might ask a stock-reading worker to purchase goods. The instruction can change what
the model requests; it must not change the worker's deterministic permissions. A **trust boundary**
separates data we interpret from authority we accept. Retrieved text and tool descriptions are
data, even when they contain imperative sentences.

### Start with a handler counter

If a dispatcher returns “not allowed” after executing a handler, the error message is reassuring
but the effect has already happened. Record a local event inside the handler so we can observe
whether it ran. Predict both the result and event list for a registered but forbidden tool.

```python tags=["foundation", "worked-example"]
intro_handler_events = []
intro_registry = {"stock": lambda: intro_handler_events.append("stock-ran") or 6}
intro_allowlist = set()


def intro_dispatch(name):
    if name not in intro_registry or name not in intro_allowlist:
        return {"ok": False, "error": "not_allowed"}
    return {"ok": True, "value": intro_registry[name]()}


assert intro_dispatch("stock")["ok"] is False
assert intro_handler_events == []
intro_allowlist.add("stock")
assert intro_dispatch("stock") == {"ok": True, "value": 6}
assert intro_handler_events == ["stock-ran"]
print(intro_handler_events)
```

This is local Python admission, not a sandbox. A **process** has its own interpreter and memory;
starting a subprocess does not automatically remove filesystem or network privileges. **OS
containment** requires operating-system controls under a stated threat model. The core notebook
proves mediation and effect ordering; the separate container experiment is needed for claims
about operating-system enforcement.

### A protocol describes messages across a boundary

**MCP**, the Model Context Protocol, defines how clients and servers exchange capabilities and
tool requests. This book uses a small pinned protocol implementation rather than assuming an
MCP SDK. **JSON-RPC** supplies request/response envelopes with method names and correlation IDs.
A **transport** carries those bytes; standard input/output is one possible transport. A request
ID correlates a reply to a request. It is not automatically the durable business-operation ID
that protects a supplier purchase from duplication.

```python tags=["foundation", "worked-example"]
import json

intro_rpc_request = {
    "jsonrpc": "2.0",
    "id": 17,
    "method": "tools/call",
    "params": {"name": "list_stock", "arguments": {}},
}
intro_rpc_reply = {"jsonrpc": "2.0", "id": 17, "result": {"count": 3}}
intro_wire = json.dumps(intro_rpc_request)
assert json.loads(intro_wire)["params"]["name"] == "list_stock"
assert intro_rpc_reply["id"] == intro_rpc_request["id"]
print("Correlated request and reply:", intro_rpc_request["id"], intro_rpc_reply["id"])
```

These two objects illustrate correlation, not a complete MCP handshake. A real session also
has initialization and capability rules. The notebook's frozen runtime supplies those mechanics
where the chapter probe uses them. You still inspect the tool name, arguments, permission and
handler observation that matter to the exercise. Reference: the pinned
[MCP 2025-06-18 basic protocol description](https://modelcontextprotocol.io/specification/2025-06-18/basic/index).

### Bounds have different positions in the execution path

Argument validation belongs before the handler. A consequential tool needs an authority guard
before the handler. The serialized result's byte length can be known only after a result exists.
If that final size check refuses output, it does not roll back an earlier side effect. This is
a limitation of that boundary, not a reason to pretend the effect never happened.

Errors returned to a caller should describe the refusal without unnecessarily echoing raw
validation inputs. The actual dispatcher catches declared operational exceptions and returns
bounded observations. An unrelated programming exception must not be counted as proof that
the correct permission check ran.

The construction task implements registry lookup, allowlist membership, strict arguments,
authority guard, handler invocation and bounded JSON output in order. The failure task removes
the allowlist condition. The transfer includes an unseen tool, an allowed read, a denied known
read, a consequential call and an oversized result. Draw the event order for each before coding,
and state which claims still require a supported container or host experiment.
