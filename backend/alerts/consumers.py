import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger('alerts.websocket')


class AlertConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for streaming real-time alerts, scan progress,
    and remediation updates directly to connected dashboard clients.
    """
    GROUP_NAME = 'alerts_broadcast'

    async def connect(self):
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()
        logger.info("WebSocket client connected to alerts broadcast: %s", self.channel_name)
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to SecureCoda real-time event stream',
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)
        logger.info("WebSocket client disconnected: %s", self.channel_name)

    async def receive(self, text_data):
        """Handle incoming messages (e.g. ping/heartbeat from client)."""
        try:
            data = json.loads(text_data)
            if data.get('type') == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
        except Exception:
            pass

    async def alert_event(self, event):
        """Receive broadcast alert event and send to WebSocket client."""
        await self.send(text_data=json.dumps(event['payload']))
