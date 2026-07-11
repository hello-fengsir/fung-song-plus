<template>
  <div class="app" :class="{ 'cinema-open': cinemaOpen }">
    <div class="shell">
      <header class="top">
        <div class="brand">
          <div class="logo user-logo">
            <img src="/brand-logo.png" alt="Logo" />
          </div>
          <div>
            <h1>Fung-song Plus</h1>
            <div class="sub">飞牛 NAS · Navidrome · 轻量音乐门户</div>
          </div>
        </div>
        <div class="search">
          <input v-model="keyword" @keyup.enter="reload" placeholder="搜索歌曲 / 歌手 / 专辑" />
          <button class="btn" @click="reload">搜索</button>
          <button class="btn enjoy-btn" :class="enjoyMode ? 'active' : ''" @click="startEnjoyMode">✨ {{ enjoyMode ? '随享中' : '随享模式' }}</button>
          <button class="btn ghost" @click="clearSearch">全部</button>
        </div>
      </header>

      <section class="stats">
        <div class="stat"><b>{{ stats.total_songs ?? '...' }}</b><span>歌曲</span></div>
        <div class="stat"><b>{{ stats.total_artists ?? '...' }}</b><span>艺术家</span></div>
        <div class="stat"><b>{{ stats.total_albums ?? '...' }}</b><span>专辑</span></div>
      </section>

      <section class="enjoy-card" :class="enjoyMode ? 'on' : ''">
        <div>
          <div class="eyebrow-small">Daily Enjoy · 本地曲库智能随播</div>
          <h2>不用挑，点一下就开始听</h2>
          <p>{{ enjoyStatus }}</p>
        </div>
        <div class="enjoy-actions">
          <button class="btn enjoy-main" @click="startEnjoyMode">{{ enjoyMode ? '换一批好歌' : '开启随享模式' }}</button>
          <button v-if="enjoyMode" class="btn ghost" @click="stopEnjoyMode">退出随享</button>
        </div>
      </section>

      <main class="grid">
        <section class="panel">
          <div class="cats">
            <button class="chip" :class="!activeCat ? 'active' : ''" @click="activeCat = ''; page = 1; loadSongs()">全部</button>
            <button v-for="c in categories.slice(0, 18)" :key="c.name" class="chip" :class="activeCat === c.name ? 'active' : ''" @click="selectCat(c.name)">{{ c.name }} · {{ c.song_count }}</button>
          </div>

          <div class="table-wrap">
            <div v-if="loading" class="empty">加载中...</div>
            <div v-else-if="!songs.length" class="empty">暂无歌曲</div>
            <div v-for="s in songs" :key="s.id" class="song" :class="player.current?.id === s.id ? 'active' : ''" @click="play(s)">
              <img class="cover" :src="s.cover_url" @error="hideBroken" @dblclick.stop="playAndOpen(s)" title="双击进入大屏" />
              <div>
                <div class="title">{{ s.title }}</div>
                <div class="muted">{{ s.file_format?.toUpperCase() || 'AUDIO' }}</div>
              </div>
              <div class="artist muted">{{ s.artist }}</div>
              <div class="album muted">{{ s.album }}</div>
              <div class="muted">{{ fmt(s.duration) }}</div>
            </div>
          </div>

          <div class="cats pager">
            <button class="btn ghost" :disabled="page <= 1" @click="page--; loadSongs()">上一页</button>
            <span class="muted" style="padding:10px">第 {{ page }} 页 / {{ total }} 首</span>
            <button class="btn ghost" :disabled="songs.length < pageSize" @click="page++; loadSongs()">下一页</button>
          </div>
        </section>

        <aside class="panel side">
          <template v-if="player.current">
            <button class="poster-btn" @click="openCinema" title="进入大屏播放模式">
              <img class="now-cover" :src="player.current.cover_url" />
              <span class="poster-mask">进入大屏</span>
            </button>
            <h2>{{ player.current.title }}</h2>
            <div class="muted">{{ player.current.artist }} · {{ player.current.album }}</div>
            <div class="lyrics compact-lyrics" ref="compactLyricsRef">
              <div v-if="!player.lyrics.length" class="muted">暂无歌词</div>
              <div v-for="(l, i) in player.lyrics" :key="i" class="line" :class="i === player.lyricIndex ? 'on' : ''" @click="player.seek(l.time)">{{ l.text }}</div>
            </div>
            <div v-if="enjoyMode" class="enjoy-side">
              <b>✨ 随享模式</b>
              <span>已准备 {{ enjoyQueue.length }} 首，结束后自动续播</span>
            </div>
            <div class="muted">歌词来源：{{ player.lyricSource || '-' }}</div>
          </template>
          <div v-else class="empty">选择一首歌开始播放</div>
        </aside>
      </main>
    </div>

    <footer v-if="player.current" class="player">
      <img class="mini-cover" :src="player.current.cover_url" @click="openCinema" title="进入大屏" />
      <div class="mini-meta">
        <div class="title one-line">{{ player.current.title }}</div>
        <div class="muted one-line">{{ player.current.artist }}</div>
      </div>
      <button class="btn ghost" @click="prevSong">⏮</button>
      <button class="btn" @click="player.toggle">{{ player.playing ? '⏸' : '▶' }}</button>
      <button class="btn ghost" @click="nextSong">⏭</button>
      <button v-if="enjoyMode" class="btn ghost" title="这首不喜欢，随享下一首" @click="skipEnjoySong">不喜欢</button>
      <button class="btn ghost" @click="player.cycleMode">{{ player.modeIcon }}</button>
      <div class="progress">
        <span class="muted">{{ fmt(player.currentTime) }}</span>
        <input type="range" :max="player.duration || 1" :value="player.currentTime" @input="player.seek(Number(($event.target as HTMLInputElement).value))" />
        <span class="muted">{{ fmt(player.duration) }}</span>
      </div>
      <input class="vol" type="range" min="0" max="1" step="0.01" :value="player.volume" @input="player.setVolume(Number(($event.target as HTMLInputElement).value))" />
    </footer>

    <Teleport to="body">
      <section v-if="cinemaOpen && player.current" class="cinema" @keydown.esc="closeCinema" tabindex="-1" ref="cinemaRef">
        <div class="cinema-bg" :style="bgStyle"></div>
        <div class="cinema-vignette"></div>
        <div class="aurora a1"></div>
        <div class="aurora a2"></div>
        <div class="life-glow lg1"></div>
        <div class="life-glow lg2"></div>
        <div class="bokeh-field" aria-hidden="true">
          <span v-for="dot in 18" :key="dot" :style="bokehStyle(dot)"></span>
        </div>
        <div class="warm-haze"></div>
        <div class="grain"></div>

        <header class="cinema-head">
          <div>
            <div class="eyebrow">Fung-song Plus · Immersive Mode</div>
            <h1>{{ player.current.title }}</h1>
            <p>{{ player.current.artist }} <span v-if="player.current.album">· {{ player.current.album }}</span></p>
          </div>
          <div class="head-actions">
            <button class="glass-btn" @click="requestFullScreen">⛶ 全屏</button>
            <button class="glass-btn" @click="closeCinema">退出</button>
          </div>
        </header>

        <main class="cinema-stage">
          <section class="karaoke" ref="cinemaLyricsRef">
            <div v-if="!player.lyrics.length" class="no-lyric">
              <b>{{ player.current.title }}</b>
              <span>暂无歌词 · 享受此刻旋律</span>
            </div>
            <button v-for="l in visibleLyrics" :key="`${l.realIndex}-${l.time}`" class="karaoke-line" :class="lyricClass(l.realIndex)" @click="player.seek(l.time)">
              {{ l.text || '♪' }}
            </button>
          </section>

          <aside class="spectrum-disc-card">
            <div class="spectrum-disc" :class="{ playing: player.playing }">
              <div class="spectrum-ring" aria-hidden="true">
                <i
                  v-for="bar in spectrumBars"
                  :key="bar"
                  :style="spectrumStyle(bar)"
                ></i>
              </div>
              <div class="cover-disc" :class="{ spin: player.playing }">
                <img :src="player.current.cover_url" />
                <span class="disc-shine"></span>
              </div>
              <div class="disc-glow"></div>
            </div>
            <div class="disc-caption">
              <strong>{{ player.current.title }}</strong>
              <span>{{ player.current.file_format?.toUpperCase() || 'AUDIO' }} · {{ fmt(player.duration || player.current.duration) }}</span>
            </div>
          </aside>
        </main>

        <footer class="cinema-controls">
          <div class="cinema-progress">
            <span>{{ fmt(player.currentTime) }}</span>
            <input type="range" :max="player.duration || 1" :value="player.currentTime" @input="player.seek(Number(($event.target as HTMLInputElement).value))" />
            <span>{{ fmt(player.duration) }}</span>
          </div>
          <div class="control-row">
            <button class="round ghost" @click="prevSong">⏮</button>
            <button class="round play" @click="player.toggle">{{ player.playing ? '⏸' : '▶' }}</button>
            <button class="round ghost" @click="nextSong">⏭</button>
            <button class="round ghost" @click="player.cycleMode">{{ player.modeIcon }}</button>
            <input class="cinema-vol" type="range" min="0" max="1" step="0.01" :value="player.volume" @input="player.setVolume(Number(($event.target as HTMLInputElement).value))" />
          </div>
        </footer>
      </section>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { getCategories, getCategorySongs, getEnjoySongs, getLyrics, getSongs, getStats, type Song } from './api/music'
import { usePlayerStore } from './stores/player'

const player = usePlayerStore()
const songs = ref<Song[]>([])
const stats = ref<any>({})
const categories = ref<any[]>([])
const keyword = ref('')
const activeCat = ref('')
const page = ref(1)
const pageSize = 60
const total = ref(0)
const loading = ref(false)
const enjoyMode = ref(false)
const enjoyLoading = ref(false)
const enjoyQueue = ref<Song[]>([])
const enjoyHistory = ref<string[]>([])
const enjoyStatus = ref('随享模式会从你的本地曲库里挑选适合连续播放的歌曲，自动一首接一首。')
const cinemaOpen = ref(false)
const cinemaRef = ref<HTMLElement | null>(null)
const compactLyricsRef = ref<HTMLElement | null>(null)
const spectrumBars = Array.from({ length: 96 }, (_, i) => i)

const bgStyle = computed(() => ({ backgroundImage: `url(${player.current?.cover_url || ''})` }))
const visibleLyrics = computed(() => {
  const lines = player.lyrics || []
  if (!lines.length) return []
  const center = Math.max(player.lyricIndex, 0)
  const start = Math.max(0, center - 5)
  const end = Math.min(lines.length, center + 7)
  return lines.slice(start, end).map((line, offset) => ({ ...line, realIndex: start + offset }))
})

function fmt(sec: number) {
  if (!sec || isNaN(sec)) return '0:00'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}
function hideBroken(e: Event) { (e.target as HTMLImageElement).style.visibility = 'hidden' }
async function loadSongs() {
  loading.value = true
  try {
    const data = activeCat.value ? await getCategorySongs(activeCat.value, { page: page.value, page_size: pageSize }) : await getSongs({ page: page.value, page_size: pageSize, search: keyword.value })
    songs.value = data.items || []
    total.value = data.total || songs.value.length
  } finally { loading.value = false }
}
async function reload() { activeCat.value = ''; page.value = 1; await loadSongs() }
async function clearSearch() { keyword.value = ''; activeCat.value = ''; page.value = 1; await loadSongs() }
async function selectCat(name: string) { activeCat.value = name; keyword.value = ''; page.value = 1; await loadSongs() }
let lyricRequestSeq = 0
let lyricLoadingFor = ''
let lyricLoadedFor = ''
async function loadLyricFor(song?: Song | null, force = false) {
  if (!song) return
  const requestSongId = song.id
  if (!force && lyricLoadedFor === requestSongId && player.lyrics.length) return
  if (!force && lyricLoadingFor === requestSongId) return
  lyricLoadingFor = requestSongId
  const seq = ++lyricRequestSeq
  try {
    const data = await getLyrics(requestSongId)
    if (seq !== lyricRequestSeq || player.current?.id !== requestSongId) return
    player.lyrics = data.lines || []
    player.lyricSource = data.source || ''
    player.lyricIndex = -1
    lyricLoadedFor = requestSongId
  } catch (err) {
    if (seq !== lyricRequestSeq || player.current?.id !== requestSongId) return
    player.lyrics = []
    player.lyricSource = ''
    setTimeout(() => {
      if (player.current?.id === requestSongId && !player.lyrics.length) loadLyricFor(player.current, true)
    }, 1200)
  } finally {
    if (lyricLoadingFor === requestSongId) lyricLoadingFor = ''
  }
}
async function refillEnjoyQueue(force = false) {
  if (enjoyLoading.value) return
  if (!force && enjoyQueue.value.length > 8) return
  enjoyLoading.value = true
  try {
    const seed = `${new Date().toISOString().slice(0, 10)}-${Math.floor(Date.now() / 1800000)}`
    const data = await getEnjoySongs({ count: 36, seed, exclude: enjoyHistory.value.slice(-120).join(','), genre: activeCat.value || undefined })
    const incoming: Song[] = data.items || []
    const known = new Set([...enjoyQueue.value.map(s => s.id), ...enjoyHistory.value.slice(-80)])
    enjoyQueue.value.push(...incoming.filter(s => !known.has(s.id)))
    enjoyStatus.value = enjoyQueue.value.length ? `已为你准备 ${enjoyQueue.value.length} 首随享歌曲，自动续播中。` : '暂时没有拿到推荐歌曲，可以稍后再试。'
  } finally {
    enjoyLoading.value = false
  }
}
async function playEnjoyNext() {
  if (!enjoyQueue.value.length) await refillEnjoyQueue(true)
  const next = enjoyQueue.value.shift()
  if (!next) return
  enjoyMode.value = true
  player.setMode('enjoy')
  player.play(next, [next, ...enjoyQueue.value])
  enjoyHistory.value.push(next.id)
  lyricLoadedFor = ''
  await loadLyricFor(next, true)
  if (enjoyQueue.value.length < 8) refillEnjoyQueue()
}
async function startEnjoyMode() {
  await refillEnjoyQueue(true)
  await playEnjoyNext()
}
function stopEnjoyMode() {
  enjoyMode.value = false
  enjoyStatus.value = '已退出随享模式，你可以继续手动选择歌曲。'
  if (player.mode === 'enjoy') player.setMode('list')
}
async function skipEnjoySong() {
  if (player.current) enjoyHistory.value.push(player.current.id)
  await playEnjoyNext()
}
async function play(s: Song) {
  enjoyMode.value = false
  if (player.mode === 'enjoy') player.setMode('list')
  player.play(s, songs.value)
  lyricLoadedFor = ''
  await loadLyricFor(s, true)
}
async function playAndOpen(s: Song) {
  await play(s)
  openCinema()
}
function openCinema() {
  if (!player.current) return
  cinemaOpen.value = true
  nextTick(() => cinemaRef.value?.focus())
  if (!player.lyrics.length) loadLyricFor(player.current)
}
function closeCinema() { cinemaOpen.value = false }
async function nextSong() { if (enjoyMode.value) { await playEnjoyNext(); return } player.next(); await nextTick(); await loadLyricFor(player.current) }
async function prevSong() { player.prev(); await nextTick(); await loadLyricFor(player.current) }
async function requestFullScreen() {
  const el = cinemaRef.value
  if (el && !document.fullscreenElement) await el.requestFullscreen?.().catch(() => {})
}
function lyricClass(i: number) {
  const d = Math.abs(i - player.lyricIndex)
  return { active: i === player.lyricIndex, near: d === 1, far: d >= 4 }
}
function spectrumStyle(i: number) {
  const phase = (i % 16) / 16
  const pulse = 0.72 + Math.abs(Math.sin(i * 0.63)) * 0.72
  const dot = 3 + (i % 5 === 0 ? 2 : 0)
  const halo = player.playing ? pulse : 0.78
  return {
    transform: `rotate(${i * 3.75}deg) translateY(-176px) scaleY(${halo})`,
    width: `${dot}px`,
    height: `${player.playing ? 14 + Math.round(14 * pulse) : 8 + (i % 3)}px`,
    animationDelay: `${-phase * 1.4}s`,
    opacity: player.playing ? 0.74 : 0.34
  }
}
function bokehStyle(i: number) {
  const x = 8 + ((i * 37) % 84)
  const y = 18 + ((i * 29) % 66)
  const size = 5 + ((i * 11) % 24)
  const delay = -((i * 17) % 36) / 10
  const alpha = 0.08 + ((i * 7) % 13) / 100
  return { left: `${x}%`, top: `${y}%`, width: `${size}px`, height: `${size}px`, animationDelay: `${delay}s`, opacity: alpha }
}
function handleKey(e: KeyboardEvent) {
  if (!cinemaOpen.value) return
  if (e.code === 'Space') { e.preventDefault(); player.toggle() }
  if (e.code === 'ArrowRight') player.seek(Math.min((player.duration || 0), player.currentTime + 5))
  if (e.code === 'ArrowLeft') player.seek(Math.max(0, player.currentTime - 5))
  if (e.code === 'Escape') closeCinema()
}
watch(() => player.currentTime, (t) => {
  let found = -1
  for (let i = player.lyrics.length - 1; i >= 0; i--) {
    if (player.lyrics[i].time <= t + 0.15) { found = i; break }
  }
  player.lyricIndex = found
})
watch(() => player.lyricIndex, async () => {
  await nextTick()
  const box = compactLyricsRef.value
  const active = box?.querySelector('.line.on') as HTMLElement | null
  if (!box || !active) return
  // 只滚动歌词容器自身，避免 scrollIntoView 把整页/主页列表一起带到底部。
  const target = active.offsetTop - box.clientHeight / 2 + active.clientHeight / 2
  box.scrollTo({ top: Math.max(0, target), behavior: 'smooth' })
})
watch(() => player.current?.id, async (id, oldId) => {
  if (!id || id === oldId) return
  await nextTick()
  loadLyricFor(player.current)
})
watch(cinemaOpen, async (open) => {
  if (!open || !player.current || player.lyrics.length) return
  await nextTick()
  loadLyricFor(player.current)
})
onMounted(async () => {
  window.addEventListener('keydown', handleKey)
  player.onEnded(async () => { if (enjoyMode.value || player.mode === 'enjoy') await playEnjoyNext(); else player.next(); await nextTick(); await loadLyricFor(player.current) })
  await Promise.all([loadSongs(), getStats().then(d => stats.value = d), getCategories().then(d => categories.value = d)])
})
onUnmounted(() => { window.removeEventListener('keydown', handleKey); player.onEnded(null) })
</script>
