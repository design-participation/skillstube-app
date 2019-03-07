import sys
import asyncio

from jinja2 import Environment, FileSystemLoader
templates = Environment(loader=FileSystemLoader('templates/'))

def from_template(name, params = {}):
    template = templates.get_template(name)
    response = web.Response(body=template.render(**params).encode('utf8'))
    response.headers['content-type'] = 'text/html'
    return response

from aiohttp import web
from aiohttp_session import get_session
from aiohttp import ClientSession
from bson.objectid import ObjectId

routes = web.RouteTableDef()
from backend import users, notifications

async def get_user(request):
    session = await get_session(request)
    if 'user_id' in session:
        return await users.get(ObjectId(session['user_id']))
    return None

async def add_globals(request):
    values = {}
    user = await get_user(request)
    if user is not None:
        user['notification_count'] = await notifications.count(user['_id'])
        values['user'] = user
    session = await get_session(request)
    # get global state
    for name in ['query', 'prompt', 'playlist']:
        if name in session:
            values[name] = session[name]
    if '-debug' in sys.argv:
        values['debug'] = True
        #values['debug_links'] = [item.path for item in routes if type(item) == web.RouteDef and item.method == 'GET']
        values['debug_links'] = ['/logout', '/debug:users']
    return values

def login_required(fn):
    async def wrapped(request, *args, **kwargs):
        if await get_user(request) is None:
            return web.HTTPFound('/login')
        return await fn(request, *args, **kwargs)

    return wrapped

class Downloader:
    def __init__(self):
        self.session = ClientSession()

    async def close(self):
        await self.session.close()

    async def get(self, urls, callback, **kwargs):
        async def get_one(url):
            async with self.session.get(url, **kwargs) as response:
                await callback(response)
        tasks = [get_one(url) for url in urls]
        await asyncio.gather(*tasks)

