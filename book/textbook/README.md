# The Teaching Book

**Edition:** nineteen-chapter construction · **Updated:** 2026-09-09

Build Your Always-On AI Agent From Scratch follows one Python agent from its first model call to an unattended day in Lucy's ice cream shop. Read the chapters in order. Each introduces a problem, constructs a mechanism, reproduces a failure and explains the repair.

Start with the [preface](PREFACE.md) and [setup and reader conventions](CONVENTIONS.md), then [Chapter 1](ch01/README.md). This directory contains the manuscript and its accompanying code. The [Exercise Book](../exercises/README.md) holds learner assignments, the [Solutions Book](../solutions/README.md) holds worked answers, and the [Educator Guide](../educator/README.md) holds classroom material. Chapter numbers and topics match across all four assets.

## What is available

There is one nineteen-chapter sequence. Sixteen chapters contain substantial **DRAFT** manuscripts and executable reference checkpoints. Chapters **4, 7 and 13** contain **PLANNED construction briefs**: their goals, interfaces, two ninety-minute practical plans and acceptance cases are documented, but their complete lessons, notebooks and new learner implementation are not yet delivered. A planned chapter is not an executable lesson. The [construction roadmap](EXPANSION.md) records the remaining work and the integration commitments.

You can read the drafted chapters and run their supplied reference checkpoints now. Building the entire nineteen-chapter system solely from your own preceding chapter code remains a release requirement. The [code ownership guide](OWNERSHIP.md) names the supplied components so a working demonstration cannot be mistaken for a completed from-scratch construction.

## Contents

| Chapter | Read | Status |
| --- | --- | --- |
| 1 | [Make the first model call for Lucy](ch01/README.md) | DRAFT |
| 2 | [Give the agent reliable shop tools](ch02/README.md) | DRAFT |
| 3 | [Build the model and tool loop](ch03/README.md) | DRAFT |
| 4 | [Build durable state with SQLite](ch04/README.md) | PLANNED |
| 5 | [Remember across conversations](ch05/README.md) | DRAFT |
| 6 | [Reuse a tested opening procedure](ch06/README.md) | DRAFT |
| 7 | [Build a durable work inbox and report outbox](ch07/README.md) | PLANNED |
| 8 | [Talk to the agent from your phone](ch08/README.md) | DRAFT |
| 9 | [Wake up for schedules and stock events](ch09/README.md) | DRAFT |
| 10 | [Ask permission before spending](ch10/README.md) | DRAFT |
| 11 | [Survive the ambiguous supplier order](ch11/README.md) | DRAFT |
| 12 | [Recover work after a process crash](ch12/README.md) | DRAFT |
| 13 | [Connect an external tool with MCP](ch13/README.md) | PLANNED |
| 14 | [Isolate tools and untrusted content](ch14/README.md) | DRAFT |
| 15 | [Measure whether the agent helps](ch15/README.md) | DRAFT |
| 16 | [Improve behavior with evaluated changes](ch16/README.md) | DRAFT |
| 17 | [Delegate one bounded task](ch17/README.md) | DRAFT |
| 18 | [Deploy and maintain the agent](ch18/README.md) | DRAFT |
| 19 | [Lucy leaves the shop for a day](ch19/README.md) | DRAFT |

The four parts are: **1–4, First useful construction**; **5–9, Continuity and initiative**; **10–14, Permission and external boundaries**; and **15–19, Evaluate and operate**.

## Working beside the manuscript

Use [runnable checkpoints](CHECKPOINTS.md) to reproduce the recorded mechanisms. Save chapter-built tools and the loop under [learner/](learner/README.md); the included completed files provide a comparison. The optional field appendices explain [Telegram identity setup](appendices/telegram-setup.md), [Linux maintenance](appendices/linux-maintenance-v1.md), [ZeoCore interoperability](appendices/zeocore-interop-v2.md), [reproducibility](appendices/reproducibility-v1.md), and [dated architectural comparisons](appendices/project-comparisons-v1.md).

The book uses a frozen Python environment from the repository root. Offline checkpoints need no model credentials, Telegram account, real purchasing account or private organizational service. Optional live exercises identify their extra facilities and keep their evidence separate. [Return to the four teaching assets](../README.md).
