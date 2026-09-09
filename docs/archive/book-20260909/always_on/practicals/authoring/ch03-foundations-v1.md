## A loop is a repeated decision with a stopping argument

One tool call cannot answer every request. Lucy's agent may first inspect stock, then ask for
prices, then prepare drafts, and finally explain what it found. An **agent loop** repeatedly
obtains a model turn, executes admitted tool requests, appends their observations and decides
whether another turn is allowed. It is ordinary control flow surrounding a model interface.

A **transcript** is the ordered sequence of messages. A tool request carries a call identifier;
the tool observation repeats it so a later reader can connect the result to the request. A
**state machine** is a description of allowed states and transitions. Our loop starts running
and eventually reaches a terminal reason such as completed, call limit or model failure.
Terminal means this episode stops; it does not mean every requested business action succeeded.

### Work one iteration by hand

The following replay has two tool requests and a final answer. `iter` creates an iterator;
`next` consumes its next item. A real provider could return different turns, but the program's
responsibility to retain observations and enforce limits is unchanged. Predict the role sequence.

```python tags=["foundation", "worked-example"]
intro_turns = [
    {"call_id": "stock-1", "tool": "stock"},
    {"call_id": "price-1", "tool": "price"},
    {"answer": "A draft is ready for review."},
]
intro_transcript = []
intro_tool_values = {"stock": 6, "price": 250}
for intro_turn in intro_turns:
    intro_transcript.append({"role": "assistant", "content": intro_turn})
    if "answer" in intro_turn:
        break
    intro_transcript.append(
        {
            "role": "tool",
            "tool_call_id": intro_turn["call_id"],
            "value": intro_tool_values[intro_turn["tool"]],
        }
    )
print([item["role"] for item in intro_transcript])
assert [item["role"] for item in intro_transcript] == [
    "assistant",
    "tool",
    "assistant",
    "tool",
    "assistant",
]
```

An assistant message requesting a tool is different from the tool observation. Do not replace
the observation with an assistant's claim that a tool succeeded. The real exercise connects
its admission function to the Chapter 2 dispatcher and retains actual handler results.

### Bound the next attempt, not just the previous result

Suppose each model attempt has a configured exposure of two pence and the budget is six.
With four already charged, one more is admitted; with five already charged, it is refused.
Equality at the boundary is allowed. Exposure is an estimate used for admission, not an invoice.
A failed admitted attempt still consumes one call and its configured exposure. Otherwise a
repeatedly failing provider appears free and can evade the bound.

```python tags=["foundation", "worked-example"]
intro_spent = 0
intro_attempts = 0
intro_events = []
while intro_attempts < 3 and intro_spent + 2 <= 6:
    intro_attempts += 1
    intro_spent += 2
    try:
        raise RuntimeError("authored provider failure")
    except RuntimeError:
        intro_events.append((intro_attempts, intro_spent, "failed"))
print(intro_events)
assert intro_events == [(1, 2, "failed"), (2, 4, "failed"), (3, 6, "failed")]
```

Move charging after the raised error in a copy of this example and predict the consequence
before trying it with a fixed three-iteration outer bound. Keep that outer bound so the
experiment cannot become an accidental infinite loop. This is the failure investigated in
Unit B: accounting belongs at admission, before the provider attempt can fail.

### Multiple limits and deterministic precedence

A call-count limit bounds the number of provider attempts. A cost-exposure limit bounds their
configured cumulative estimate. A tool-call limit bounds a different operation and must not
be confused with model turns: one model turn may request multiple tools. If two refusal reasons
apply, the implementation needs a declared precedence so the same input yields an explainable
result. This lesson checks call count before cost exposure.

The dataclass `ModelTurn` packages a content string and a tuple of calls. `ReplayModel.complete`
returns the next authored turn. These are test doubles implementing the same small interface
that the loop expects from a provider. They are not trained models. `Limits` supplies configured
bounds. Your function decides admission; the surrounding loop records counters and invokes it.

Before coding, draw a trace with columns for attempt number, exposure before, next cost,
admission decision, provider outcome and exposure after. Include zero budget, exact fit and
first-attempt failure. Then explain why a terminal status without counters is insufficient
evidence for a bounded loop. The transfer changes costs and call identifiers, so memorizing
the first transcript will not solve it.
