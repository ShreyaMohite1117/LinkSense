import axios from 'axios'

const TOKEN_KEY = 'ls-access'
const REFRESH_KEY = 'ls-refresh'

export const tokens = {
  get access() {
    return localStorage.getItem(TOKEN_KEY)
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY)
  },
  save({ access_token, refresh_token }) {
    if (access_token) localStorage.setItem(TOKEN_KEY, access_token)
    if (refresh_token) localStorage.setItem(REFRESH_KEY, refresh_token)
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_KEY)
  },
}

const api = axios.create({
  baseURL: `${import.meta.env.VITE_API_URL || ''}/api`,
  timeout: 20000,
})

api.interceptors.request.use((config) => {
  const token = tokens.access
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// When the access token expires, quietly swap it using the refresh token and retry once.
let refreshing = null

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    const status = error.response?.status
    const isAuthCall = original?.url?.startsWith('/auth/login') || original?.url?.startsWith('/auth/refresh')

    if (status === 401 && !original._retried && !isAuthCall && tokens.refresh) {
      original._retried = true
      try {
        refreshing =
          refreshing ||
          axios.post(`${api.defaults.baseURL}/auth/refresh`, { refresh_token: tokens.refresh }).finally(() => {
            refreshing = null
          })
        const { data } = await refreshing
        tokens.save(data)
        original.headers.Authorization = `Bearer ${data.access_token}`
        return api(original)
      } catch {
        tokens.clear()
        window.dispatchEvent(new Event('ls-logout'))
      }
    }
    return Promise.reject(error)
  },
)

export function errorMessage(err, fallback = 'Something went wrong') {
  if (err?.response?.data?.error) return err.response.data.error
  if (err?.code === 'ERR_NETWORK') return "Can't reach the server. Is the backend running?"
  return fallback
}

export async function downloadFile(path, filename) {
  const res = await api.get(path, { responseType: 'blob' })
  const url = URL.createObjectURL(res.data)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export default api
