export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T | null
}

export interface ApiPaginationResponse<T = unknown>
  extends Omit<ApiResponse<T[]>, 'data'> {
  total: number
  total_pages: number
  data: T[]
}
