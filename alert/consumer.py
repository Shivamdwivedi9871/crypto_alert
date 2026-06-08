import json
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):

        # self.user = self.scope['user']

        # if self.user.is_authenticated:
        self.group_name = f"user_shivansh"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        print(f"Websocket Connected: 'shivansh' is now online")
        # else:
        #     await self.close()

    async def disconnect(self, close_code):
        if self.user.is_authenticated:

            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

            print(f"Websocket Disconnected for '{self.user.username}'")

    async def send_notification(self, event):
        message = event['message']

        await self.send(text_data=json.dumps({
            'type': 'crypto_alert',
            'message': message
        }))
