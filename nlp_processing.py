import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
from config import NER_MODEL_PATH

# ====== Настройка устройства ======
DEVICE = torch.device("cpu")  # Render бесплатный тариф — CPU only

# ====== Загрузка NER-модели ======
tokenizer = AutoTokenizer.from_pretrained(NER_MODEL_PATH)
model = AutoModelForTokenClassification.from_pretrained(
    NER_MODEL_PATH,
    torch_dtype=torch.float32  # экономим память
)
model.to(DEVICE)
model.eval()

# Словарь для замены сущностей
REPLACE_DICT = {
    "PER": "*имя*",
    "LOC": "*город*",
    "ORG": "*организация*"
}


def anonymize_text(text: str) -> str:
    # Разбиваем на слова
    words = text.split()

    # Токенизация (без max_length, экономим память)
    inputs = tokenizer(
        words,
        is_split_into_words=True,
        return_tensors="pt",
        truncation=True,
        padding=True  # minimal padding
    ).to(DEVICE)

    # Инференс
    with torch.no_grad():
        outputs = model(**inputs)

    predictions = torch.argmax(outputs.logits, dim=-1)
    word_ids = inputs.word_ids(batch_index=0)

    # Получаем предсказанные метки на слово
    pred_labels = []
    prev_word_id = None
    for i, word_id in enumerate(word_ids):
        if word_id is None or word_id == prev_word_id:
            continue
        label = model.config.id2label[predictions[0, i].item()]
        pred_labels.append(label)
        prev_word_id = word_id

    # Заменяем сущности
    filtered_words = [
        REPLACE_DICT.get(label.split("-")[-1], word)
        if i < len(pred_labels) else word
        for i, (word, label) in enumerate(zip(words, pred_labels + ["O"] * len(words)))
    ]

    return " ".join(filtered_words)


# ====== Загрузка модели настроения ======
mood_model = pipeline(
    "sentiment-analysis",
    model="blanchefort/rubert-base-cased-sentiment",
    device=-1  # CPU only
)


def analyze_sentiment(text: str) -> str:
    result = mood_model(text, truncation=True)[0]["label"]
    return "happy" if result == "POSITIVE" else "sad"
