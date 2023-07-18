# FASTAPI application

import os
import json
import logging
from contextlib import asynccontextmanager

import starlette.websockets
from fastapi import FastAPI, WebSocket
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)

# Constants

DEVICE_CREATE = "DeviceCreate"
DEVICE_MOVE = "DeviceMove"
MULTIPLE_MESSAGE = "MultipleMessage"

# Globals

topologies = {}


# types


class Device(BaseModel):
    name: str
    x: float
    y: float
    device_type: str
    host_id: int
    id: int


class Topology(BaseModel):
    id: int
    devices: dict[int, Device]


def load_topology():
    global topologies
    if os.path.exists("topology.json"):
        with open("topology.json") as f:
            data = json.loads(f.read())
        devices = {}
        for device in data.get("devices", {}).values():
            devices[device["id"]] = Device(**device)
        topology = Topology(id=0, devices=devices)
        topologies[topology.id] = topology
    else:
        topology = Topology(id=0, devices={})
        topologies[topology.id] = topology


# API


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_topology()
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


def build_topology():
    return jsonable_encoder(topologies[0])


def save_topology(topology_json):
    with open("topology.json", "w") as f:
        f.write(json.dumps(topology_json))


def build_snapshot():
    snapshot = {"msg_type": "Snapshot"}
    topology = build_topology()
    snapshot['devices'] = list(topology['devices'].values())
    return ['Snapshot', snapshot]


def xy_to_float(message_data):
    message_data['x'] = float(message_data['x'])
    message_data['y'] = float(message_data['y'])

def handle_message(message_type, message_data):
    if message_type == DEVICE_CREATE:
        xy_to_float(message_data)
        message_data['device_type'] = message_data['type']
        topologies[0].devices[message_data["id"]] = Device(**message_data)
    if message_type == DEVICE_MOVE:
        xy_to_float(message_data)
        topologies[0].devices[message_data["id"]].__dict__.update(
            x=message_data["x"], y=message_data["y"]
        )

    if message_data == MULTIPLE_MESSAGE:
        for message in message_data["messages"]:
            handle_message(message["msg_type"], message)


@app.websocket("/ws/network_ui")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    async def send(data):
        await websocket.send_text(json.dumps(data))


    await send(build_snapshot())

    try:
        while True:
            data = await websocket.receive_text()
            print("websocket:", data, type(data))
            message = json.loads(data)
            message_type, message_data = message
            print(message_type)
            print(message_data)
            print(build_topology())
            handle_message(message_type, message_data)

            save_topology(build_topology())

    except starlette.websockets.WebSocketDisconnect as e:
        logger.error("websocket_endpoint %s", e)
        print("websocket_endpoint %s", e)
