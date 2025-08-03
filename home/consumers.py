# yourapp/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get user_id from URL
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f"user_{self.user_id}"

        # Verify user exists
        user = await self.get_user(self.user_id)
        if not user:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        print(f"WebSocket connected for user {self.user_id}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"WebSocket disconnected for user {self.user_id}")

    async def send_notification(self, event):
        """Send notification to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'message': event['message']
        }))

    @database_sync_to_async
    def get_user(self, user_id):
        """Get user by ID."""
        # Import here to avoid AppRegistryNotReady error
        from .models import CustomUser
        try:
            return CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return None
