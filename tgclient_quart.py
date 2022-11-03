import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

model_repos = [
    "sismetanin/sbert-ru-sentiment-rusentiment",
]
model_names = [
    "sbert-ru-sentiment-rusentiment",
]

models = []
tokenizers = []

output_permutations = [
    [0, 1, 2]
]

torch.set_printoptions(precision=3, sci_mode=False, linewidth=70)

for repo in model_repos:
    tokenizers.append(AutoTokenizer.from_pretrained(repo))
    models.append(AutoModelForSequenceClassification.from_pretrained(repo))

i = 0
model = models[i]
tokenizer = tokenizers[i]
perm = output_permutations[i]

import random

def predict(phrases):
    # return [random.random() for i in range(3)]
    inputs = tokenizer(phrases, return_tensors="pt", padding=True)
    outputs = torch.nn.functional.softmax(model(**inputs).logits.detach(), dim=1)
    return torch.nn.functional.normalize(outputs[:, :3][:, perm])


from telethon.sync import TelegramClient, events
import redis
import json
import time

r = redis.StrictRedis('queue', 6379, charset="utf-8", decode_responses=True)


import logging
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.INFO)

MAX_MESSAGE_LEN = 100

##########################################################
# source https://github.com/LonamiWebs/Telethon/blob/v1/telethon_examples/quart_login.py

import base64
import os

import hypercorn.asyncio
from quart import Quart, render_template_string, request

from telethon import TelegramClient, utils
from telethon.errors import SessionPasswordNeededError


def get_env(name, message):
    if name in os.environ:
        return os.environ[name]
    return input(message)


BASE_TEMPLATE = '''
<!DOCTYPE html>
<html>
    <head>
        <meta charset='UTF-8'>
        <title>Login</title>
    </head>
    <body>{{ content | safe }}</body>
</html>
'''

PHONE_FORM = '''
<form action='/' method='post'>
    Phone (international format): <input name='phone' type='text' placeholder='+34600000000'>
    <input type='submit'>
</form>
'''

CODE_FORM = '''
<form action='/' method='post'>
    Telegram code: <input name='code' type='text' placeholder='70707'>
    <input type='submit'>
</form>
'''

PASSWORD_FORM = '''
<form action='/' method='post'>
    Telegram password: <input name='password' type='text' placeholder='your password'>
    <input type='submit'>
</form>
'''

# Session name, API ID and hash to use; loaded from environmental variables
SESSION = os.environ.get('TG_SESSION', 'quart')
API_ID =  int(os.environ.get('TG_APP_ID'))
API_HASH = os.environ.get('TG_APP_HASH')
DEBUG = bool(os.environ.get('DEBUG', False))

# Telethon client
client = TelegramClient(SESSION, API_ID, API_HASH)
client.parse_mode = 'html'  # <- Render things nicely
phone = None

# Quart app
app = Quart(__name__)
app.secret_key = os.environ.get('APP_SECRET')


# Helper method to format messages nicely
async def format_message(message):
    if message.photo:
        content = '<img src="data:image/png;base64,{}" alt="{}" />'.format(
            base64.b64encode(await message.download_media(bytes)).decode(),
            message.raw_text
        )
    else:
        # client.parse_mode = 'html', so bold etc. will work!
        content = (message.text or '(action message)').replace('\n', '<br>')

    return '<p><strong>{}</strong>: {}<sub>{}</sub></p>'.format(
        utils.get_display_name(message.sender),
        content,
        message.date
    )


# Connect the client before we start serving with Quart
@app.before_serving
async def startup():
    await client.connect()


# After we're done serving (near shutdown), clean up the client
@app.after_serving
async def cleanup():
    await client.disconnect()


@app.route('/', methods=['GET', 'POST'])
async def root():
    # We want to update the global phone variable to remember it
    global phone

    # Check form parameters (phone/code)
    form = await request.form
    if 'phone' in form:
        phone = form['phone']
        await client.send_code_request(phone)

    if 'code' in form:
        try:
            await client.sign_in(code=form['code'])
        except SessionPasswordNeededError:
            return await render_template_string(BASE_TEMPLATE, content=PASSWORD_FORM)

    if 'password' in form:
        await client.sign_in(password=form['password'])

    # If we're logged in, show them some messages from their first dialog
    if await client.is_user_authorized():
        # They are logged in, show them some messages from their first dialog
        # dialog = (await client.get_dialogs())[0]
        result = '<h1>You are authorized</h1>'
        # async for m in client.iter_messages(dialog, 10):
        #     result += await(format_message(m))

        return await render_template_string(BASE_TEMPLATE, content=result)

    # Ask for the phone if we don't know it yet
    if phone is None:
        return await render_template_string(BASE_TEMPLATE, content=PHONE_FORM)

    # We have the phone, but we're not logged in, so ask for the code
    return await render_template_string(BASE_TEMPLATE, content=CODE_FORM)


async def main():
    config = hypercorn.Config()
    config.bind = "0.0.0.0:8001"
    await hypercorn.asyncio.serve(app, config)

@client.on(events.NewMessage(incoming=True, outgoing=False))
async def handler(event):
    if event.is_private and event.message.message:
        sender = await event.get_sender()
        first_name = sender.first_name if sender.first_name is not None else ""
        second_name = sender.last_name if sender.last_name is not None else ""
        message = event.message.message[:MAX_MESSAGE_LEN]
        probs = predict([message])
        result = dict(
            probs=probs,
            time=time.time()
        )
        if DEBUG:
            result.update(dict(
                first_name=first_name,
                second_name=second_name,
                message=event.message.message
            ))
        r.publish("predictions", json.dumps(result))
        logging.info(f"{first_name} {second_name}: {event.message.message}")
        logging.info(f"Semantic: {probs}")


# By default, `Quart.run` uses `asyncio.run()`, which creates a new asyncio
# event loop. If we create the `TelegramClient` before, `telethon` will
# use `asyncio.get_event_loop()`, which is the implicit loop in the main
# thread. These two loops are different, and it won't work.
#
# So, we have to manually pass the same `loop` to both applications to
# make 100% sure it works and to avoid headaches.
#
# To run Quart inside `async def`, we must use `hypercorn.asyncio.serve()`
# directly.
#
# This example creates a global client outside of Quart handlers.
# If you create the client inside the handlers (common case), you
# won't have to worry about any of this, but it's still good to be
# explicit about the event loop.
if __name__ == '__main__':
    client.loop.run_until_complete(main())