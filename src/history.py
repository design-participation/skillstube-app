from aiohttp import web
import aiohttp_jinja2

from backend import history
from util import routes, login_required, get_user

@routes.get('/history/{category}')
@login_required
@aiohttp_jinja2.template('history.html')
async def personal(request):
    user = await get_user(request)
    category = request.match_info['category']
    history_items = await history.list(user['_id'], type=category)
    return {'history': history_items, 'category': category}


#GET /history => show history data
@routes.get('/history')
@login_required
@aiohttp_jinja2.template('history.html')
async def personal(request):
    user = await get_user(request)
    history_items = await history.list(user['_id'])
    #await history.add(user['_id'], 'show-history')
    return {'history': history_items, 'category': 'all'}

#POST /action => log action to history
@routes.post('/action')
@login_required
async def personal(request):
    user = await get_user(request)
    data = await request.json()
    await history.add(user['_id'], 'action', data)
    return web.json_response('recorded')

