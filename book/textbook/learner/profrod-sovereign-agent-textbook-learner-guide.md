# Your constructed definitions

> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.
> **Read the full book and get the latest learning materials:** [https://profrod.ai/book](https://profrod.ai/book).
> **Join the Prof Rod learner community:** [https://profrod.ai/community](https://profrod.ai/community)
> — bring your questions, compare experiments and share what you build.
> **Original source and updates:** [profrodai/sovereign-agent](https://github.com/profrodai/sovereign-agent).

Each file below is the completed comparison implementation for one chapter's construction. Work in your own checkout, and retain your attempts before replacing them with a comparison.

| Chapter | File | What it builds |
| --- | --- | --- |
| 1 | `profrod_sovereign_agent_ch01_model_call_learner.py` | Byte-pair encoding, a bigram model, softmax with temperature, sampling, entropy and perplexity |
| 2 | `profrod_sovereign_agent_ch02_pydantic_shop_tools_learner.py` | Tool schemas, handlers and dispatch |
| 2 | `profrod_sovereign_agent_ch02_constrained_decoding_learner.py` | Validity over length, logit masking, and masked decoding against conditioning on a toy model |
| 3 | `profrod_sovereign_agent_ch03_agent_loop_learner.py` | The owned model and tool loop, its adapter, and the reliability arithmetic |
| 4 | `profrod_sovereign_agent_ch04_state_store_learner.py` | The durable state store |
| 5 | `profrod_sovereign_agent_ch05_retrieval_learner.py` | BM25, cosine similarity, precision@k, recall@k, reciprocal rank and a context packer |
| 6 | `profrod_sovereign_agent_ch06_prompt_sensitivity_learner.py` | Labels from free text, accuracy, spread across prompts, case-sampling noise and agreement |
| 7 | `profrod_sovereign_agent_ch07_work_queue_learner.py` | The durable work queue |
| 14 | `profrod_sovereign_agent_ch14_injection_learner.py` | Attempted-action checks, attack success rates with intervals, and spotlighting |
| 15 | `profrod_sovereign_agent_ch15_evaluation_statistics_learner.py` | Wilson intervals, clustered standard errors, McNemar's test, sample size, pass@k and kappa |
| 16 | `profrod_sovereign_agent_ch16_optimization_learner.py` | The expected maximum of k normals, the winner's curse, and Bradley–Terry ratings fitted from preferences |
| 18 | `profrod_sovereign_agent_ch18_inference_economics_learner.py` | Decode ceilings, arithmetic intensity, KV-cache memory, latency, percentiles, Little's law and loop cost |

Each chapter's checkpoint loads its file, so changing a function's essential behavior changes the executable result. The live adapters still use supplied bounded HTTP transport, and later reference checkpoints import other supplied runtime components. See [code ownership](../profrod-sovereign-agent-textbook-ownership.md) and the [construction roadmap](../profrod-sovereign-agent-textbook-expansion.md) before treating these files as a finished nineteen-chapter agent.

## Keep building with Prof Rod

Found this material through a colleague, classroom or shared download? [Get the complete book at profrod.ai/book](https://profrod.ai/book) and [join the Prof Rod learner community](https://profrod.ai/community). Bring one result, one question or one failure you learned from. Share this resource with another learner and keep its source links with it so they can find the full course and future updates.
