# Telegram field setup

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

Read [Chapter 8](../ch08/profrod-sovereign-agent-ch08-telegram-messaging-chapter.md) for the adapter and identity model. Its offline checkpoint uses a fake bot and needs no account. The optional field exercise needs your own dedicated teaching bot, a private chat initiated by you and explicit consent from everyone involved in the test exchange.

Follow Telegram's [official tutorial](https://core.telegram.org/bots/tutorial) to create the bot. Keep the credential in an operator-owned environment file outside this repository. The bot token authenticates the application; numeric sender and chat IDs select the authorized person and conversation. A display name is not an authorization identity.

From the repository root, run the identity helper described in Chapter 8:

```bash
uv run python book/textbook/appendices/profrod_sovereign_agent_textbook_telegram_identity_v1.py
```

Then use Chapter 8's exact environment and `--telegram` command with a fresh local state directory. Retain sanitized intake, work and delivery identities, restart the process, and inspect the reply on the actual handset. Do not include tokens in screenshots or evidence. A missing credential leaves the field exercise unperformed; it does not prevent the offline core lesson.

The remaining field and retry requirements are recorded in [the integration roadmap](../profrod-sovereign-agent-textbook-expansion.md#telegram-and-operating-integrations).

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
