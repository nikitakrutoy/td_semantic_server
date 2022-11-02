from flask import Flask, jsonify
import redis
import json

app = Flask(__name__)

r = redis.StrictRedis('queue', 6379, charset="utf-8", decode_responses=True)
sub = r.pubsub()
sub.subscribe('predictions')

@app.route("/")
def hello_world():
    messages = []
    while m := sub.get_message():
        data = json.loads(str(m.get("data")))
        print(data)
        messages.append(data)
    
    return jsonify(messages)