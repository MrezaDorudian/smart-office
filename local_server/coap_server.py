import asyncio
import random
import utils

import aiocoap.resource as resource
import aiocoap
from utils import authenticate
import requests
import jwt

jwt_secret_key = 'super-secret'


class CoAPServer:
    class CoAPInfo(resource.Resource):
        async def render_post(self, request):
            payload = request.payload.decode('utf-8')
            try:
                user_id, password, room_id = payload.split(':')
                auth = authenticate(user_id, password)
                if auth:
                    return_value = utils.send_get_request_to_central_server(user_id, '4679', jwt_secret_key, '1')
                    return aiocoap.Message(content_format=0, payload=f'{return_value}'.encode('utf8'))
                else:
                    return aiocoap.Message(content_format=0, payload=f'{auth}'.encode('utf8'))
            except ValueError:
                user_id, password, room_id, _ = payload.split(':')
                utils.send_get_request_to_central_server(user_id, '4679', jwt_secret_key, '2')



async def setup_coap_server():
    root = resource.Site()
    root.add_resource(['info'], CoAPServer.CoAPInfo())
    await aiocoap.Context.create_server_context(bind=('localhost', 5555), site=root)
    await asyncio.get_running_loop().create_future()


if __name__ == '__main__':
    asyncio.run(setup_coap_server())
