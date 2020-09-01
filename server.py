#!/usr/bin/env python3

import asyncio
import websockets
import numpy as np
import cv2
from PIL import Image
import base64
from io import BytesIO
import json

global broadcast_task, cap, CLIENTS
CLIENTS = set()
cap = cv2.VideoCapture(0)


def capture_and_process(cap=cap):
    """Capture frame from video source and process."""
    # Capture frame-by-frame
    frame_got, frame = cap.read()
    if frame_got is False:
        return None
    
    # frame processing
    ret = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # ..

    return ret


async def broadcast():
    """Broadcast task"""
    global CLIENT, cap
    print('BROADCAST STARTED!')
    while True:
        ret=capture_and_process()
        if ret is None:
            pass
        else:
            ret = Image.fromarray(ret.astype("uint8"))
            rawBytes = BytesIO()
            ret.save(rawBytes, "JPEG")
            ret_base64 = base64.b64encode(rawBytes.getvalue())
            msg=json.dumps({'type': 'image', 'buffer': ret_base64.decode('utf-8') })
        await asyncio.gather(
            *[ws.send(msg) for ws in CLIENTS],
            return_exceptions=True,
        )

async def handler(websocket, path):
    global is_now_broadcasting, CLIENTS, broadcast_thread, broadcast_thread_lock

    CLIENTS.add(websocket)
    try:
        # if no client connected yet, start broadcast task
        if len(CLIENTS)==1:
            broadcast_task=asyncio.create_task(broadcast())
        async for msg in websocket:
                pass
    except websockets.ConnectionClosedError:
        pass
    finally:
        CLIENTS.remove(websocket)
        # if no client currently connected, cancel the broadcast task
        if len(CLIENTS)==0:
            print('Stop broadcasting..')
            broadcast_task.cancel()

start_server = websockets.serve(handler, "127.0.0.1", 1998)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()