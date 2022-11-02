


import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

model_repos = [
    "sismetanin/sbert-ru-sentiment-rusentiment",
]
model_names = [
    "sbert-ru-sentiment-rusentiment",
]

# models = []
# tokenizers = []

# output_permutations = [
#     [0, 1, 2]
# ]

# torch.set_printoptions(precision=3, sci_mode=False, linewidth=70)

# for repo in model_repos:
#     tokenizers.append(AutoTokenizer.from_pretrained(repo))
#     models.append(AutoModelForSequenceClassification.from_pretrained(repo))

# i = 0
# model = models[i]
# tokenizer = tokenizers[i]
# perm = output_permutations[i]

import random

def predict(phrases):
    return [random.random() for i in range(3)]
    # inputs = tokenizer(phrases, return_tensors="pt", padding=True)
    # outputs = torch.nn.functional.softmax(model(**inputs).logits.detach(), dim=1)
    # return torch.nn.functional.normalize(outputs[:, :3][:, perm])


from telethon.sync import TelegramClient, events
import redis
import json
import time

r = redis.StrictRedis('localhost', 6379, charset="utf-8", decode_responses=True)


import logging
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.INFO)

api_id = int(os.environ.get('TG_APP_ID'))
api_hash = os.environ.get('TG_APP_HASH')

MAX_MESSAGE_LEN = 100
client = TelegramClient('session_name', api_id, api_hash)
# client.start()
# client.qr_login()

# with TelegramClient('name', api_id, api_hash) as client:
    # client.send_message('me', 'Hello, myself!')
    # print(client.download_profile_photo('me'))

@client.on(events.NewMessage(incoming=True, outgoing=False))
async def handler(event):
    if event.is_private and event.message.message:
        sender = await event.get_sender()
        first_name = sender.first_name if sender.first_name is not None else ""
        second_name = sender.last_name if sender.last_name is not None else ""
        message = event.message.message[:MAX_MESSAGE_LEN]
        probs = predict([message])
        result = dict(
            first_name=first_name,
            second_name=second_name,
            message=event.message.message,
            probs=probs,
            time=time.time()
        )
        r.publish("predictions", json.dumps(result))
        logging.info(f"{first_name} {second_name}: {event.message.message}")
        logging.info(f"Semantic: {probs}")

client.run_until_disconnected()