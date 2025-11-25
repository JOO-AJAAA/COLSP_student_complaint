# --- CONFIGURATION API huggingface and token---
# Use the HF router host for inference. Hugging Face has moved to the router
# endpoint for many setups; if you have a custom router, replace these URLs.
HF_API_URL_SPAM = "https://router.huggingface.co/hf-inference/models/mrm8488/bert-tiny-finetuned-sms-spam-detection"
HF_API_URL_TOXIC = "https://router.huggingface.co/hf-inference/models/unitary/multilingual-toxic-xlm-roberta"
HF_API_URL_NSFW = "https://router.huggingface.co/hf-inference/models/Falconsai/nsfw_image_detection"