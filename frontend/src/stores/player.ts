import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { Song } from '../api/music'

export interface LyricLine { time:number; text:string; zh?:string }
export const usePlayerStore = defineStore('player', () => {
  const current = ref<Song|null>(null)
  const list = ref<Song[]>([])
  const index = ref(-1)
  const playing = ref(false)
  const currentTime = ref(0)
  const duration = ref(0)
  const volume = ref(0.8)
  const lyrics = ref<LyricLine[]>([])
  const lyricSource = ref('')
  const lyricIndex = ref(-1)
  const mode = ref<'list'|'repeat'|'shuffle'|'enjoy'>('list')
  let audio: HTMLAudioElement|null = null
  let endedHandler: (() => void) | null = null
  function init(){ if(audio) return; audio=new Audio(); audio.volume=volume.value; audio.addEventListener('timeupdate',()=>{currentTime.value=audio!.currentTime}); audio.addEventListener('loadedmetadata',()=>{duration.value=audio!.duration||0}); audio.addEventListener('play',()=>playing.value=true); audio.addEventListener('pause',()=>playing.value=false); audio.addEventListener('ended',()=>{ if(mode.value==='repeat'){ audio!.currentTime=0; audio!.play() } else if(endedHandler){ endedHandler() } else next() }) }
  function play(song:Song, playlist?:Song[]){ init(); if(playlist){list.value=playlist; index.value=playlist.findIndex(s=>s.id===song.id)} current.value=song; lyrics.value=[]; lyricIndex.value=-1; audio!.src=song.stream_url; audio!.load(); audio!.play().catch(()=>{}) }
  function toggle(){ if(!audio) return; playing.value ? audio.pause() : audio.play().catch(()=>{}) }
  function seek(t:number){ if(audio) audio.currentTime=t }
  function setVolume(v:number){ volume.value=v; if(audio) audio.volume=v }
  function next(){ if(!list.value.length) return; let ni = mode.value==='shuffle' ? Math.floor(Math.random()*list.value.length) : (index.value+1)%list.value.length; index.value=ni; play(list.value[ni]) }
  function prev(){ if(!list.value.length) return; let ni = index.value<=0 ? list.value.length-1 : index.value-1; index.value=ni; play(list.value[ni]) }
  function cycleMode(){ mode.value = mode.value==='list' ? 'repeat' : mode.value==='repeat' ? 'shuffle' : mode.value==='shuffle' ? 'enjoy' : 'list' }
  function setMode(v:'list'|'repeat'|'shuffle'|'enjoy'){ mode.value=v }
  function onEnded(fn:(()=>void)|null){ endedHandler=fn }
  const modeIcon = computed(()=> mode.value==='list'?'🔁':mode.value==='repeat'?'🔂':mode.value==='shuffle'?'🔀':'✨')
  return {current,list,index,playing,currentTime,duration,volume,lyrics,lyricSource,lyricIndex,mode,modeIcon,play,toggle,seek,setVolume,next,prev,cycleMode,setMode,onEnded}
})
