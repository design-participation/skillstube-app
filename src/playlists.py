from aiohttp import web
import aiohttp_jinja2

from util import routes, get_user, login_required, to_objectid, redirect
from backend import playlists, videos, history

@routes.get('/playlists/{folder_id}')
@aiohttp_jinja2.template('playlist.html')
@login_required
async def show_playlists(request):
    user = await get_user(request)
    folder_id = to_objectid(request.match_info['folder_id'])
    folder = await playlists.get(folder_id)
    if folder is not None and folder['user_id'] == user['_id']:
        await history.add(user['_id'], 'show-playlist', {'folder_id': folder_id, 'name': folder['name']})
        folder['videos'] = await videos.get([item['video_id'] for item in await playlists.list(user['_id'], folder['_id'])])
        folder['count'] = await playlists.count(folder['_id'])
        return {'folder': folder, 'nav': 'playlists'}
    raise web.HTTPBadRequest()

@routes.get('/add-playlist')
@aiohttp_jinja2.template('add_playlist.html')
@login_required
async def add_playlist(request):
    user = await get_user(request)
    await history.add(user['_id'], 'add-playlist-form')
    return {'nav': 'playlists'}

@routes.post('/add-playlist')
@login_required
async def add_playlist(request):
    user = await get_user(request)
    data = await request.post()
    if 'name' in data:
        folder_id = await playlists.add_folder(user['_id'], data['name'])
        if folder_id is not None:
            await history.add(user['_id'], 'add-playlist', {'folder_id': folder_id, 'name': data['name']})
        await redirect(request, '/playlists', info='Playlist "%s" created' % data['name'])
    await redirect(request, '/playlists', error='Invalid playlist name')

@routes.post('/rename-playlist')
@login_required
async def add_playlist(request):
    user = await get_user(request)
    data = await request.post()
    if 'name' in data and 'folder' in data:
        folder_id = to_objectid(data['folder'])
        if folder_id is not None:
            await playlists.rename_folder(folder_id, data['name'])
            await history.add(user['_id'], 'rename-folder', {'folder_id': folder_id, 'name': data['name']})
            await redirect(request, '/playlists/%s' % folder_id, info='Playlist renamed to "%s"' % data['name'])
    await redirect(request, '/playlists', error='Cannot rename playlist')

@routes.get('/playlists')
@aiohttp_jinja2.template('playlists.html')
@login_required
async def show_playlists(request):
    user = await get_user(request)
    folders = await playlists.list_folders(user['_id'])
    for folder in folders:
        folder['videos'] = await videos.get([item['video_id'] for item in await playlists.list(user['_id'], folder['_id'], limit=4)])
        folder['count'] = await playlists.count(folder['_id'])
    await history.add(user['_id'], 'show-playlists')
    return {'folders': folders, 'nav': 'playlists'}

@routes.get('/set_playlist/{video_id}')
@aiohttp_jinja2.template('set_playlist.html')
@login_required
async def set_playlist_ui(request):
    user = await get_user(request)
    video_id = request.match_info['video_id']
    folders = await playlists.list_folders(user['_id'])
    video = await videos.get(video_id)
    await history.add(user['_id'], 'show-playlist-selector', {'video_id': video['_id'], 'youtube_id': video_id})
    return {'folders': folders, 'video': video, 'nav': 'playlists'}

@routes.post('/set_playlist/{video_id}')
@aiohttp_jinja2.template('set_playlist.html')
@login_required
async def set_playlist(request):
    user = await get_user(request)
    video_id = request.match_info['video_id']
    data = await request.post()
    folder_id = None
    video = await videos.get(video_id)
    if 'folder' in data and data['folder'].strip() != '':
        folder_id = to_objectid(data['folder'])
        if not await playlists.get(folder_id):
            folder_id = None
    if 'new_name' in data and data['new_name'].strip() != '':
        folder_id = await playlists.add_folder(user['_id'], data['new_name'])
        await history.add(user['_id'], 'add-playlist', {'folder_id': folder_id, 'name': data['new_name']})
    if folder_id is not None:
        await playlists.add(user['_id'], folder_id, video_id)
        folder = await playlists.get(folder_id)
        await history.add(user['_id'], 'set-playlist', {'video_id': video['_id'], 'youtube_id': video_id, 'folder_id': folder_id, 'name': folder['name']})
        raise web.HTTPFound('/watch/' + video_id)
    raise web.HTTPBadRequest()

