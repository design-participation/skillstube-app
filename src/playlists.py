from aiohttp import web
import aiohttp_jinja2
from bson.objectid import ObjectId

from util import routes, get_user, login_required
from backend import playlists, videos
from navigation import Breadcrumb

@routes.get('/playlists/{folder_id}')
@aiohttp_jinja2.template('playlist.html')
@login_required
async def show_playlists(request):
    user = await get_user(request)
    folder_id = ObjectId(request.match_info['folder_id'])
    folder = await playlists.get(folder_id)
    if folder is not None and folder['user_id'] == user['_id']:
        folder['videos'] = await videos.get([item['video_id'] for item in await playlists.list(user['_id'], folder['_id'])])
        folder['count'] = await playlists.count(folder['_id'])
        return {'folder': folder, 'breadcrumb': [Breadcrumb.HOME(), Breadcrumb.PLAYLISTS(), Breadcrumb.PLAYLIST(folder['name'], folder['_id'])]}
    raise web.HTTPBadRequest()

@routes.get('/playlists')
@aiohttp_jinja2.template('playlists.html')
@login_required
async def show_playlists(request):
    user = await get_user(request)
    folders = await playlists.list_folders(user['_id'])
    for folder in folders:
        folder['videos'] = await videos.get([item['video_id'] for item in await playlists.list(user['_id'], folder['_id'], limit=4)])
        folder['count'] = await playlists.count(folder['_id'])
    return {'folders': folders, 'breadcrumb': [Breadcrumb.HOME(), Breadcrumb.PLAYLISTS()]}

# GET /set_playlist/{video_id} => ui for adding a video to a playlist
@routes.get('/set_playlist/{video_id}')
@aiohttp_jinja2.template('set_playlist.html')
@login_required
async def set_playlist_ui(request):
    user = await get_user(request)
    video_id = request.match_info['video_id']
    folders = await playlists.list_folders(user['_id'])
    video = await videos.get(video_id)
    return {'folders': folders, 'video': video, 'breadcrumb': [Breadcrumb.HOME(), Breadcrumb.PLAYLISTS()]}

# POST /set_playlist/{video_id} => actually add the video to a playlist
@routes.post('/set_playlist/{video_id}')
@aiohttp_jinja2.template('set_playlist.html')
@login_required
async def set_playlist(request):
    user = await get_user(request)
    video_id = request.match_info['video_id']
    data = await request.post()
    folder_id = None
    if 'folder' in data and data['folder'].strip() != '':
        folder_id = ObjectId(data['folder'])
        if not await playlists.get(folder_id):
            folder_id = None
    if 'new_name' in data and data['new_name'].strip() != '':
        folder_id = await playlists.add_folder(user['_id'], data['new_name'])
    if folder_id is not None:
        await playlists.add(user['_id'], folder_id, video_id)
        raise web.HTTPFound('/watch/' + video_id)
    raise web.HTTPBadRequest()

