# td_semantic_server

TouchDesigner server for monitoring semantic of private messages from telegram.

## Usage

### Server

```
docker compose up -d --build
```

### Client

Add SemanticServer.tox to you td project. Set url in its parameters to your server url. 

Open your_server_addr:8001 in browser and login into your account
