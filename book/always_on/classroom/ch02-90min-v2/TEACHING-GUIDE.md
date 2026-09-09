# Chapter 2 — instructor plan for 90 minutes

**Created:** 2026-09-09 · **Status:** DRAFT / classroom review pending.

## New in v2: Pydantic from first principles

No previous Pydantic experience is assumed. Both notebooks and their matching Markdown copies contain the same complete introduction before the first tool model. Teach it once in notebook 1; in notebook 2, use it as a reference or as the starting lesson for learners joining there. Basic Python functions, dictionaries, exceptions and classes remain prerequisites.

The guided sequence moves from annotations that do not enforce types at runtime to `BaseModel`, required fields and defaults, structured `ValidationError` details, coercion versus strict validation, `Field` bounds, forbidden extra keys, and dictionary/JSON/schema representations. Worked examples ask for predictions before displaying actual values. A small data-repair exercise checks understanding before the original four core exercises. The final example shows why structurally valid data still needs an authoritative source and permission checks.

Allow 20 minutes for the primer, including its checkpoint. In the complete class, the opening stock problem takes 2 minutes and the primer occupies minutes 2–22. Its section times are relative to the primer's start. All later clock labels refer to the complete 90-minute lesson. The complete primer appears in notebook 2 for independent study; it is not a second 20-minute block in the class schedule.



The lesson develops a mechanism from a concrete example, inspects intermediate values, asks for predictions, then changes the inputs to test whether the mechanism generalizes. It is designed for students comfortable with basic Python, with guided reading for the class and independent construction/repair in four exercises. No claim of endorsement or pedagogical acceptance is made.

## Prepare before learners arrive

Distribute only the student ZIP or the two files in `student/`. Open both instructor notebooks, restart each kernel, and run the first setup cell on the classroom machine. The notebooks need Pydantic 2 but no repository installation or API key. Keep the answer notebooks in a separate browser tab for the debrief.

Ask learners to run setup before the lesson begins. If one environment fails, pair that learner with a working machine for participation and record which learner actually executes each exercise. A teacher demonstration is not evidence of that learner completing the task. Preserve the Markdown companions as a reading/printing fallback; they do not replace executed work.

Use the student notebooks on the projector while introducing each exercise. Reveal the instructor version only after collecting an attempt and a prediction. The instructor-only cells add changed inputs after the visible examples; avoid presenting them as cryptographically secret tests.

## The exact 90-minute sequence

| Clock | Activity | Instructor prompt | Evidence |
|---|---|---|---|
| 0–2 | Lucy's six-tub problem | “Which proposed quantities need checking?” | First predictions |
| 2–7 | Primer: annotations, models and instances | “Did an annotation stop the string?” | Observed string result and required/default fields |
| 7–12 | Primer: errors and strict validation | “Where is the error, and what was converted?” | Error locations and predicted acceptance table |
| 12–18 | Primer: constraints, JSON and schema | “Which output holds data, which describes it?” | Boundary cases and JSON round trip |
| 18–22 | Primer: factual limits and repair checkpoint | “Can 999 pass the model and still be false?” | Three corrected data defects and explanation |
| 22–28 | Exercise 1: typed arguments | “Transfer the stock contract to a positive order quantity.” | Ten visible checks and corrected class |
| 28–40 | Exercise 2: grounded draft | “Which source owns the price and quantity?” | Five checks, source, unchanged stock |
| 40–46 | Connect the student's function to a tool | “Where does the schema stop and execution begin?” | Schema and actual handler result |
| 46–48 | New-product transfer | “Mango at 325p, then 350p: what changes?” | 1300p and 1400p, under-order refusal |
| 48–50 | Retrieval and notebook switch | “Can a schema-valid request still be wrong?” | Short oral answers |
| 50–54 | Read the actual dispatcher | “Point to model_validate before the handler.” | Annotated execution path |
| 54–57 | Classify refusal layers | “Which check catches this request?” | Five classified observations |
| 57–68 | Exercise 3: repair two dispatcher defects | “Did an error response prevent the handler?” | Event order and five probe outcomes |
| 68–71 | Introduce reserved stock | “What changed in the business contract?” | Nine required, original rule gives six |
| 71–81 | Exercise 4: one rule, two call sites | “Can stock reporting and validation disagree?” | Five arithmetic and two connected checks |
| 81–87 | Compose the actual tool sequence | “Trace 2250p back to authoritative inputs.” | Three observations through student code |
| 87–90 | Exit ticket | Four notebook questions without rerunning cells | Explanation and limits |

Timebox the independent attempts, then debrief using the worked answer. A learner who needs the reveal should retain an incomplete first attempt and rerun the corrected version; do not record that as an independent repair. All four core exercises stay in the lesson. Faster pairs use the extension bank after their core checks and explanations are complete.

## Answer and misconception map

**Pydantic checkpoint.** Repair to `{"sku": "SKU-VANILLA", "on_hand": 2}`: replace the empty SKU, use an integer instead of a string, and remove the undeclared approval key. Keep the strict model unchanged. Ask learners to distinguish an invalid representation from an inaccurate fact: a count of 999 passes the model but disagrees with the authoritative count of two. An empty shelf is allowed by `ge=0`; an order uses `gt=0`. The default `note` is supplied when omitted, while fields without defaults remain required. Catching `ValidationError` reports a failed contract; it does not silently repair the data or authorize a tool.

**Debrief cues.** Ask a learner to trace dictionary → `model_validate` → instance → `model_dump`. Ask another to find the schema's minimum and explain why it is not the current quantity. In the strict-integer table only integer 6 passes; default validation also converts the string, boolean and integral float. Have learners predict a novel input such as `-1` against both an unconstrained strict integer and bounded stock: strict typing alone does not impose non-negativity.

**Exercise 1.** `model_config = ConfigDict(extra="forbid", strict=True)`; SKU has length 1–100; quantity is `int = Field(gt=0, le=1000)`. The valid cases in the visible table are six and 1000. A well-formed unknown SKU can pass this structural schema: catalog membership needs shop data. A model-supplied `approved=True` must not enlarge the operation's contract.

**Exercise 2.** Compute `needed = max(0, reorder_point - on_hand)`, compare quantity against it, look up the SKU price, multiply integer pence, return the exact draft fields. Vanilla gives 1500p; strawberry gives 1100p. Seven is structurally valid but violates need. The canonical code raises for unknown identities and missing prices instead of inventing values. A surplus has need zero; a positive-quantity draft should refuse rather than create an unnecessary order. There is no purchase function in this lesson.

**Tool connection.** The `lambda` wrapper calls the learner's function with the authoritative fixture and price map. It does not contain a reference answer. If the learner function remains incomplete, the connection remains incomplete. `model_json_schema()` describes arguments; calling the registered handler performs the calculation. Ask students to point to both operations.

**Exercise 3.** Restore `tool is None or call.name not in self.allowed`. Move the authority callback before `tool.handler(arguments)`. The forbidden probe records no events. Refusal records only `authority`; an allowed consequential call records `authority`, then `handler`. Missing authority records nothing. An ordinary allowed read records one handler call. Returning an error after the handler executes is not prevention. Returning errors for every case fails the two allowed cases.

**Exercise 4.** Sellable stock is on hand minus reserved. Substitute into target minus sellable stock: `max(0, reorder_point - on_hand + row.get("reserved", 0))`. Vanilla now needs nine at 250p: 2250p. The old six-tub request must fail. The shared function must feed both `list_stock` and draft validation; calculating the right number in a disconnected cell earns no integration credit.

**Capstone.** `list_stock`, `supplier`, `draft_order` run in an explicit deterministic sequence. The observations come from actual handlers using the learner's dispatcher and need function. This demonstrates the tool interface a future model loop will consume. It does not demonstrate that a live model chooses those calls reliably. Physical stock stays at two throughout.

## Additional transfer prompts

Use one changed case after the visible exercise to defeat memorized examples. Ask for a numerical prediction first.

* Pear: on hand 2, target 9, price 175p. Seven units cost 1225p.
* Mango with reservations: on hand 1, target 5, reserved 2, price 325p. Six units cost 1950p.
* On hand 12, target 6, reserved 2 gives zero need. Do not create a negative or zero-quantity draft.
* An empty shop returns an empty stock list; an unknown quote refuses. Duplicate SKU identities refuse at construction.
* A 200-character local result with a 128-byte observation limit refuses the output after the handler ran. A recorded list append remains; no rollback is implied.
* Two dispatchers close over separate copied stock rows. Editing the original input later does not refresh an existing snapshot. This is isolation for an experiment, not a production freshness or concurrency guarantee.

The notebooks' instructor-only checks cover the pear case, empty shop, duplicate identities, a changed reservation case, the connected 2250p result, and the oversized-result effect distinction.

## Assessment and classroom record

Score five dimensions from 0–2: prediction revised using evidence; correct structural contract; grounded calculation with changed input; actual permission/order repair; connected reservation transfer with an honest explanation. Zero means absent or incorrect, one means a specific correction was needed, two means independently supported by execution and explanation. A suggested readiness threshold is 8/10, with full credit for permission/order repair before proceeding to consequential tools. Treat this threshold as a teaching choice, not a validated psychometric claim.

Record anonymous counts: learners present, setup successes, completion of each exercise, highest hint used, independent versus revealed-answer repair, novel transfer success, and recurring misconceptions. Record actual classroom minutes and human preparation/release minutes separately from automated execution time. Leave unobserved values unknown.

The longer repository exercises in `book/always_on/exercises/ch02/` remain follow-on assignments for implementing the complete factory and using saved source handoffs. The standalone ninety-minute pack does not claim to replace their full scope.
