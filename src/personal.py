from aiohttp import web
import aiohttp_jinja2

from backend import users, history, comments, friends, notifications
from util import routes, login_required, get_user

#GET /personal => show personal information
@routes.get('/personal')
@login_required
@aiohttp_jinja2.template('personal.html')
async def personal(request):
    user = await get_user(request)
    notification_items = await notifications.list(user['_id'], return_all=False, populate=True)
    return {'notifications': notification_items}

