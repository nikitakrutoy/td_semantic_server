# td_semantic_server

TouchDesigner server for monitoring semantic of private messages from telegram. Semantic is obtained on flask server with neural net.

## Usage

### Enviroment

Add `.env` file with your telegram app creadentials

```
TG_APP_ID=<your_app_id>
TG_APP_HASH=<your_app_hash>
APP_SECRET=<your_secret>
DEBUG=0
```

Set `DEBUG=1` to include senders name and message text in data. 

### CLI
Add SemanticServer.tox to you td project. Set url in its parameters to your server url. 

From app folder
```
python tgclient_cli.py
```

### TG Server

From app folder
```
docker compose up -d --build
```

### TD Client

Add SemanticClient.tox to you td project. Set url in its parameters to your server url. 

Open your_server_addr:8001 in browser and login into your account
