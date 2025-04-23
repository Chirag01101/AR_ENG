from transformers import MarianMTModel, MarianTokenizer
import os

# Define model and save path
model_name = "Helsinki-NLP/opus-mt-ar-en"
save_path = "./models/opus-mt-ar-en"

# Check if already downloaded
if not os.path.exists(save_path):
    print("🔄 Downloading model and tokenizer...")
    model = MarianMTModel.from_pretrained(model_name)
    tokenizer = MarianTokenizer.from_pretrained(model_name)

    model.save_pretrained(save_path)
    tokenizer.save_pretrained(save_path)
    print(f"✅ Model and tokenizer saved to {save_path}")
else:
    print(f"📦 Using cached model from {save_path}")
    model = MarianMTModel.from_pretrained(save_path)
    tokenizer = MarianTokenizer.from_pretrained(save_path)

# Test translation
text = "مرحبا بك في عالم الذكاء الاصطناعي"
inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
translated = model.generate(**inputs)
output = tokenizer.decode(translated[0], skip_special_tokens=True)

print("🔤 Translated Text:", output)
