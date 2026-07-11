import axios from 'axios'
export const api = axios.create({ baseURL: '/api/v1/music', timeout: 30000 })
export interface Song { id:string; title:string; artist:string; album:string; duration:number; file_format:string; genre?:string; cover_url:string; stream_url:string }
export async function getSongs(params:any){ return (await api.get('/songs',{params})).data }
export async function getStats(){ return (await api.get('/stats')).data }
export async function getCategories(){ return (await api.get('/categories')).data }
export async function getCategorySongs(name:string, params:any){ return (await api.get('/categories/'+encodeURIComponent(name)+'/songs',{params})).data }
export async function getLyrics(id:string){ return (await api.get('/songs/'+encodeURIComponent(id)+'/lyrics')).data }

export async function getEnjoySongs(params:any = {}){ return (await api.get('/enjoy',{params})).data }
