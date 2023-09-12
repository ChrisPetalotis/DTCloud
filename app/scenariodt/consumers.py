from channels.generic.websocket import AsyncWebsocketConsumer
from django.template import Context, Template
import json


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()  # accept and build a websocket connection between client and server
        await self.channel_layer.group_add("notifications", self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("notifications", self.channel_name)

    # This is run when a notification is sent from the server to the connected clients
    async def send_notification(self, event):
        message = event["message"]
        template = Template('<div class"notification_text"><p>{{message}}</p></div>')
        context = Context({"message": message})
        rendered_notiication = template.render(context)
        await self.send(
            text_data=json.dumps(
                {"type": "notification", "message": rendered_notiication}
            )
        )
