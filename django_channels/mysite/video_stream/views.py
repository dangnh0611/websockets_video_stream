# chat/views.py
from django.shortcuts import render

def room(request, room_name):
    return render(request, 'video_stream/room.html', {
        'room_name': room_name
    })