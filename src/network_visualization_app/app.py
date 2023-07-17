# FASTAPI application

import json
import logging
from contextlib import asynccontextmanager

import starlette.websockets
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

# types

# API


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Network Visualization",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    async def send(data):
        await websocket.send_text(json.dumps(data))

    try:
        while True:
            data = await websocket.receive_text()
            print("websocket:", data, type(data))
    except starlette.websockets.WebSocketDisconnect as e:
        logger.error("websocket_endpoint %s", e)
        print("websocket_endpoint %s", e)
