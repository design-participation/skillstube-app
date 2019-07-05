from aiohttp import web
from datetime import datetime
import aiohttp_jinja2

from util import routes, login_required, get_user, to_objectid, redirect

from backend import comments, friends, videos, shares, history

# TODO: deprecated
@routes.get('/comment/{video_id}') 
@login_required
@aiohttp_jinja2.template('comment.html')
async def write_comment(request):
    user = await get_user(request)
    video_id = request.match_info['video_id']
    video = await videos.get(video_id)
    friend_items = await friends.list(user['_id'], populate=True)
    await history.add(user['_id'], 'write-comment', {'video_id': video['_id'], 'youtube_id': video_id})
    return {'video': video, 'friends': friend_items}

@routes.post('/comment/{video_id}')
@login_required
async def post_comment(request):
    user = await get_user(request)
    video_id = request.match_info['video_id']
    data = await request.post()
    num_shared = len([key for key in data if key == 'friend'])
    if num_shared == 0:
        await redirect(request, '/watch/' + video_id, error='Share at least with one friend')
    if 'text' in data:
        comment_id = await comments.add(user['_id'], video_id, data['text'])
        for key, other_id in data.items():
            if key == 'friend':
                #print('adding', other_id)
                await shares.add(video_id, comment_id, {'thumbnail': 'https://i.ytimg.com/vi/%s/mqdefault.jpg' % video_id, 'text': data['text']}, user['_id'], to_objectid(other_id))
        video = await videos.get(video_id)
        await history.add(user['_id'], 'save-comment', {'video_id': video['_id'], 'youtube_id': video_id, 'comment': data['text'], 'shared-with': [v for k, v in data.items() if key == 'friend']})
        raise web.HTTPFound('/watch/' + video_id + '#' + str(comment_id))
    else:
        raise web.HTTPBadRequest()

