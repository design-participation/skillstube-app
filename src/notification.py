from aiohttp import web
from aiohttp_session import get_session
import aiohttp_jinja2
from bson.objectid import ObjectId

from util import routes, login_required, get_user
from backend import notifications

#get /dismiss/{notification_id} => dismiss notification (json result)
@routes.get('/dismiss/{notification_id}')
@login_required
async def dismiss_notification(request):
    user = await get_user(request)
    notification_id = request.match_info['notification_id']
    await notifications.dismiss(user['_id'], ObjectId(notification_id))
    return web.json_response('ok')

@routes.get('/notifications')
@login_required
@aiohttp_jinja2.template('notifications.html')
async def show_notifications(request):
    user = await get_user(request)
    notification_items = await notifications.list(user['_id'], return_all=True, populate=True)
    return {'notifications': notification_items}
