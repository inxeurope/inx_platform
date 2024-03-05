import asyncio
import random

from django.http import StreamingHttpResponse
from django.shortcuts import render


async def sse_stream(request):
    """
    Sends server-sent events to the client.
    """
    async def event_stream():
        messages = ["m1", "m2", "m3", "m4", "m5"]
        i = 0
        while True:
            yield f'data: {random.choice(messages)} {i}\n\n'
            i += 1
            await asyncio.sleep(1)

    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')


def index(request):
    return render(request, 'app_pages/sse.html')