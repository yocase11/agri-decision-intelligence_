import torch
import json
import argparse
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import Dataset
import os
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
import bitsandbytes as bnb

def load_dataset(json_file):
    """Load the Q&A dataset from JSON file"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def format_instruction(example):
    """Format the instruction-response pair for training"""
    instruction = example['instruction']
    input_text = example.get('input', '')
    output = example['output']

    if input_text:
        formatted_text = f"### Instruction:\n{instruction}\n\n### Input:\n{input_text}\n\n### Response:\n{output}"
    else:
        formatted_text = f"### Instruction:\n{instruction}\n\n### Response:\n{output}"

    return {"text": formatted_text}

def prepare_dataset(train_file, val_file=None):
    """Prepare the dataset for training"""
    # Load data
    train_data = load_dataset(train_file)
    train_dataset = Dataset.from_list(train_data)

    # Format for instruction tuning
    train_dataset = train_dataset.map(format_instruction)

    if val_file and os.path.exists(val_file):
        val_data = load_dataset(val_file)
        val_dataset = Dataset.from_list(val_data)
        val_dataset = val_dataset.map(format_instruction)
    else:
        # Split train data for validation if no val file provided
        train_dataset = train_dataset.train_test_split(test_size=0.1, seed=42)
        val_dataset = train_dataset['test']
        train_dataset = train_dataset['train']

    return train_dataset, val_dataset

def find_all_linear_names(model):
    """Find all linear layer names for LoRA"""
    cls = bnb.nn.Linear4bit
    lora_module_names = set()
    for name, module in model.named_modules():
        if isinstance(module, cls):
            names = name.split('.')
            lora_module_names.add(names[0] if len(names) == 1 else names[-1])
    if 'lm_head' in lora_module_names:
        lora_module_names.remove('lm_head')
    return list(lora_module_names)

def setup_model_and_tokenizer(model_name, use_4bit=True):
    """Setup model and tokenizer with optional quantization"""
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    if use_4bit:
        # Load model with 4-bit quantization
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            load_in_4bit=True,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
        )
        model = prepare_model_for_kbit_training(model)

        # Setup LoRA
        modules = find_all_linear_names(model)
        lora_config = LoraConfig(
            r=64,
            lora_alpha=16,
            target_modules=modules,
            lora_dropout=0.1,
            bias="none",
            task_type="CAUSAL_LM",
        )
        model = get_peft_model(model, lora_config)
    else:
        # Load model without quantization
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
        )

    model.config.use_cache = False
    model.config.pretraining_tp = 1

    return model, tokenizer

def tokenize_function(examples, tokenizer, max_length=512):
    """Tokenize the text data"""
    return tokenizer(
        examples["text"],
        truncation=True,
        padding="max_length",
        max_length=max_length,
    )

def train_model(args):
    """Main training function"""
    print(f"Loading model: {args.model_name}")
    model, tokenizer = setup_model_and_tokenizer(args.model_name, args.use_4bit)

    print("Preparing dataset...")
    train_dataset, val_dataset = prepare_dataset(args.train_file, args.val_file)

    # Tokenize datasets
    tokenized_train = train_dataset.map(
        lambda x: tokenize_function(x, tokenizer, args.max_length),
        batched=True,
        remove_columns=["text"]
    )
    tokenized_val = val_dataset.map(
        lambda x: tokenize_function(x, tokenizer, args.max_length),
        batched=True,
        remove_columns=["text"]
    )

    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )

    # Training arguments
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.num_epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        optim="paged_adamw_32bit",
        save_steps=args.save_steps,
        logging_steps=args.logging_steps,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        fp16=args.use_fp16,
        bf16=False,
        max_grad_norm=0.3,
        max_steps=-1,
        warmup_ratio=0.03,
        group_by_length=True,
        lr_scheduler_type="constant",
        evaluation_strategy="steps",
        eval_steps=args.eval_steps,
        save_strategy="steps",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
    )

    # Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_val,
        data_collator=data_collator,
    )

    print("Starting training...")
    trainer.train()

    # Save the model
    print(f"Saving model to {args.output_dir}")
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    print("Training completed!")

def main():
    parser = argparse.ArgumentParser(description="Fine-tune a language model for agricultural Q&A")
    parser.add_argument("--model_name", type=str, default="microsoft/DialoGPT-medium",
                       help="Pre-trained model name or path")
    parser.add_argument("--train_file", type=str, default="agricultural_train.json",
                       help="Path to training data JSON file")
    parser.add_argument("--val_file", type=str, default="agricultural_val.json",
                       help="Path to validation data JSON file")
    parser.add_argument("--output_dir", type=str, default="./agri_finetuned_model",
                       help="Output directory for the fine-tuned model")
    parser.add_argument("--num_epochs", type=int, default=3,
                       help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=4,
                       help="Batch size for training")
    parser.add_argument("--gradient_accumulation_steps", type=int, default=1,
                       help="Gradient accumulation steps")
    parser.add_argument("--learning_rate", type=float, default=2e-4,
                       help="Learning rate")
    parser.add_argument("--weight_decay", type=float, default=0.001,
                       help="Weight decay")
    parser.add_argument("--max_length", type=int, default=512,
                       help="Maximum sequence length")
    parser.add_argument("--save_steps", type=int, default=500,
                       help="Save model every N steps")
    parser.add_argument("--logging_steps", type=int, default=100,
                       help="Log every N steps")
    parser.add_argument("--eval_steps", type=int, default=500,
                       help="Evaluate every N steps")
    parser.add_argument("--use_4bit", action="store_true", default=True,
                       help="Use 4-bit quantization")
    parser.add_argument("--use_fp16", action="store_true", default=True,
                       help="Use FP16 training")

    args = parser.parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    train_model(args)

if __name__ == "__main__":
    main()