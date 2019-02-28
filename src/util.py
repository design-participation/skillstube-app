import sys

from jinja2 import Environment, FileSystemLoader
templates = Environment(loader=FileSystemLoader('templates/'))

def from_template(name, params = {}):
    template = templates.get_template(name)
    response = web.Response(body=template.render(**params).encode('utf8'))
    response.headers['content-type'] = 'text/html'
    return response

from aiohttp import web
from aiohttp_session import get_session
from bson.objectid import ObjectId

routes = web.RouteTableDef()
from backend import users, notifications

async def get_user(request):
    session = await get_session(request)
    if 'user_id' in session:
        return await users.get(ObjectId(session['user_id']))
    return None

async def add_globals(request):
    print(request.url)
    values = {}
    user = await get_user(request)
    if user is not None:
        user['notification_count'] = await notifications.count(user['_id'])
        values['user'] = user
    if '-debug' in sys.argv:
        values['debug'] = True
    return values

def login_required(fn):
    async def wrapped(request, *args, **kwargs):
        if await get_user(request) is None:
            return web.HTTPFound('/login')
        return await fn(request, *args, **kwargs)

    return wrapped

