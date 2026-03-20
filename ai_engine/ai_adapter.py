# ai_engine/ai_adapter.py
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import os

class AIAdapter:
    def __init__(self):
        # Sửa "phobert-ahn-final" thành "phobert-ahp-final"
        self.model_path = os.path.join(os.path.dirname(__file__), "phobert-ahp-final")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_path)
        self.model.eval()

# ... (Giữ nguyên các phần code bên dưới của bạn)

    def get_weights(self, user_text: str) -> dict:
        inputs = self.tokenizer(user_text, return_tensors="pt", truncation=True, padding=True, max_length=256)
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1).squeeze()

        weights = {
            "Giá": float(probs[0]),
            "Hiệu năng": float(probs[1]),
            "Trải nghiệm": float(probs[2]),
            "Camera": float(probs[3])
        }
        total = sum(weights.values())
        for k in weights:
            weights[k] = round(weights[k] / total, 4)
        return weights