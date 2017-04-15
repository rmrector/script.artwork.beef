from lib.providers.themoviedb import TheMovieDBSearch

searcher = None

def init(session):
    global searcher
    searcher = TheMovieDBSearch(session)

def search(query, mediatype):
    return searcher.search(query, mediatype)

def for_id(query, mediatype):
    result = search(query, mediatype)
    if result:
        for rs in result:
            if rs['label'] == query:
                return rs['id']
        return result[0]['id']
