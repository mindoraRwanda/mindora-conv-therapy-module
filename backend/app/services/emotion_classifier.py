import torch
from sentence_transformers import SentenceTransformer, util

import os
hf_token = os.getenv("HUGGINGFACE_HUB_TOKEN")
model = SentenceTransformer("BAAI/bge-small-en", use_auth_token=hf_token)


# Emotion categories and example prompts
emotion_examples = {
    "sadness": [
        "I feel like crying all the time.",
        "Nothing makes me happy anymore.",
        "I’m tired of everything.",
        "I don’t see the point in anything.",
        "I feel so low I can’t get out of bed."
    ],
    "anxiety": [
        "I'm always overthinking everything.",
        "I can't calm down, my mind won’t stop racing.",
        "I’m scared something bad will happen.",
        "I feel shaky and nervous all day.",
        "I worry about everything, even small things."
    ],
    "stress": [
        "I feel like I’m drowning in responsibilities.",
        "I can't take any more pressure.",
        "Everything is too much right now.",
        "I feel burned out.",
        "I’m overwhelmed and can’t focus."
    ],
    "fear": [
        "I’m terrified for no reason.",
        "I had a panic attack earlier.",
        "I feel unsafe, even at home.",
        "I’m afraid something is going to go wrong.",
        "My heart races and I can’t breathe when I think about it."
    ],
    "anger": [
        "I get irritated at everyone.",
        "I feel like screaming sometimes.",
        "Everything makes me so mad lately.",
        "I can’t control my temper.",
        "I feel like I’m going to explode."
    ],
    "guilt": [
        "I hate myself for what I did.",
        "I feel so ashamed.",
        "I can’t forgive myself.",
        "I’m a failure to everyone.",
        "People would hate me if they knew the truth."
    ],
    "craving": [
        "I really want to drink again.",
        "I’m trying to quit but I can’t stop.",
        "The urge to use is too strong.",
        "I feel like I need something to cope.",
        "I keep going back to old habits."
    ],
    "numbness": [
        "I don’t feel anything anymore.",
        "It’s like I’m empty inside.",
        "I can’t care about anything.",
        "Nothing matters to me now.",
        "I just go through the motions."
    ],
    "joy": [
        "Today actually felt okay.",
        "I laughed and it felt good.",
        "I feel lighter than usual.",
        "Something good finally happened.",
        "I think I’m starting to feel better."
    ],
    "neutral": [
        "Hello",
        "Hi",
        "How are you?",
        "Just checking in.",
        "Hey there"
        ]

}

# Precompute embeddings
emotion_embeddings = {
    label: model.encode(prompts, convert_to_tensor=True)
    for label, prompts in emotion_examples.items()
}

def classify_emotion(user_input: str) -> str:
    input_embedding = model.encode(user_input, convert_to_tensor=True)

    best_label = None
    best_score = -1

    for label, embeddings in emotion_embeddings.items():
        cosine_scores = util.cos_sim(input_embedding, embeddings)
        avg_score = torch.mean(cosine_scores).item()

        if avg_score > best_score:
            best_score = avg_score
            best_label = label

    # Set a confidence threshold
    threshold = 0.35
    if best_score < threshold:
        return "neutral"

    return best_label

# # Example usage
# if __name__ == "__main__":
#     test_input = "I can’t sleep, I keep thinking about everything that could go wrong."
#     predicted_emotion = classify_emotion(test_input)
#     print(f"Predicted Emotion: {predicted_emotion}")
