import json
from channels.generic.websocket import AsyncWebsocketConsumer

class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.room_group_name = f'call_{self.user.id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        call_type = data.get('type')

        if call_type == 'call_offer':
            receiver_id = data['receiver_id']
            offer = data['offer']
            
            await self.channel_layer.group_send(
                f'call_{receiver_id}',
                {
                    'type': 'call_offer',
                    'offer': offer,
                    'caller_id': self.user.id,
                    'caller_name': self.user.email
                }
            )
        
        elif call_type == 'call_answer':
            caller_id = data['caller_id']
            answer = data['answer']
            
            await self.channel_layer.group_send(
                f'call_{caller_id}',
                {
                    'type': 'call_answer',
                    'answer': answer
                }
            )
        
        elif call_type == 'ice_candidate':
            target_id = data['target_id']
            candidate = data['candidate']
            
            await self.channel_layer.group_send(
                f'call_{target_id}',
                {
                    'type': 'ice_candidate',
                    'candidate': candidate
                }
            )

    async def call_offer(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call_offer',
            'offer': event['offer'],
            'caller_id': event['caller_id'],
            'caller_name': event['caller_name']
        }))

    async def call_answer(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call_answer',
            'answer': event['answer']
        }))

    async def ice_candidate(self, event):
        await self.send(text_data=json.dumps({
            'type': 'ice_candidate',
            'candidate': event['candidate']
        }))