# Rem Persona Cloner & Fine-Tuning Suite 🧠✨

This directory provides end-to-end tooling to clone your personal texting cadence or train specialized companion personas directly from raw chat exports (WhatsApp `.txt` or Discord `.json`).

---

## Architecture Overview

```
[WhatsApp .txt / Discord JSON Export]
                 │
                 ▼
      [ml/chat_parser.py]
• Filters system notices & media placeholders
• Groups rapid consecutive texts into burst turns ('|||')
• Formats into multi-turn ChatML JSONL format
                 │
                 ▼
      [ml/train_lora.py (Unsloth QLoRA)]
• Base: unsloth/Llama-3.2-3B-Instruct or unsloth/Qwen2.5-7B-Instruct
• Target: QLoRA (Rank=16, Alpha=32)
• Response-only loss masking
• Training time: ~20 mins on free Colab T4 GPU
                 │
                 ▼
      [Trained LoRA Adapter (~35MB)]
• Loaded into vLLM, Ollama, or Hugging Face runtime for authentic cadence!
```

---

## Step 1: Exporting Your Chat

### WhatsApp
1. Open the WhatsApp conversation on your phone.
2. Tap the contact name at the top $\to$ scroll down to **Export Chat**.
3. Select **Without Media** (attaching media creates large unnecessary zip files).
4. Save the resulting `_chat.txt` file into `data/my_chat.txt`.

### Discord
1. Use [DiscordChatExporter](https://github.com/Tyrrrz/DiscordChatExporter) (CLI or GUI).
2. Export your direct messages or channel as **JSON**.
3. Save the resulting file into `data/discord_chat.json`.

---

## Step 2: Parsing & Ingesting (`chat_parser.py`)

Run the parser to aggregate rapid texts into `|||` delimited turns and build a ChatML dataset:

```bash
# Parse WhatsApp export
python3 ml/chat_parser.py \
  --input data/my_chat.txt \
  --target "Rem" \
  --output data/rem_training.jsonl \
  --burst-gap 90 \
  --session-gap 3.0

# Parse Discord export
python3 ml/chat_parser.py \
  --input data/discord_chat.json \
  --target "rem_username" \
  --output data/rem_training.jsonl
```

### Key Arguments:
- `--target`: The exact sender name of the person you want Rem to speak like. This speaker is mapped to `assistant`, and the other person is mapped to `user`.
- `--burst-gap`: Seconds threshold to join consecutive texts from the same sender with ` ||| ` (default: 90s).
- `--session-gap`: Inactivity hours used to segment new conversation sessions (default: 3.0h).

---

## Step 3: QLoRA Fine-Tuning (`train_lora.py`)

Fine-tune on a free Google Colab T4 GPU (or any local NVIDIA GPU with $\ge$8GB VRAM):

```bash
python3 ml/train_lora.py \
  --dataset data/rem_training.jsonl \
  --model unsloth/Llama-3.2-3B-Instruct \
  --output outputs/rem_lora \
  --epochs 3 \
  --batch-size 2 \
  --lr 2e-4
```

### Export to Ollama / GGUF
To export a quantized GGUF model for local deployment in Ollama or llama.cpp, add the `--gguf` flag:

```bash
python3 ml/train_lora.py \
  --dataset data/rem_training.jsonl \
  --model unsloth/Llama-3.2-3B-Instruct \
  --gguf
```

---

## Step 4: Loading into the Emotion Agent

Once trained, set the model or adapter in `backend/.env`:

```env
MODEL_ID=outputs/rem_lora/lora_adapter
# or for local Ollama / vLLM:
# INFERENCE_URL=http://localhost:11434/v1/chat/completions
# MODEL_ID=rem-custom:latest
```
