import re
from pathlib import Path
from app.config import settings

TIME_RE = re.compile(r"\[(\d{1,2}):(\d{1,2}(?:\.\d{1,3})?)\]")
META_RE = re.compile(r"^\[[a-zA-Z]+:.*\]$")

def parse_lrc(text: str) -> list[dict]:
    if not text:
        return []
    lines: list[dict] = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        raw = raw.strip("\ufeff \t")
        if not raw or META_RE.match(raw):
            continue
        matches = list(TIME_RE.finditer(raw))
        if not matches:
            continue
        lyric = TIME_RE.sub("", raw).strip()
        if not lyric:
            continue
        for m in matches:
            t = int(m.group(1)) * 60 + float(m.group(2))
            lines.append({"time": round(t, 3), "text": lyric, "zh": ""})
    lines.sort(key=lambda x: x["time"])
    return lines

def read_text(path: Path) -> str:
    data = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "gb18030", "gbk", "big5"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", errors="ignore")

def music_roots() -> list[Path]:
    return [Path(x.strip()) for x in settings.music_roots.split(",") if x.strip()]

def candidate_music_paths(song: dict) -> list[Path]:
    values = []
    for key in ("path", "file", "title"):
        v = song.get(key)
        if v:
            values.append(str(v))
    title = str(song.get("title") or "").strip()
    artist = str(song.get("artist") or "").strip()
    if title:
        values.extend([title, f"{artist}-{title}" if artist else title, f"{artist} - {title}" if artist else title])
    out: list[Path] = []
    for v in values:
        p = Path(v)
        if p.is_absolute():
            out.append(p)
        for root in music_roots():
            out.append(root / v)
            out.append(root / Path(v).name)
    seen=set(); uniq=[]
    for p in out:
        s=str(p)
        if s not in seen:
            seen.add(s); uniq.append(p)
    return uniq

def find_lrc(song: dict) -> Path | None:
    names = []
    title = str(song.get("title") or "").strip()
    artist = str(song.get("artist") or "").strip()
    if title:
        names += [title, f"{artist}-{title}" if artist else title, f"{artist} - {title}" if artist else title]
    for mp in candidate_music_paths(song):
        base = mp.with_suffix("")
        for ext in (".lrc", ".LRC", ".txt"):
            cand = base.with_suffix(ext)
            if cand.is_file():
                return cand
        parent = mp.parent
        if parent.exists():
            for name in names:
                for ext in (".lrc", ".LRC", ".txt"):
                    cand = parent / f"{name}{ext}"
                    if cand.is_file():
                        return cand
    for root in music_roots():
        if not root.exists():
            continue
        for name in names[:3]:
            for ext in (".lrc", ".LRC", ".txt"):
                direct = root / f"{name}{ext}"
                if direct.is_file():
                    return direct
    return None
