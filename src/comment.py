from aiohttp import web
from datetime import datetime
import aiohttp_jinja2

from util import routes, login_required, get_user

from backend import comments

#POST /comment/{videoId} (text) => add root comment to video
@routes.post('/comment/{videoId}')
@login_required
async def post_comment(request):
    user = await get_user(request)
    video_id = request.match_info['videoId']
    data = await request.post()
    if 'text' in data:
        comment_id = await comments.add(user['_id'], video_id, data['text'])
        raise web.HTTPFound('/watch/' + video_id + '#' + str(comment_id))
    else:
        raise web.HTTPBadRequest()

@routes.get('/comments')
@login_required
@aiohttp_jinja2.template('comments.html')
async def show_comments(request):
    user = await get_user(request)
    comment_items = await comments.list(user['_id'], populate=True)
    return {'comments': comment_items, 'show_video': True}

