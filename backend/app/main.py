from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import random
import time
from app.config import settings
from app.core.navidrome import navidrome
from app.services.lyrics import parse_lrc, find_lrc, read_text

app = FastAPI(title=settings.app_name)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def song_out(s: dict) -> dict:
    sid = s.get("id") or ""
    cover_id = s.get("coverArt") or sid
    return {
        "id": sid,
        "title": s.get("title") or "未知歌曲",
        "artist": s.get("artist") or "未知艺术家",
        "album": s.get("album") or "未知专辑",
        "duration": float(s.get("duration") or 0),
        "file_format": s.get("suffix") or "",
        "genre": s.get("genre") or "",
        "year": s.get("year") or None,
        "cover_id": cover_id,
        "cover_url": f"/api/v1/music/songs/{sid}/cover",
        "stream_url": f"/api/v1/music/songs/{sid}/stream",
    }

@app.get("/api/health")
async def health():
    return {"status": "ok", "system": settings.app_name, "source": "Navidrome"}

@app.get("/api/v1/music/songs")
async def list_songs(page: int = Query(1, ge=1), page_size: int = Query(60, ge=1, le=200), search: str = ""):
    offset = (page - 1) * page_size
    sr = await navidrome.call("search3.view", query=search or "", songCount=page_size, songOffset=offset)
    songs = sr.get("searchResult3", {}).get("song", [])
    items = [song_out(s) for s in songs]
    total = len(items)
    if not search:
        total = 0; off = 0
        while True:
            batch = await navidrome.call("search3.view", query="", songCount=500, songOffset=off)
            arr = batch.get("searchResult3", {}).get("song", [])
            if not arr: break
            total += len(arr); off += 500
    return {"items": items, "total": total, "page": page, "page_size": page_size}

@app.get("/api/v1/music/songs/{song_id}")
async def get_song(song_id: str):
    sr = await navidrome.call("getSong.view", id=song_id)
    return song_out(sr.get("song", {}))

async def proxy_navidrome(endpoint: str, request: Request, media_type: str | None = None, **params):
    import httpx
    headers = {}
    if request.headers.get("range"):
        headers["Range"] = request.headers["range"]
    url = navidrome.url(endpoint, **params)
    client = httpx.AsyncClient(timeout=None, follow_redirects=True)
    try:
        resp = await client.send(client.build_request("GET", url, headers=headers), stream=True)
    except Exception as e:
        await client.aclose()
        raise HTTPException(status_code=502, detail=str(e))
    out_headers = {}
    for h in ("content-length", "content-range", "accept-ranges", "cache-control"):
        if h in resp.headers:
            out_headers[h] = resp.headers[h]
    async def body():
        try:
            async for chunk in resp.aiter_bytes():
                yield chunk
        finally:
            await resp.aclose()
            await client.aclose()
    return StreamingResponse(body(), status_code=resp.status_code, media_type=media_type or resp.headers.get("content-type"), headers=out_headers)

@app.get("/api/v1/music/songs/{song_id}/stream")
async def stream(song_id: str, request: Request):
    return await proxy_navidrome("stream.view", request, id=song_id)

@app.get("/api/v1/music/songs/{song_id}/cover")
async def cover(song_id: str, request: Request, size: int = 360):
    try:
        sr = await navidrome.call("getSong.view", id=song_id)
        song = sr.get("song", {})
        cover_id = song.get("coverArt") or song_id
    except Exception:
        cover_id = song_id
    return await proxy_navidrome("getCoverArt.view", request, media_type="image/jpeg", id=cover_id, size=size)

@app.get("/api/v1/music/songs/{song_id}/lyrics")
async def lyrics(song_id: str):
    song = {}
    try:
        sr = await navidrome.call("getSong.view", id=song_id)
        song = sr.get("song", {})
    except Exception:
        song = {"id": song_id}
    local = find_lrc(song)
    if local:
        lines = parse_lrc(read_text(local))
        return {"has_lrc": bool(lines), "source": "local", "lines": lines, "meta": {"path": str(local), "title": song.get("title"), "artist": song.get("artist")}}
    try:
        sr = await navidrome.call("getLyrics.view", id=song_id)
        value = (sr.get("lyrics", {}) or {}).get("value") or ""
        lines = parse_lrc(value)
        return {"has_lrc": bool(lines), "source": "navidrome", "lines": lines, "meta": {"title": song.get("title"), "artist": song.get("artist")}}
    except Exception:
        return {"has_lrc": False, "source": "none", "lines": [], "meta": {"title": song.get("title"), "artist": song.get("artist")}}

@app.get("/api/v1/music/stats")
async def stats():
    artists_data = await navidrome.call("getArtists.view")
    artists = sum(len(idx.get("artist", [])) for idx in artists_data.get("artists", {}).get("index", []))
    albums = 0; off = 0
    while True:
        sr = await navidrome.call("getAlbumList2.view", type="alphabeticalByName", size=500, offset=off)
        arr = sr.get("albumList2", {}).get("album", [])
        if not arr: break
        albums += len(arr); off += 500
    songs = 0; off = 0
    while True:
        sr = await navidrome.call("search3.view", query="", songCount=500, songOffset=off)
        arr = sr.get("searchResult3", {}).get("song", [])
        if not arr: break
        songs += len(arr); off += 500
    return {"total_songs": songs, "total_artists": artists, "total_albums": albums}

@app.get("/api/v1/music/enjoy")
async def enjoy_recommendations(
    count: int = Query(36, ge=1, le=100),
    seed: str = "",
    exclude: str = "",
    genre: str = "",
):
    # Generate a lightweight daily/enjoy queue from the local Navidrome library.
    rnd = random.Random(seed or f"{int(time.time() // 3600)}")
    excluded = {x for x in exclude.split(",") if x}
    pool: list[dict] = []
    seen: set[str] = set()

    async def add_songs(arr):
        for raw in arr or []:
            sid = raw.get("id") or ""
            if not sid or sid in seen or sid in excluded:
                continue
            duration = float(raw.get("duration") or 0)
            if duration and duration < 45:
                continue
            seen.add(sid)
            pool.append(raw)

    if genre:
        for _ in range(3):
            offset = rnd.randint(0, 900)
            sr = await navidrome.call("getSongsByGenre.view", genre=genre, count=min(100, max(count * 2, 30)), offset=offset)
            await add_songs(sr.get("songsByGenre", {}).get("song", []))
            if len(pool) >= count:
                break

    list_types = ["frequent", "recent", "starred", "random", "random", "random"]
    rnd.shuffle(list_types)
    for typ in list_types:
        if len(pool) >= count * 3:
            break
        try:
            sr = await navidrome.call("getAlbumList2.view", type=typ, size=24, offset=rnd.randint(0, 80) if typ != "random" else 0)
            albums = sr.get("albumList2", {}).get("album", [])
            rnd.shuffle(albums)
            for album in albums[:12]:
                if len(pool) >= count * 3:
                    break
                try:
                    detail = await navidrome.call("getAlbum.view", id=album.get("id"))
                    songs = detail.get("album", {}).get("song", [])
                    if songs:
                        await add_songs([rnd.choice(songs)])
                except Exception:
                    continue
        except Exception:
            continue

    attempts = 0
    while len(pool) < count and attempts < 10:
        attempts += 1
        offset = rnd.randint(0, 2200)
        sr = await navidrome.call("search3.view", query="", songCount=min(100, max(count * 2, 50)), songOffset=offset)
        await add_songs(sr.get("searchResult3", {}).get("song", []))

    scored = []
    for raw in pool:
        dur = float(raw.get("duration") or 0)
        score = rnd.random()
        if raw.get("coverArt"):
            score += 0.18
        if raw.get("artist") and raw.get("album"):
            score += 0.14
        if 120 <= dur <= 360:
            score += 0.2
        if raw.get("genre"):
            score += 0.08
        scored.append((score, raw))
    scored.sort(key=lambda x: x[0], reverse=True)
    picked = [song_out(x[1]) for x in scored[:count]]
    return {"items": picked, "total": len(picked), "seed": seed or "hourly", "mode": "genre" if genre else "daily_mix", "message": "随享模式已为你挑选一组更适合连续播放的歌曲"}

@app.get("/api/v1/music/categories")
async def categories():
    sr = await navidrome.call("getGenres.view")
    genres = sr.get("genres", {}).get("genre", [])
    out = [{"name": g.get("value", ""), "song_count": g.get("songCount", 0), "album_count": g.get("albumCount", 0)} for g in genres if g.get("songCount", 0) > 0]
    return sorted(out, key=lambda x: x["song_count"], reverse=True)

@app.get("/api/v1/music/categories/{name}/songs")
async def category_songs(name: str, page: int = Query(1, ge=1), page_size: int = Query(60, ge=1, le=200)):
    offset = (page - 1) * page_size
    sr = await navidrome.call("getSongsByGenre.view", genre=name, count=page_size, offset=offset)
    songs = sr.get("songsByGenre", {}).get("song", [])
    return {"items": [song_out(s) for s in songs], "total": len(songs), "page": page, "page_size": page_size}
