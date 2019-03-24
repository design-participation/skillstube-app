from aiohttp import web
import aiohttp_jinja2

from backend import history
from util import routes, login_required, get_user

#GET /history => show history data
@routes.get('/history')
@login_required
@aiohttp_jinja2.template('history.html')
async def personal(request):
    user = await get_user(request)
    history_items = await history.list(user['_id'])
    #await history.add(user['_id'], 'show-history')
    return {'history': history_items, 'category': 'all'}

#GET /history => show history data for single category
@routes.get('/history/{category}')
@login_required
@aiohttp_jinja2.template('history.html')
async def personal(request):
    user = await get_user(request)
    category = request.match_info.get('category')
    history_items = await history.list(user['_id'], category)
    #await history.add(user['_id'], 'show-history-category', {'category': category})
    return {'history': history_items, 'category': category}

