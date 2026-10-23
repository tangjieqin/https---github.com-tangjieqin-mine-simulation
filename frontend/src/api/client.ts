/**
 * HTTP 请求封装。
 *
 * 为什么统一走这里：
 * 1. baseURL 只有一处（/api/v1），由 vite 代理转发到 8000 端口，不用写死域名
 * 2. 错误处理只有一处：非 2xx 统一抛 ApiError，页面不用各自判断
 *
 * 注意：阶段 1 不加 axios，原生 fetch 足够（就两个接口）。
 */

const BASE_URL = '/api/v1'

export class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

/** FastAPI 的错误体：detail 可能是字符串，也可能是 422 时的数组 */
function extractDetail(body: unknown): string {
  if (typeof body === 'string') return body
  if (body && typeof body === 'object' && 'detail' in body) {
    const d = (body as { detail: unknown }).detail
    if (typeof d === 'string') return d
    if (Array.isArray(d)) {
      // 422 校验错误形如 [{loc:[...],msg:"...",type:"..."}]
      return d
        .map((item) => {
          const it = item as { loc?: unknown[]; msg?: string }
          return `${Array.isArray(it.loc) ? it.loc.join('.') : ''} ${it.msg ?? ''}`.trim()
        })
        .join('; ')
    }
  }
  return '请求失败'
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  })

  if (!resp.ok) {
    let body: unknown = null
    try {
      body = await resp.json()
    } catch {
      body = null
    }
    throw new ApiError(resp.status, extractDetail(body))
  }

  return (await resp.json()) as T
}
