import sys
import os
import asyncio

from aiohttp import web
from aiohttp_session import get_session
from aiohttp import ClientSession
from bson.objectid import ObjectId

from jinja2 import Environment, FileSystemLoader
import aiohttp_jinja2

from backend import users, notifications

templates = Environment(loader=FileSystemLoader('templates/'))
def from_template(name, params = {}):
    template = templates.get_template(name)
    response = web.Response(body=template.render(**params).encode('utf8'))
    response.headers['content-type'] = 'text/html'
    return response

# Global iohttp routes
routes = web.RouteTableDef()

# Get user from session
async def get_user(request):
    session = await get_session(request)
    if 'user_id' in session:
        return await users.get(to_objectid(session['user_id']))
    return None

# Add user with notification count and other globals to dictionary passed to jinja2 template
async def add_globals(request):
    values = {}
    user = await get_user(request)
    if user is not None:
        user['notification_count'] = await notifications.count(user['_id'])
        values['user'] = user
    if '-debug' in sys.argv:
        values['debug'] = True
    return values

def to_objectid(text):
    try:
        return ObjectId(text)
    except:
        return None

# Decorator to enforce that the user is logged for a given page
def login_required(fn):
    async def wrapped(request, *args, **kwargs):
        if await get_user(request) is None:
            return web.HTTPFound('/login')
        return await fn(request, *args, **kwargs)

    return wrapped

# aiohttp middleware to render nice error pages
@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
        if response.status < 400:
            return response
        message = response.message
    except web.HTTPException as ex:
        if ex.status < 400:
            raise
        message = ex.reason
    values = await add_globals(request)
    values.update({'error_message': message})
    return from_template('error.html', values)

# Downloads a bunch of urls in parallel, calls a function to process the result of each
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

# Runs a command and gets the return code, stdout and stderr 
async def run_command(cmd):
    proc = await asyncio.create_subprocess_shell( cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout.decode(), stderr.decode()

# Remove a file if it exists
def remove_file(filename):
    if os.path.exists(filename):
        os.unlink(filename)
        return True
    return False

