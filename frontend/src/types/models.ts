export type TaskStatus = 'pending' | 'downloading' | 'merging' | 'completed' | 'failed' | 'stopped'

export interface TaskModel {
  id: string
  hash_id: string
  name: string
  m3u8_url: string
  status: TaskStatus
  total_segments: number
  downloaded_segments: number
  failed_segments: number
  total_size: number
  total_duration: number
  speed: number
  progress: number
  eta: number | null
  created_at: string
  updated_at: string
  download_dir: string
  concurrency: number
  speed_limit: number | null
  chunk_size: number | null
  proxy: string | null
  headers: Record<string, string> | null
  merge_video: boolean
  delete_cache: boolean
}

export interface GlobalConfigModel {
  id: string
  task_concurrency: number
  ffmpeg_path: string | null
  download_dir: string
  concurrency: number
  speed_limit: number | null
  chunk_size: number | null
  proxy: string | null
  headers: Record<string, string> | null
  merge_video: boolean
  delete_cache: boolean
}
