import axios from 'axios'

const normalizeBaseUrl = (url: string) => {
  return url.replace(/\/+$/, '').replace(/\/api$/i, '')
}

// Ensure we use 127.0.0.1 to avoid localhost resolution issues
const envUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'
const BASE_URL = normalizeBaseUrl(envUrl.replace('localhost', '127.0.0.1'))

console.log('[API Client] BASE_URL:', BASE_URL, 'from NEXT_PUBLIC_API_URL:', process.env.NEXT_PUBLIC_API_URL)

const instance = axios.create({
  baseURL: BASE_URL,
  headers: { Accept: 'application/json' }
})

const getAxiosErrorMessage = (err: any) => {
  const normalize = (value: any) => {
    if (typeof value === 'string') return value
    if (value === undefined || value === null) return ''
    try {
      return JSON.stringify(value)
    } catch (_err) {
      return String(value)
    }
  }

  if (axios.isAxiosError(err)) {
    if (err.request && !err.response) {
      console.error('[API Client] Axios request sent but no response received', err.config?.url, err.message)
      return 'Backend not running'
    }
    const detail = err.response?.data?.detail
    const data = err.response?.data
    const status = err.response?.status
    const url = err.config?.url
    console.error('[API Client] Axios error response', { url, status, data, message: err.message })
    const message = normalize(detail || data || err.message || 'Network error')
    return status ? `${message} (${status} ${url})` : message
  }
  return normalize(err?.message || err || 'Network error')
}

export const apiClient = {
  // Get persons list
  getPersons: async (limit = 100, offset = 0, status?: string) => {
    try {
      const tryUrls = ['/api/persons', '/api/get_people', '/api/getPeople']
      for (const url of tryUrls) {
        try {
          const resp = await instance.get(url)
          return { success: true, data: resp.data?.persons ?? resp.data ?? [] }
        } catch (error) {
          // continue to next endpoint alias
        }
      }
      return { success: false, error: 'No matching persons endpoint found', data: null }
    } catch (err: any) {
      return { success: false, error: getAxiosErrorMessage(err), data: null }
    }
  },

  // Register / add a person - use the face recognition JSON registration endpoint
  addPerson: async (payload: FormData | { name: string; image_base64: string; status?: string }) => {
    try {
      const buildJsonBodyFromFormData = async (formData: FormData) => {
        const file = formData.get('file') as File | null
        const name = formData.get('name')?.toString?.() ?? ''
        if (!file || !name) return null

        const base64Image = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader()
          reader.onload = (e) => {
            const result = e.target?.result
            if (!result || typeof result !== 'string') {
              reject(new Error('Unable to read file'))
              return
            }
            resolve(result.split(',')[1])
          }
          reader.onerror = () => reject(new Error('Failed to read file'))
          reader.readAsDataURL(file as File)
        })

        const status = formData.get('status')?.toString?.()
        const caseNo = formData.get('case_no')?.toString?.()
        const ageValue = formData.get('age')?.toString?.()

        const body: any = { name, image_base64: base64Image }
        if (status) body.status = status
        const metadata: any = {}
        if (caseNo) metadata.case_no = caseNo
        if (ageValue) metadata.age = isNaN(Number(ageValue)) ? ageValue : Number(ageValue)
        if (Object.keys(metadata).length > 0) body.metadata = metadata
        return body
      }

      if (payload instanceof FormData) {
        const jsonBody = await buildJsonBodyFromFormData(payload)
        if (!jsonBody) {
          return { success: false, error: 'Invalid registration form data', data: null }
        }

        try {
          console.log('[API Client] addPerson JSON POST /api/register', { url: '/api/register', body: jsonBody })
          const resp = await instance.post('/api/register', jsonBody, { headers: { 'Content-Type': 'application/json' } })
          console.log('[API Client] addPerson success', resp.data)
          return { success: true, data: resp.data }
        } catch (e: any) {
          console.error('[API Client] addPerson failed', {
            url: '/api/register',
            error: e?.message,
            response: axios.isAxiosError(e) ? e.response?.data : null,
            status: axios.isAxiosError(e) ? e.response?.status : null,
          })
          if (axios.isAxiosError(e) && e.request && !e.response) {
            return { success: false, error: 'Backend not running', data: null }
          }
          return { success: false, error: getAxiosErrorMessage(e), data: null }
        }
      }

      // If payload is already JSON, call the register endpoint directly
      try {
        const resp = await instance.post('/api/register', payload, { headers: { 'Content-Type': 'application/json' } })
        return { success: true, data: resp.data }
      } catch (e: any) {
        if (axios.isAxiosError(e) && e.request && !e.response) {
          return { success: false, error: 'Backend not running', data: null }
        }
        return { success: false, error: getAxiosErrorMessage(e), data: null }
      }
    } catch (err: any) {
      return { success: false, error: getAxiosErrorMessage(err), data: null }
    }
  },

  // Get alerts (recent matches)
  getAlerts: async (limit = 50, startDate?: string, endDate?: string) => {
    try {
      const params = new URLSearchParams()
      params.append('limit', String(limit))
      if (startDate) params.append('start_date', startDate)
      if (endDate) params.append('end_date', endDate)
      const resp = await instance.get(`/api/alerts?${params.toString()}`)
      const raw = resp.data ?? []
      if (Array.isArray(raw)) {
        return {
          success: true,
          data: raw.map((r: any) => ({
            id: r.id ?? r.person_id,
            person_id: r.person_id ?? r.id,
            person_name: r.person_name ?? r.name ?? r.person,
            similarity: r.similarity ?? 0.0,
            location: r.location ?? '',
            created_at: r.created_at ?? new Date().toISOString()
          }))
        }
      }
      return { success: true, data: [] }
    } catch (err: any) {
      // If the backend does not provide alerts, return an empty list instead of blocking the dashboard
      return { success: true, data: [], error: getAxiosErrorMessage(err) }
    }
  },

  getPersonAlerts: async (personId: number, limit = 50) => {
    try {
      const resp = await instance.get(`/api/alerts/${personId}`).catch(() => instance.get(`/api/alerts/by-person/${personId}?limit=${limit}`))
      const raw = resp.data ?? []
      if (Array.isArray(raw)) {
        return {
          success: true,
          data: raw.map((r: any) => ({
            id: r.id ?? r.person_id,
            person_id: r.person_id ?? personId,
            person_name: r.person_name ?? r.name ?? r.person,
            similarity: r.similarity ?? 0.0,
            location: r.location ?? '',
            created_at: r.created_at ?? new Date().toISOString()
          }))
        }
      }
      return { success: true, data: [] }
    } catch (err: any) {
      return { success: true, data: [], error: err?.message || 'Network error' }
    }
  },

  deleteAlert: async (alertId: number) => {
    try {
      const resp = await instance.delete(`/api/alerts/${alertId}`).catch(() => instance.delete(`/api/alerts/${alertId}`))
      return { success: true, data: resp.data }
    } catch (err: any) {
      return { success: false, error: err?.message || 'Network error', data: null }
    }
  },

  // Delete person
  deletePerson: async (personId: number) => {
    try {
      const resp = await instance.delete(`/api/person/${personId}`).catch(() => instance.delete(`/api/delete_person/${personId}`))
      return { success: true, data: resp.data }
    } catch (err: any) {
      return { success: false, error: err?.message || 'Network error', data: null }
    }
  },

  // Get dashboard statistics
  getStats: async (startDate?: string, endDate?: string) => {
    try {
      const params = new URLSearchParams()
      if (startDate) params.append('start_date', startDate)
      if (endDate) params.append('end_date', endDate)
      const queryString = params.toString() ? `?${params.toString()}` : ''
      let resp = await instance.get(`/api/stats/summary${queryString}`).catch(() => instance.get(`/api/stats${queryString}`)).catch(() => instance.get(`/api/statistics${queryString}`))
      const rawData = resp.data ?? {}
      const data = rawData.statistics ? rawData.statistics : rawData
      const recentAlerts = rawData?.recent_alerts ?? rawData?.alerts ?? []

      return {
        success: true,
        data: {
          total_persons: data.total_persons ?? data.total_registered_persons ?? 0,
          missing_persons: data.missing_persons ?? 0,
          wanted_persons: data.wanted_persons ?? 0,
          total_matches: data.total_matches ?? data.total_facial_embeddings ?? 0,
          total_alerts: data.total_alerts ?? 0,
          active_alerts: data.active_alerts ?? 0,
          total_scans: data.total_scans ?? 0,
          recent_alerts: recentAlerts
        }
      }
    } catch (err: any) {
      return { success: false, error: getAxiosErrorMessage(err), data: null }
    }
  },

  // System health - try multiple endpoints with proper error handling
  getSystemHealth: async () => {
    const endpoints = ['/api/health', '/health', '/api/system/health']
    console.log('[API Client] Checking backend health with BASE_URL:', BASE_URL)
    for (const endpoint of endpoints) {
      try {
        const fullUrl = BASE_URL + endpoint
        console.log('[API Client] Trying health endpoint:', fullUrl)
        const resp = await instance.get(endpoint, { timeout: 5000 })
        console.log('[API Client] Health check succeeded:', resp.status, resp.data)
        if (resp.status === 200) {
          return { success: true, data: resp.data }
        }
      } catch (err: any) {
        console.log('[API Client] Health check failed for', endpoint, ':', err.message)
        // Continue to next endpoint
        continue
      }
    }
    // If all endpoints failed
    console.error('[API Client] All health endpoints failed')
    return { success: false, error: 'Backend not reachable', data: null }
  },

  // Match face
  matchFace: async (payload: { image_base64: string; top_k?: number } | File) => {
    const base64ToFile = async (base64: string, filename = 'upload.png', mimeType = 'image/png') => {
      const binary = atob(base64)
      const length = binary.length
      const bytes = new Uint8Array(length)
      for (let i = 0; i < length; i += 1) {
        bytes[i] = binary.charCodeAt(i)
      }
      return new File([bytes], filename, { type: mimeType })
    }

    const sendMatchRequest = async (payloadBody: { image_base64: string; top_k?: number }) => {
      const resp = await instance.post('/api/match', payloadBody, { headers: { 'Content-Type': 'application/json' } })
      return { success: true, data: resp.data }
    }

    const sendScanFrameRequest = async (file: File) => {
      const form = new FormData()
      form.append('file', file)
      const resp = await instance.post('/api/scan_frame', form)
      return { success: true, data: resp.data }
    }

    const convertFileToBase64 = async (file: File) => {
      const reader = new FileReader()
      return await new Promise<string>((resolve, reject) => {
        reader.onload = (e) => resolve(e.target?.result as string)
        reader.onerror = () => reject(new Error('Failed to read file'))
        reader.readAsDataURL(file)
      })
    }

    try {
      if (payload instanceof File) {
        const dataUrl = await convertFileToBase64(payload)
        const base64Image = dataUrl.split(',')[1]
        try {
          return await sendMatchRequest({ image_base64: base64Image, top_k: 5 })
        } catch (err: any) {
          if (axios.isAxiosError(err) && err.response?.status === 404) {
            return await sendScanFrameRequest(payload)
          }
          throw err
        }
      }

      try {
        return await sendMatchRequest(payload)
      } catch (err: any) {
        if (axios.isAxiosError(err) && err.response?.status === 404) {
          const mime = payload.image_base64.startsWith('data:') ? payload.image_base64.split(';')[0].split(':')[1] : 'image/png'
          const file = await base64ToFile(payload.image_base64, 'upload.png', mime)
          return await sendScanFrameRequest(file)
        }
        throw err
      }
    } catch (err: any) {
      return { success: false, error: getAxiosErrorMessage(err), data: null }
    }
  },

  // Compare faces
  compareFaces: async (payload: { image1_base64: string; image2_base64: string }) => {
    try {
      const resp = await instance.post('/api/compare', payload, { headers: { 'Content-Type': 'application/json' } })
      return { success: true, data: resp.data }
    } catch (err: any) {
      return { success: false, error: err?.message || 'Network error', data: null }
    }
  },

  // Process video for face recognition
  processVideo: async (file: File, onProgress?: (progress: number) => void) => {
    try {
      const formData = new FormData()
      formData.append('video', file)

      const resp = await instance.post('/api/process_video', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            onProgress(percentCompleted)
          }
        }
      })
      return { success: true, data: resp.data }
    } catch (err: any) {
      return { success: false, error: getAxiosErrorMessage(err), data: null }
    }
  },

  // Scan frame for face recognition
  scanFrame: async (file: File, location = "CCTV-01") => {
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('location', location)

      const resp = await instance.post('/api/scan_frame', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      return { success: true, data: resp.data }
    } catch (err: any) {
      return { success: false, error: getAxiosErrorMessage(err), data: null }
    }
  },

  getCCTVs: async () => {
    try {
      const resp = await instance.get('/api/cctv')
      return { success: true, data: resp.data }
    } catch (err: any) {
      return { success: false, error: getAxiosErrorMessage(err), data: null }
    }
  },

  connectCCTV: async (payload: { name: string; location: string; stream_url: string }) => {
    try {
      const resp = await instance.post('/api/connect-cctv', payload, { headers: { 'Content-Type': 'application/json' } })
      return { success: true, data: resp.data }
    } catch (err: any) {
      return { success: false, error: getAxiosErrorMessage(err), data: null }
    }
  },

  updateCCTV: async (cameraId: number, payload: { enabled?: boolean; connected?: boolean }) => {
    try {
      const resp = await instance.patch(`/api/cctv/${cameraId}`, payload, { headers: { 'Content-Type': 'application/json' } })
      return { success: true, data: resp.data }
    } catch (err: any) {
      return { success: false, error: getAxiosErrorMessage(err), data: null }
    }
  },

  disconnectCCTV: async (cameraId: number) => {
    try {
      const resp = await instance.delete(`/api/cctv/${cameraId}`)
      return { success: true, data: resp.data }
    } catch (err: any) {
      return { success: false, error: getAxiosErrorMessage(err), data: null }
    }
  },

  // SSE helper
  createEventSource: (path = '/api/events') => {
    try {
      const url = `${BASE_URL}${path}`
      const es = new EventSource(url)
      return es
    } catch (err) {
      console.error('Failed to create EventSource', err)
      return null
    }
  }
}

export default apiClient
