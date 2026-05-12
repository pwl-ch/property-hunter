# Local LLM Agents

PropertyHunter uses Pydantic AI agents for listing extraction and regulatory
summaries.

## Default Mode

The default agent mode is `llm`. It targets an LM Studio OpenAI-compatible
server:

```bash
PROPERTY_HUNTER_AGENT_MODE=llm
PROPERTY_HUNTER_LLM_PROVIDER=lm_studio
PROPERTY_HUNTER_LM_STUDIO_BASE_URL=http://127.0.0.1:1234/v1
PROPERTY_HUNTER_MODEL_NAME=google/gemma-4-e4b
PROPERTY_HUNTER_LLM_API_KEY=lm-studio
```

LM Studio documents OpenAI-compatible endpoints under `/v1`, including
`/v1/chat/completions`. Start the LM Studio local server, load
`google/gemma-4-e4b`, then run:

```bash
uv run property_hunter serve
```

## Structured Outputs

The extraction agent returns `ExtractedProperty` and the regulatory agent
returns `RegulatorySummary`. Both agents are built with:

```python
Agent(model, output_type=YourPydanticModel, instructions="...")
```

The model is an `OpenAIChatModel` configured with an `OpenAIProvider` pointed at
the LM Studio base URL.

## Offline Mode

For development without a running LLM server, use deterministic heuristic
agents:

```bash
PROPERTY_HUNTER_AGENT_MODE=heuristic uv run property_hunter serve
```

This mode keeps the API usable while preserving the same application ports.

## Real Listing Evaluation

The test suite includes an opt-in live evaluation against a real Otodom listing
snapshot for `Działka budowlana w Pępowie objęta MPZP`.

The normal test suite skips live LLM calls. To assess the configured LM Studio
model against the snapshot, start LM Studio on `http://127.0.0.1:1234/v1`, load
`google/gemma-4-e4b`, then run:

```bash
PROPERTY_HUNTER_RUN_LLM_EVALS=1 uv run pytest -m llm_eval
```

The evaluation checks whether the agents recover key facts such as price, area,
price per square meter, city, and MPZP information.

## Dashboard Agent Testing

Run the dashboard to test the configured agents interactively on fresh data:

```bash
uv run property_hunter dashboard
```

Use the **Agent test** panel to either paste listing text or provide a listing
URL. URL mode fetches the page locally, keeps the raw HTML snapshot, converts
visible HTML text into listing content, and runs the extraction and regulatory
agents without saving the result.

## Logging

PropertyHunter logs API requests, agent selection, analysis progress, adapter
failures, and persistence events through Python's standard `logging` module.
Set the level with:

```bash
PROPERTY_HUNTER_LOG_LEVEL=DEBUG uv run property_hunter serve
```

## References

- [Pydantic AI agents](https://pydantic.dev/docs/ai/core-concepts/agent/)
- [Pydantic AI OpenAI-compatible models](https://pydantic.dev/docs/ai/models/openai/)
- [LM Studio OpenAI compatibility endpoints](https://lmstudio.ai/docs/developer/openai-compat)
