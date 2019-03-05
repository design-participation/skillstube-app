import sys
import asyncio
import uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

from aiohttp import web

from aiohttp_session import get_session, setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage

import aiohttp_jinja2
import jinja2

import user
import search
import personal
import friend
import share
import comment
import notification
import favorites

if '-debug' in sys.argv[1:]:
    import debug

import secrets
from util import routes, get_user, add_globals

async def init():
    app = web.Application()

    setup(app, EncryptedCookieStorage(secrets.SERVER_COOKIE_KEY))
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates/'), context_processors=[add_globals])

    routes.static('/static', 'static', append_version=True)
    routes.static('/', 'static/favicon', append_version=True)
    app.add_routes(routes) 
    return app

app = asyncio.get_event_loop().run_until_complete(init())

ssl_context = None
if secrets.USE_SSL:
    import ssl
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(secrets.SSL_CRT, secrets.SSL_KEY)

web.run_app(app, ssl_context=ssl_context, host=secrets.HOST, port=secrets.PORT)

