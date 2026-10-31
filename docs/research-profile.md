# A persistent research investigation

The research profile specializes the same Python agent. The shop remains the
default. Start with a fresh root; mixing shop, research and organization roots is
refused. The only authoritative lifecycle database is `<root>/agent.sqlite`.

```sh
sovereign-agent agent init --profile research --root ./research
sovereign-agent agent ask 'Find a low value of the bounded synthetic objective; compare to x=0 and state uncertainty.' --profile research --root ./research
```

Save the returned investigation identifier. Use it as `INVESTIGATION` below.
`status` without `--id` lists investigations. The question is a core Outcome;
immutable objective revisions, queue associations, operations and observations
reside in that same database. `assistant_work` owns claims, generations and restore
epochs. This profile's role is `investigation`; the older catering `research`
worker is unrelated.

```sh
sovereign-agent agent status --profile research --root ./research --id "$INVESTIGATION"
sovereign-agent agent serve --profile research --root ./research
sovereign-agent agent pause --profile research --root ./research --id "$INVESTIGATION"
sovereign-agent agent redirect 'Prioritize interpreting existing measurements; do not claim global optimality.' --profile research --root ./research --id "$INVESTIGATION"
sovereign-agent agent resume --profile research --root ./research --id "$INVESTIGATION"
sovereign-agent agent report --profile research --root ./research --id "$INVESTIGATION"
```

Without `--live`, `work` and `serve` perform mechanical collection only. A live
reasoning worker requires an explicitly authorized `SOVEREIGN_AGENT_LLM_MODEL`,
the existing OpenAI-compatible `SOVEREIGN_AGENT_LLM_BASE_URL`, and optional key in
`SOVEREIGN_AGENT_LLM_API_KEY`; append `--live --reasoning-effort provider-default`.
This neither provisions an endpoint nor grants provider spending. No model is
prescribed. `work` performs one wake; `serve` keeps durable availability with a
one-second local readiness check and no inference while idle. SIGINT/SIGTERM stop
the supervisor. Restart the same command and root. No organizational scheduler,
ZEO service installation, or web application is needed.

The first adapter can only measure a fixed deterministic synthetic objective at
`x` in `[-2,2]`. The model may choose a sample or replication, wait, interpret,
stop, or escalate, with reasons, a revisable belief and observation identities.
Its assertions remain interpretations. A model stop moves the Outcome to
VERIFYING, never operator acceptance. A changed objective revokes earlier plans;
collection of launched work stays permitted. Pause also revokes live plans;
resume does not restore their authority.

Every investigation reserves at most 12 inference requests, 12,000 output tokens,
24 admitted scientific actions and 12 evaluations cumulatively. Its objectives,
observations and history do not expire. An execution campaign lasts at most 600
seconds and draws only on the remaining cumulative allowance. Each request
reserves up to 2,000 output tokens before transport, including lost replies,
with a 32,768-byte context limit, 120-second request limit and one sequential
request. Counters survive restarts and revisions. They do not measure provider
billing or authorize API spend. Expiry or an invalid reply holds the queue for
operator inspection; there is no automatic model retry. Resume can enqueue a new
reasoning turn within the original budget. Status includes counters, next wake,
pending operations and recent interpretations; report gives the full history.
The shared inference lease survives objective redirection; a lost client holds
the lane for at most 180 seconds before another bounded request is admitted.

When a campaign expires, the investigation waits for an explicit authorized
allowance. `resume` cannot reset use or bypass an expired campaign. For example:

```sh
sovereign-agent agent allow --profile research --root ./research --id "$INVESTIGATION" --key session-2 --campaign-seconds 300 --campaign-calls 3 --evidence 'operator authorization reference'
sovereign-agent agent resume --profile research --root ./research --id "$INVESTIGATION"
```

Use a new session key for a new authorization. Reusing a key never refreshes its
clock or counters. New campaigns cannot raise the cumulative ceilings. The old
schema's initial deadline is preserved as migration history and grants no
execution authority. Status lists campaign counters, the cumulative counters,
and reservation records. The `calls` counter conservatively charges transport
attempts, including attempts later proven not to have performed inference.
Acknowledged token use is consumed; unused reservation is released. Missing
acknowledgement stays UNKNOWN with its entire exposure reserved. Only the
operator can release a proven zero-inference reservation, using
`release-inference no-inference --key RESERVATION --evidence PROOF`. This does
not reset the attempt count or erase the original events.

The approved subscription route is available through normal operation:

```sh
sovereign-agent agent work --profile research --root ./research --live --research-provider claude-subscription
sovereign-agent agent serve --profile research --root ./research --live --research-provider claude-subscription
```

This uses the existing Claude Code CLI with `claude-fable-5-1`, safe/restricted
mode, no provider tools, MCP or skills, one turn, no retries and the runtime's
time/output limits. The operator explicitly selected this existing subscription
route; the rejected literal zero-budget flag is omitted. API-key overrides are
refused. A CLI API-price valuation is recorded separately from billing; it is
not proof of an invoice or an enforceable dollar ceiling. Other operators must
establish their own authorized access contract. No provider installation,
credential copying or account/billing reconfiguration is performed here.
The child inherits only PATH, unchanged native HOME/USER/LOGNAME, LANG/LC_ALL
and TMPDIR, plus fixed turn/output controls. Endpoint, config-directory, proxy
and unrelated secret overrides are excluded. Empty `--setting-sources` disables
user/project/local settings; safe/restricted mode disables custom hooks and
skills. Installed administrative policy still applies. Research roots are 0700;
the database and proposal artifacts are 0600.

Operation intent precedes submission. Executor files under `.sovereign/executor/`
represent external work; the database alone grants authority. Stable operation
identity and an exclusive worker claim prevent duplicate measurements across a
lost acknowledgement. A claimed worker that dies before writing its result is
uncertain and is held rather than evaluated again. These guarantees apply to
this fixture, not arbitrary executors. Request cancellation using:

```sh
sovereign-agent agent cancel --profile research --root ./research --key "$OPERATION"
```

Cancellation is best effort: an already completed measurement is retained. Late
results carry their original objective revision and require fresh interpretation.
Malformed and conflicting results are held with their bytes preserved; they are
not silently repaired or admitted as new evidence. Proposal artifacts stay in
`.sovereign/runs/<work_id>/`; observation receipts and digests live in SQLite.

Status includes reasons and supported recovery actions. `work` without `--live`
collects late receipts and retires expired inference ownership without inference;
unknown usage remains charged. `recover --key OPERATION --evidence REVIEW` can
withdraw a provably undispatched fixture intent (no request/claim/result exists)
and fences its old plan. It can clear a conflict only after the operator restores
the exact originally accepted receipt. Neither operation repeats an experiment.
A dead claimed executor without a receipt remains UNKNOWN: request cancellation,
collect an eventual original receipt, or preserve it for operator diagnosis.
There is no automatic repeat or silent indefinite hold. Receipt reads refuse
FIFOs, devices, directories and symlinks without blocking.

This finite slice has no paper ingestion, arbitrary code execution, general
scientific memory graph, manuscript tools or delegation. Evidence must be treated
as untrusted data, never instructions granting tool access. Executing third-party
research code requires a separately approved isolation adapter; the owned fixture
subprocess is not such a boundary. The deterministic tests demonstrate lifecycle
mechanics, separately from any live-model scientific evaluation.

## Private paper evidence adapter (implementation draft)

This extension consumes an explicitly approved supplied snapshot. It does not
fetch OpenReview, extract PDFs, execute paper code or publish assessments. The
commands below require qualification of this source before operational use; the
new mechanical paths must first pass the synthetic CLI continuity checks.

A supplied `sovereign.paper-source/v1` manifest names one primary paper and up to
four examined prior-work sources. It binds actual source identity/version/URL,
original bytes, approved extracted UTF-8 text, extractor/configuration digests
and hashed byte-range locators. All paths are relative to the research root.
Original files are limited to 16 MiB, each extracted text to 128 KiB, the manifest
to 64 KiB, all locators to 24, and each excerpt to 1,024 bytes. Files must be
owned regular files without symlinks or hardlinks. Copies of admitted extraction
text and provenance become immutable private events in the same `agent.sqlite`.

The input producer must supply actual public/submission-only and anonymity
provenance. Author, venue-decision and review fields are not accepted by this
closed manifest. The parser cannot prove that free text is anonymous or that a
source license permits assessment. Citation-link-only and unknown use refuse.
The operator must approve the actual input/access decision separately, binding
the exact manifest digest. A field, URL, requester identity or digest alone does
not provide that authority. Approval evidence is an operator attestation, not an
automatic rights verification or a public release.

A downloader's original-byte custody manifest is a separate protocol from this
consumer manifest. A receiving/extraction owner must admit the originals, make
the actual bounded extraction and any required identity-free projection, then
issue the consumer manifest. Its attachment digest hashes those exact consumer
manifest bytes, not the downloader's manifest. `original_sha256` binds the
unchanged original paper bytes; `text_sha256` binds the actual derived UTF-8
input. `source_id`, `source_version`, `source_api` and `source_observation`
describe observed identity/version/API and the retained receiving evidence,
without sending raw author, review or decision metadata to the model.
For OpenReview, do not call the raw Note `version` a manuscript revision
counter. Bind the observed snapshot using its actual true modification time
(`tmdate`), selected-Note evidence and original PDF digest. `mdate` is a
venue-set workflow timestamp and does not replace `tmdate`. These distinctions
follow the official [Note fields](https://docs.openreview.net/reference/api-v2/entities/note/fields)
and [API schema](https://docs.openreview.net/reference/api-v2/openapi-definition).

For each document, `locator_map_sha256` hashes its ordered anchor list serialized
as compact JSON with sorted object keys, ASCII escaping and **no trailing
newline**. Each anchor has exactly `id`, `locator`, `start`, `end` and
`quote_sha256`. The half-open `[start, end)` offsets address the admitted UTF-8
text bytes; their exact quote digest does not establish an original PDF byte
offset. The original page/section label and extraction correspondence must be
supplied by the actual extractor. A producer's different request-manifest
serialization must not be substituted. Source-use decisions, receiving
transactions and retention/withdrawal obligations remain with their real
owners; the consumer does not implement a downloader admission backend or
invent an extractor, current-use receipt or library identity.

Choose a private root outside every Git worktree as `PRIVATE_RESEARCH_ROOT`;
the paper adapter refuses Git-contained roots. Do not copy real source snapshots
or private drafts into the public checkout, even if an ignore rule exists.
Use the existing `ask` command to create the investigation, or explicitly
redirect the continuing investigation, and save its ID as `INVESTIGATION`.
Never create a fresh investigation merely to bypass expired or consumed budgets.
Before attachment, authorize a bounded paper campaign explicitly;
the synthetic profile's automatic initial allowance cannot admit paper work.
For two execution sessions within the finite baseline, allocate 300 seconds,
three calls, 6,000 tokens and four actions to each, with zero evaluations:

```sh
sovereign-agent agent allow --profile research --root "$PRIVATE_RESEARCH_ROOT" --id "$INVESTIGATION" --key paper-session-1 --campaign-seconds 300 --campaign-calls 3 --campaign-tokens 6000 --campaign-actions 4 --campaign-evaluations 0 --evidence "$CAMPAIGN_AUTHORIZATION"
sovereign-agent agent attach-paper paper-input/manifest.json --profile research --root "$PRIVATE_RESEARCH_ROOT" --id "$INVESTIGATION" --digest "$APPROVED_MANIFEST_SHA256" --evidence "$INPUT_ACCESS_APPROVAL"
sovereign-agent agent paper-card --profile research --root "$PRIVATE_RESEARCH_ROOT" --id "$INVESTIGATION"
```

These names refer to actual authorized inputs, not values the model supplies.
Attachment changes the objective revision atomically and fences earlier plans.
A changed snapshot requires a new digest and approval and cannot inherit old
observations or a current card. Reattachment and redirection never reset usage.

Use the same documented `work`/`serve`, model provider, pause, redirect, resume
and report routes as the research profile. The model chooses a permitted excerpt
read, interpretation, private assessment, wait, stop or escalation. Every read
returns an observation identity and the exact quoted bytes with original-source
and extraction provenance. Only these inspected observations can support a card.
Paper actions cannot invoke the synthetic objective, fetch a source or run code.
After `wait` or `assess`, automatic inference stops until an operator resumes or
redirects the investigation; the reason remains visible in status.

A card has five separate provisional ordinal dimensions (1–5) or insufficient
evidence. There is no total score. Numeric judgments require evidence; missing
material is not level 1. Originality requires actually inspected primary and
prior-work sources, not unexamined bibliography entries. A valid locator proves
that a reference resolves, not that the evidence entails a scientific claim.
Human scientific review and calibration remain necessary. Reproduction stays
`not attempted`; readiness is a different dimension. The report always labels
cards private/unreviewed, includes their original revision, and marks old cards
stale after redirection or source change. It cannot approve or publish itself.

The entire finite private baseline can allocate at most 600 campaign seconds,
six calls, 12,000 output tokens and eight actions, with no evaluations, across
its sessions. Expired or unused campaign allocations are not silently refreshed.
All existing cumulative accounting and UNKNOWN reservation rules also remain.
If session 1 used the entire allocation, a new session cannot bypass it; report
the exhausted allowance rather than creating another investigation to reset it.
The actual conditional model baseline still requires qualified code and approved
input/access. This draft and its invented tests establish no scientific result.

Private Markdown in the card report expands every numeric dimension into its
exact evidence anchors and stored rubric sentence, with an excerpts-only label.
It shows provisional calibration, automated origin and pending human state.
Null renders as not enough evidence with its reason; reproduction is a neutral
dated not-attempted fact. The adapter never ranks papers or computes a total.
No public index, sitemap, search, feed or social-card eligibility is created.
A later website projection needs actual scientific, editorial/brand, operator
and site-owner release checks; none can be granted by model-supplied fields.

An interrupted paper inference with no committed proposal is held, with its
reservation/usage retained and an explicit report/redirect/resume recovery action.
There is no implicit repeat. A durable proposal recovered before queue completion
is acknowledged without another inference or admitted scientific action.
