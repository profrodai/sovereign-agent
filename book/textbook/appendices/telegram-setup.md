# Telegram field setup

Read [Chapter 8](../ch08/README.md) for the adapter and identity model. Its offline checkpoint uses a fake bot and needs no account. The optional field exercise needs your own dedicated teaching bot, a private chat initiated by you and explicit consent from everyone involved in the test exchange.

Follow Telegram's [official tutorial](https://core.telegram.org/bots/tutorial) to create the bot. Keep the credential in an operator-owned environment file outside this repository. The bot token authenticates the application; numeric sender and chat IDs select the authorized person and conversation. A display name is not an authorization identity.

From the repository root, run the identity helper described in Chapter 8:

```bash
uv run python book/textbook/appendices/telegram_identity_v1.py
```

Then use Chapter 8's exact environment and `--telegram` command with a fresh local state directory. Retain sanitized intake, work and delivery identities, restart the process, and inspect the reply on the actual handset. Do not include tokens in screenshots or evidence. A missing credential leaves the field exercise unperformed; it does not prevent the offline core lesson.

The remaining field and retry requirements are recorded in [the integration roadmap](../EXPANSION.md#telegram-and-operating-integrations).
