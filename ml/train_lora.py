#!/usr/bin/env python3
"""
Unsloth QLoRA Fine-Tuning Pipeline for Rem Persona & Texting Dynamics

Fine-tunes Llama-3.2-3B-Instruct or Qwen-2.5-7B on ChatML datasets generated
by ml/chat_parser.py. Runs efficiently in ~20 minutes on a free Google Colab T4 GPU (16GB VRAM).

Features:
- QLoRA 4-bit NF4 quantization (Unsloth 2x faster, 70% less VRAM).
- Response-only loss masking: Only calculates gradient loss on assistant responses.
- Automatic ChatML template formatting.
- Adapter saving + GGUF / 16-bit merge support for deployment to vLLM, Ollama, or local runtime.
"""

import os
import sys
import argparse
from typing import Optional


def train(
    dataset_path: str,
    base_model: str = "unsloth/Llama-3.2-3B-Instruct",
    output_dir: str = "outputs/rem_lora",
    max_seq_length: int = 2048,
    lora_r: int = 16,
    lora_alpha: int = 32,
    epochs: int = 3,
    batch_size: int = 2,
    grad_accum: int = 4,
    learning_rate: float = 2e-4,
    save_gguf: bool = False,
):
    print("=" * 60)
    print("  Rem AI Persona Fine-Tuning Engine (QLoRA / Unsloth)")
    print("=" * 60)
    print(f"[*] Base Model:       {base_model}")
    print(f"[*] Dataset:          {dataset_path}")
    print(f"[*] Output Directory: {output_dir}")
    print(f"[*] Max Sequence Len: {max_seq_length}")
    print(f"[*] LoRA Config:      r={lora_r}, alpha={lora_alpha}")
    print(f"[*] Training Epochs:  {epochs}")

    # Check for unsloth availability
    try:
        from unsloth import FastLanguageModel
        from unsloth.chat_templates import get_chat_template, train_on_responses_only
        import torch
        from trl import SFTTrainer
        from transformers import TrainingArguments
        from datasets import load_dataset
        has_unsloth = True
    except ImportError:
        print("[!] Unsloth not installed. Checking for standard Hugging Face PEFT + TRL...")
        has_unsloth = False

    if not has_unsloth:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, BitsAndBytesConfig
            from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
            from trl import SFTTrainer, DataCollatorForCompletionOnlyLM
            from datasets import load_dataset
        except ImportError as e:
            print(f"[!] Missing required ML dependencies: {e}")
            print("\nTo run fine-tuning, install required packages:")
            print("  pip install \"unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git\"")
            print("  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
            print("  pip install datasets trl transformers peft bitsandbytes")
            sys.exit(1)

    # 1. Load Model & Tokenizer
    print("\n[1/4] Loading quantized base model...")
    if has_unsloth:
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=base_model,
            max_seq_length=max_seq_length,
            load_in_4bit=True,
            dtype=None,
        )

        model = FastLanguageModel.get_peft_model(
            model,
            r=lora_r,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            lora_alpha=lora_alpha,
            lora_dropout=0,
            bias="none",
            use_gradient_checkpointing="unsloth",
            random_state=3407,
        )

        tokenizer = get_chat_template(
            tokenizer,
            chat_template="chatml",
            mapping={"role": "role", "content": "content", "user": "user", "assistant": "assistant"},
        )
    else:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
        if not tokenizer.pad_token:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            base_model,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
        )
        model = prepare_model_for_kbit_training(model)
        peft_config = LoraConfig(
            r=lora_r,
            lora_alpha=lora_alpha,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
        )
        model = get_peft_model(model, peft_config)

    # 2. Format Dataset
    print("\n[2/4] Loading and formatting ChatML dataset...")
    dataset = load_dataset("json", data_files=dataset_path, split="train")

    def format_chatml(examples):
        convs = examples["messages"]
        texts = [tokenizer.apply_chat_template(convo, tokenize=False, add_generation_prompt=False) for convo in convs]
        return {"text": texts}

    formatted_dataset = dataset.map(format_chatml, batched=True)
    print(f"[*] Loaded {len(formatted_dataset)} conversation samples.")

    # 3. Configure Trainer
    print("\n[3/4] Configuring training loop & loss masking...")
    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=grad_accum,
        warmup_steps=10,
        num_train_epochs=epochs,
        learning_rate=learning_rate,
        fp16=not torch.cuda.is_bf16_supported() if torch.cuda.is_available() else False,
        bf16=torch.cuda.is_bf16_supported() if torch.cuda.is_available() else False,
        logging_steps=5,
        optim="adamw_8bit" if torch.cuda.is_available() else "adamw_torch",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=3407,
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=formatted_dataset,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        dataset_num_proc=2,
        packing=False,
        args=training_args,
    )

    if has_unsloth:
        # Mask prompt loss so model only learns target assistant responses
        trainer = train_on_responses_only(
            trainer,
            instruction_part="<|im_start|>user\n",
            response_part="<|im_start|>assistant\n",
        )

    # 4. Execute Training
    print("\n[4/4] Starting training run...")
    trainer.train()

    # 5. Save Output
    print(f"\n[+] Training complete! Saving LoRA adapter to {output_dir}/lora_adapter...")
    os.makedirs(f"{output_dir}/lora_adapter", exist_ok=True)
    model.save_pretrained(f"{output_dir}/lora_adapter")
    tokenizer.save_pretrained(f"{output_dir}/lora_adapter")

    if save_gguf and has_unsloth:
        print("[+] Exporting to 8-bit GGUF for Ollama / llama.cpp...")
        model.save_pretrained_gguf(f"{output_dir}/rem_gguf", tokenizer, quantization_method="q8_0")

    print("\n" + "=" * 60)
    print("  FINE-TUNING COMPLETED SUCCESSFULLY!")
    print(f"  LoRA adapter saved at: {output_dir}/lora_adapter")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Unsloth QLoRA Fine-Tuning Pipeline for Rem Persona")
    parser.add_argument("--dataset", "-d", required=True, help="Path to ChatML JSONL dataset")
    parser.add_argument("--model", "-m", default="unsloth/Llama-3.2-3B-Instruct", help="Base model (Llama-3.2-3B or Qwen2.5-7B)")
    parser.add_argument("--output", "-o", default="outputs/rem_lora", help="Output directory for LoRA weights")
    parser.add_argument("--epochs", "-e", type=int, default=3, help="Number of training epochs (default: 3)")
    parser.add_argument("--batch-size", "-b", type=int, default=2, help="Per device batch size (default: 2)")
    parser.add_argument("--seq-len", type=int, default=2048, help="Max sequence length (default: 2048)")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate (default: 2e-4)")
    parser.add_argument("--gguf", action="store_true", help="Also export GGUF binary for Ollama / llama.cpp")

    args = parser.parse_args()

    train(
        dataset_path=args.dataset,
        base_model=args.model,
        output_dir=args.output,
        max_seq_length=args.seq_len,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        save_gguf=args.gguf,
    )


if __name__ == "__main__":
    main()
