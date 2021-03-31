# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
import numpy as np
import cv2
from PIL import Image
import base64
from io import BytesIO

PREFERED_FPS=30
FRAME_DELAY=1/PREFERED_FPS
global NCLIENTS, broadcast_task, cap
NCLIENTS=0
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

async def broadcast_task(channel_layer, room_group_name):
    print('*********Start broadcasting..')
    while True:
        await asyncio.sleep(FRAME_DELAY)
        frame=capture_and_process()
        if frame is None:
            pass
        else:
            frame = Image.fromarray(frame.astype("uint8"))
            rawBytes = BytesIO()
            frame.save(rawBytes, "JPEG")
            frame_base64 = base64.b64encode(rawBytes.getvalue())
            await channel_layer.group_send(
                room_group_name,
                {
                    'type': 'frame_message',
                    'message': frame_base64.decode('utf-8')
                }
            )


class VideoStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        global NCLIENTS, broadcast_task
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'room_%s' % self.room_name
        NCLIENTS+=1

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        # if no client connected yet, start broadcast task
        if NCLIENTS==1:
            broadcast_task=asyncio.create_task(broadcast_task(self.channel_layer, self.room_group_name))

    async def disconnect(self, close_code):
        global NCLIENTS, broadcast_task
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        NCLIENTS-=1
        if NCLIENTS==0:
            print('*********Stop broadcasting..')
            broadcast_task.cancel()
        
    # Receive message from WebSocket
    async def receive(self, text_data):
        pass

    # Receive message from room group
    async def frame_message(self, event):
        # Send message to WebSocket
        msg=event['message']
        print(msg)
        await self.send(text_data=json.dumps({
            'type': 'frame',
            'data': msg
        }))