import torch
import json
import os
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import Dataset
from src.create_agri_dataset import create_agricultural_qa_dataset, create_training_split

def create_instruction_tuned_dataset():
    """Create dataset in instruction tuning format"""
    qa_pairs = create_agricultural_qa_dataset()

    # Convert to instruction format
    formatted_data = []
    for pair in qa_pairs:
        instruction = pair['instruction']
        input_text = pair.get('input', '')
        output = pair['output']

        if input_text:
            text = f"### Instruction:\n{instruction}\n\n### Input:\n{input_text}\n\n### Response:\n{output}"
        else:
            text = f"### Instruction:\n{instruction}\n\n### Response:\n{output}"

        formatted_data.append({"text": text})

    return formatted_data

def train_agricultural_model():
    """Train a model specifically for agricultural Q&A"""

    print("Creating agricultural Q&A dataset...")
    dataset = create_instruction_tuned_dataset()

    # Split dataset
    train_data, val_data = create_training_split(dataset, train_ratio=0.8)

    # Convert to HuggingFace datasets
    train_dataset = Dataset.from_list(train_data)
    val_dataset = Dataset.from_list(val_data)

    print(f"Training samples: {len(train_dataset)}")
    print(f"Validation samples: {len(val_dataset)}")

    # Use a smaller, more accessible model for fine-tuning
    model_name = "microsoft/DialoGPT-small"  # Smaller model for easier training

    print(f"Loading model: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(model_name)

    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            padding="max_length",
            max_length=256,  # Shorter sequences for efficiency
        )

    print("Tokenizing datasets...")
    tokenized_train = train_dataset.map(tokenize_function, batched=True, remove_columns=["text"])
    tokenized_val = val_dataset.map(tokenize_function, batched=True, remove_columns=["text"])

    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )

    # Training arguments optimized for smaller model
    training_args = TrainingArguments(
        output_dir="./agri_model",
        num_train_epochs=2,  # Fewer epochs for smaller model
        per_device_train_batch_size=2,  # Smaller batch size
        per_device_eval_batch_size=2,
        gradient_accumulation_steps=4,  # Accumulate gradients
        learning_rate=5e-5,  # Slightly higher learning rate
        weight_decay=0.01,
        save_steps=100,
        logging_steps=50,
        evaluation_strategy="steps",
        eval_steps=100,
        save_strategy="steps",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        fp16=True,  # Use mixed precision if available
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_val,
        data_collator=data_collator,
    )

    print("Starting training...")
    trainer.train()

    print("Saving model...")
    trainer.save_model("./agri_model")
    tokenizer.save_pretrained("./agri_model")

    print("Training completed! Model saved to ./agri_model")

    return "./agri_model"

def test_model(model_path):
    """Test the trained model"""
    print("Loading trained model for testing...")

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path)

    # Test questions
    test_questions = [
        "What crops should I grow this season?",
        "How can I improve soil fertility?",
        "What are the best practices for pest control?"
    ]

    print("\nTesting trained model:")
    print("=" * 50)

    for question in test_questions:
        input_text = f"### Instruction:\n{question}\n\n### Response:\n"

        inputs = tokenizer(input_text, return_tensors="pt", truncation=True, max_length=256)

        with torch.no_grad():
            outputs = model.generate(
                inputs["input_ids"],
                max_length=150,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract just the response part
        if "### Response:" in response:
            response = response.split("### Response:")[1].strip()

        print(f"Q: {question}")
        print(f"A: {response}")
        print("-" * 50)

if __name__ == "__main__":
    # Train the model
    model_path = train_agricultural_model()

    # Test the model
    test_model(model_path)

    print(f"\nModel training and testing completed!")
    print(f"Trained model saved at: {model_path}")
    print("You can now integrate this model into your chatbot system.")