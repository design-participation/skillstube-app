import re

from aiohttp import web
from aiohttp_session import get_session
import aiohttp_jinja2

from util import routes, get_user, login_required
from youtube import Youtube
from backend import users, comments, history, videos, playlists
import secrets

youtube = Youtube()
prompts = {'1': 'How to', '2': 'What is', '3': 'Examples of', '4': ''}
def validate_prompt(prompt):
    return prompt if prompt in prompts else '1'

@routes.get('/')
@aiohttp_jinja2.template('index.html')
async def index(request):
    session = await get_session(request)
    for variable in ['query', 'prompt', 'channel_only']:
        if variable in session:
            del session[variable]
    return {'nav': 'home', 'channel_name': secrets.YOUTUBE_CHANNEL_NAME}

@routes.get('/search')
@aiohttp_jinja2.template('search.html')
async def search(request):
    session = await get_session(request)

    query = request.query.get('q', session['query'] if 'query' in session else '')
    prompt = validate_prompt(request.query.get('prompt', session['prompt'] if 'prompt' in session else ''))
    # checkboxes are only specified in query if they are ticked
    if 'q' in request.query:
        channel_only = request.query.get('channel_only', 'off')
    else:
        channel_only = session['channel_only'] if 'channel_only' in session else 'off'

    results = []
    # handle copy-pasted youtube URL => show video instead
    youtube_url_pattern = re.compile(r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/ ]{11})', re.I)
    found = youtube_url_pattern.search(query)
    if found:
        video_id = found.group(1)
        async for item in youtube.video([video_id]):
            video = {'video_id': video_id, 'thumbnail': item['snippet']['thumbnails']['medium']['url'], 'title': item['snippet']['title']}
            await videos.add(**video)
            results.append(video)
    elif query.strip() != '':
        final_query = '"%s" %s' % (prompts[prompt], query)
        if channel_only == 'on':
            args = {
                'videoSyndicated': 'true',
                'videoEmbeddable': 'true',
                'channelId': secrets.YOUTUBE_CHANNEL_ID,
            }
        else:
            args = {
                    # videoCategory: 26 = how to and style, 27 = education
                'videoCategoryId': 26,
                'relevanceLanguage': secrets.YOUTUBE_LANGUAGE,
                'videoSyndicated': 'true',
                'videoEmbeddable': 'true',
                'videoDuration': 'short',
                'regionCode': secrets.YOUTUBE_REGION_CODE,
                'safeSearch': 'strict',
            }
                    # unset if prompt is (no start)
        if prompts[prompt] == '' and 'videoCategoryId' in args:
            del args['videoCategoryId']
        async for item in youtube.search(final_query, 24, **args):
            video = {'video_id': item['id']['videoId'], 'thumbnail': item['snippet']['thumbnails']['medium']['url'], 'title': item['snippet']['title']}
            results.append(video)
            await videos.add(**video)

    user = await get_user(request)
    if user is not None:
        if query != '':
            await history.add(user['_id'], 'search', {'query': query, 'prompt': prompt, 'channel_only': channel_only, 'results': ','.join([item['video_id'] for item in results])})
        else:
            await history.add(user['_id'], 'show-search-page')

    session['query'] = query
    session['prompt'] = prompt
    session['channel_only'] = channel_only
    
    return {'results': results, 'query': query, 'prompt': prompt, 'channel_only': channel_only, 'nav': 'search', 'channel_name': secrets.YOUTUBE_CHANNEL_NAME}

# TODO: deprecated
async def get_video_info(videoId):
    def work():
        info = pafy.new(videoId)
        return info.getbestvideo().url, info.getbestaudio().url, info.title

    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, work)

# TODO: deprecated
async def get_related(videoId):
    results = []
    async for item in youtube.related(videoId, 25):
        results.append({'videoId': item['id']['videoId'], 'thumbnail': item['snippet']['thumbnails']['medium']['url'], 'title': item['snippet']['title']})
    return results

@routes.get('/watch/{video_id}')
@aiohttp_jinja2.template('watch.html')
async def watch(request):
    user = await get_user(request)
    video_id = request.match_info['video_id']
    #task1 = asyncio.create_task(get_related(video_id))
    #task2 = asyncio.create_task(get_video_info(video_id))
    #results, (video_url, audio_url, title) = await asyncio.gather(task1, task2)
    comment_items = []
    folder = None
    video = await videos.get(video_id)
    if video is None:
        async for item in youtube.video([video_id]):
            video = {'video_id': video_id, 'thumbnail': item['snippet']['thumbnails']['medium']['url'], 'title': item['snippet']['title']}
            await videos.add(**video)
        if video is None:
            raise web.HTTPBadRequest()
    if user is not None:
        comment_items = await comments.list(user['_id'], video_id, populate=True)
        await history.add(user['_id'], 'show-video', {'video_id': video['_id'], 'youtube_id': video['video_id'], 'link': 'https://youtu.be/' + video['video_id'], 'title': video['title'], 'thumbnail': video['thumbnail']})
        folder = await playlists.get_for_video(user['_id'], video_id)
    return { 'video': video, 'comments': comment_items, 'folder': folder, 'nav': 'search'}

#TODO: deprecated (maybe use categories to host recent videos)
@routes.get('/recent')
@login_required
@aiohttp_jinja2.template('recent.html')
async def show_recent(request):
    user = await get_user(request)
    history_items = await history.list(user['_id'], 'video')
    recent_videos = []
    seen = set()
    for item in history_items:
        videoId = item['data']
        if videoId not in seen:
            recent_videos.append({'videoId': videoId, 'title': '', 'thumbnail': 'http://i3.ytimg.com/vi/%s/mqdefault.jpg' % videoId})
            seen.add(videoId)
    await history.add(user['_id'], 'recent-videos')
    return {'results': recent_videos, 'nav': 'playlists'}

@routes.get('/suggest')
async def suggest(request):
    query = request.query.get('q', '')
    prompt = request.query.get('prompt', '1')
    if prompt not in prompts:
        prompt = 1
    found = await youtube.suggest(prompts[prompt] + ' ' + query)
    suggestions = [re.sub('^' + prompts[prompt].lower(), '', item.strip()).strip() for item in found[1]]
    user = await get_user(request)
    if user is not None:
        await history.add(user['_id'], 'query-suggestion', {'query': query, 'prompt': prompt, 'suggestions': suggestions})
    return web.json_response(suggestions)

