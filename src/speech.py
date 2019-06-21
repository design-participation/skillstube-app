# Full doc at https://azure.microsoft.com/en-us/services/cognitive-services/speech-to-text/
# Examples at https://github.com/Azure-Samples/cognitive-services-speech-sdk/tree/master/samples/js/browser

from aiohttp import web
import aiohttp
import aiohttp_jinja2

from util import routes
import secrets

# This function is called every 9 minutes by clients to renew access token to microsoft cognitive services
# for speech recognition. 
@routes.get('/stt/microsoft')
async def tts_token_microsoft(request):
    url = 'https://%s.api.cognitive.microsoft.com/sts/v1.0/issueToken' % secrets.MS_COGNITIVE_SERVICES_REGION
    headers = {'Ocp-Apim-Subscription-Key': secrets.MS_COGNITIVE_SERVICES_KEY}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={}, headers=headers) as response:
            if response.status == 200:
                data = await response.text()
                return web.Response(body=data, headers={'Access-Control-Allow-Origin': secrets.SERVER_NAME})
    raise web.HTTPForbidden()

