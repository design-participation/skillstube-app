from aiohttp_session import get_session
import aiohttp_jinja2

from util import routes, get_user, login_required
from youtube import Youtube
from backend import users, comments, history
import secrets

youtube = Youtube()

@routes.get('/')
@aiohttp_jinja2.template('index.html')
async def index(request):
    query = request.query.get('q', '')
    return {'query': query}

@routes.get('/search')
@aiohttp_jinja2.template('search.html')
async def search(request):
    query = request.query.get('q', '')
    results = []
    prompt = request.query.get('prompt', '1')
    prompts = {'1': 'How to', '2': 'What is', '3': 'Show me', '4': ''}
    if prompt not in prompts:
        prompt = '1'
    if query.strip() != '':
        final_query = '"%s" %s' % (prompts[prompt], query)
        if request.query.get('channel_only'):
            async for item in youtube.search(final_query, 24,
                        videoSyndicated='true',
                        videoEmbeddable='true',
                        channelId=secrets.YOUTUBE_CHANNEL,
                    ):
                results.append({'videoId': item['id']['videoId'], 'thumbnail': item['snippet']['thumbnails']['high']['url'], 'title': item['snippet']['title']})
        else:
            async for item in youtube.search(final_query, 24,
                        videoCategoryId=26, # 26 = how to and style, 27 = education
                        relevanceLanguage='en',
                        videoSyndicated='true',
                        videoEmbeddable='true',
                        videoDuration='short',
                        regionCode='AU',
                        safeSearch='strict',
                    ):
                results.append({'videoId': item['id']['videoId'], 'thumbnail': item['snippet']['thumbnails']['high']['url'], 'title': item['snippet']['title']})
    user = await get_user(request)
    if user is not None:
        await history.add(user['_id'], 'query', query)
    return {'query': query, 'results': results, 'channel_only': request.query.get('channel_only'), 'prompt': prompt}

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
        results.append({'videoId': item['id']['videoId'], 'thumbnail': item['snippet']['thumbnails']['high']['url'], 'title': item['snippet']['title']})
    return results

@routes.get('/watch/{videoId}')
@aiohttp_jinja2.template('watch.html')
async def video(request):
    user = await get_user(request)
    videoId = request.match_info['videoId']
    query = request.query.get('q', '')
    #task1 = asyncio.create_task(get_related(videoId))
    #task2 = asyncio.create_task(get_video_info(videoId))
    #results, (video_url, audio_url, title) = await asyncio.gather(task1, task2)
    comment_items = []
    if user is not None:
        comment_items = await comments.list(user['_id'], videoId, populate=True)
        # TODO: add user info
        #for comment_item in comment_items:
        #    for i, share_uid in enumerate(comment_item['shared_with']):
        #        comment_item['shared_with'][i] = await user.get(share_uid)
        await history.add(user['_id'], 'video', videoId)
    return { 'videoId': videoId, 'query': query, 'comments': comment_items }

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
            recent_videos.append({'videoId': videoId, 'title': '', 'thumbnail': 'http://i3.ytimg.com/vi/%s/hqdefault.jpg' % videoId})
            seen.add(videoId)
    return {'results': recent_videos}

