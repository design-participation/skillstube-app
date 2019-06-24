from aiohttp import web
import aiohttp_jinja2

from backend import history
from util import routes, login_required, get_user
import util

import secrets

@routes.get('/history/{category}')
@login_required
@aiohttp_jinja2.template('history.html')
async def personal(request):
    user = await get_user(request)
    category = request.match_info['category']
    history_items = await history.list(user['_id'], type=category)
    # convert history to local timezone before rendering
    for item in history_items:
        item['date'] = util.as_log_timezone(item['date']).strftime("%Y-%m-%d %H:%M:%S")
    return {'history': history_items, 'category': category}


@routes.get('/history')
@login_required
@aiohttp_jinja2.template('history.html')
async def personal(request):
    user = await get_user(request)
    history_items = await history.list(user['_id'])
    # convert history to local timezone before rendering
    for item in history_items:
        item['date'] = util.as_log_timezone(item['date']).strftime("%Y-%m-%d %H:%M:%S")
    return {'history': history_items, 'category': 'all'}

@routes.post('/action')
@login_required
async def personal(request):
    user = await get_user(request)
    data = await request.json()
    action_type = data.get('type', '')
    action_parameters = data.get('parameters', None)

    allowed_types = ['query-suggestion', 'voice-input', 'typed-text']
    if action_type in allowed_types and action_parameters is not None:
        await history.add(user['_id'], action_type, action_parameters)
        return web.json_response('recorded')
    print('unknown action:', data)
    raise web.HTTPBadRequest(reason='unknown action')

