import torch
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    pipeline,
)
from config import NER_MODEL_PATH

# -------- NER --------

tokenizer = AutoTokenizer.from_pretrained(NER_MODEL_PATH)
model = AutoModelForTokenClassification.from_pretrained(NER_MODEL_PATH)
model.eval()

replace_dict = {
    "PER": "*имя*",
    "LOC": "*город*",
    "ORG": "*организация*"
}

def anonymize_text(text: str) -> str:
    words = text.split()

    inputs = tokenizer(
        words,
        is_split_into_words=True,
        return_tensors="pt",
        truncation=True,
        padding="max_length",
        max_length=128
    )

    with torch.no_grad():
        outputs = model(**inputs)

    predictions = torch.argmax(outputs.logits, dim=-1)
    word_ids = inputs.word_ids(batch_index=0)

    pred_labels = []
    prev_word_id = None

    for i, word_id in enumerate(word_ids):
        if word_id is None or word_id == prev_word_id:
            continue
        label = model.config.id2label[predictions[0, i].item()]
        pred_labels.append(label)
        prev_word_id = word_id

    filtered_words = []
    for word, label in zip(words, pred_labels):
        entity = label.split("-")[-1]
        filtered_words.append(replace_dict.get(entity, word))

    return " ".join(filtered_words)

# -------- MOOD --------

mood_model = pipeline(
    "sentiment-analysis",
    model="blanchefort/rubert-base-cased-sentiment"
)

def analyze_sentiment(text: str) -> str:
    result = mood_model(text)[0]["label"]
    return "happy" if result == "POSITIVE" else "sad"
