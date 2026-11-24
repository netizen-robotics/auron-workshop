# 08 · LLMs, Ollama and Gemma 4

[Workshop topic index](../README.md#topics)

Run Ollama on your laptop and keep the same model available for [Topic 09](../09_python_agent/README.md).

An **LLM** is a large language model that generates a response using the prompt and context it receives. **Gemma 4** is the model and **Ollama** is the tool that downloads and runs it. Install and start [Ollama](https://ollama.com/download) on the laptop. If the Linux service is inactive, run `ollama serve` in a separate terminal.

```text
ollama --version
ollama pull gemma4:e2b
ollama list
ollama run gemma4:e2b
```

Ask **“What is Auron's current battery reading?”** Identify the live data the model would need. Enter `/bye` to return to the shell. Pre-download the model before class. Pair up at a prepared station if needed.
