
class Breadcrumb(dict):
    def __init__(self, text, link, icon=''):
        self['text'] = text
        self['link'] = link
        self['icon'] = icon

    @classmethod
    def HOME(cls):
        return Breadcrumb('Home', '/', 'home')
    @classmethod
    def SEARCH(cls, prompt, prompt_text, query):
        return Breadcrumb(prompt_text + ' ' + query, '/search?q=' + query + '&prompt=' + str(prompt), 'search')
    @classmethod
    def WATCH(cls, video_id, title):
        return Breadcrumb(title, '/watch/' + video_id, 'film')

    @classmethod
    def FRIENDS(cls):
        return Breadcrumb('Friends', '/friends', 'user-friends')

    @classmethod
    def PLAYLISTS(cls):
        return Breadcrumb('Playlists', '/playlists', 'star')

    @classmethod
    def PLAYLIST(cls, name, folder_id):
        return Breadcrumb(name, '/playlists/' + str(folder_id), 'star')

    @classmethod
    def SHARED(cls):
        return Breadcrumb('Shared with me', '/shared', 'share-alt')

    @classmethod
    def NOTIFICATIONS(cls):
        return Breadcrumb('Notifications', '/notifications', 'bell')

