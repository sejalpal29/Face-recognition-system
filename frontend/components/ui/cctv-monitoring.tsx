"use client"

import React, { useRef, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Upload, Image as ImageIcon, AlertCircle, Loader, CheckCircle, Video } from "lucide-react"
import { apiClient } from "@/lib/api-client"
import { useAddPerson } from "@/lib/api"
import { useEffect } from "react"

interface MatchResult {
  person_id: number
  name: string
  similarity: number
  confidence: number
}

interface FaceMatchDetail {
  person_id: number
  name: string
  similarity: number
  confidence: number
  status: string
}

interface ImageFaceMatch {
  face_index: number
  detection_bbox: number[]
  matches: FaceMatchDetail[]
  best_match: FaceMatchDetail
  status: 'matched' | 'unknown'
  best_similarity: number
}

export default function CCTVMonitoring() {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const registerFileRef = useRef<HTMLInputElement>(null)
  const videoFileRef = useRef<HTMLInputElement>(null)
  const imageRef = useRef<HTMLImageElement>(null)
  const [uploadedImage, setUploadedImage] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string>("")
  const [registerImageData, setRegisterImageData] = useState<string | null>(null)
  const [registerFileNameLocal, setRegisterFileNameLocal] = useState("")
  const [matchResults, setMatchResults] = useState<MatchResult[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [bestMatch, setBestMatch] = useState<MatchResult | null>(null)
  const [errorMessage, setErrorMessage] = useState<string>("")
  const [recentAlerts, setRecentAlerts] = useState<any[]>([])
  const [alertsLoading, setAlertsLoading] = useState(false)

  // Video processing state
  const [videoFile, setVideoFile] = useState<File | null>(null)
  const [videoFileName, setVideoFileName] = useState<string>("")
  const [isProcessingVideo, setIsProcessingVideo] = useState(false)
  const [videoProgress, setVideoProgress] = useState<number>(0)
  const [videoResults, setVideoResults] = useState<any[]>([])
  const [videoError, setVideoError] = useState<string>("")
  const [videoProcessed, setVideoProcessed] = useState(false)
  const [imageFaceMatches, setImageFaceMatches] = useState<ImageFaceMatch[]>([])
  const [imageProcessed, setImageProcessed] = useState(false)
  const [imageNaturalSize, setImageNaturalSize] = useState({ width: 1, height: 1 })
  const [imageDisplaySize, setImageDisplaySize] = useState({ width: 1, height: 1 })
  const [backendStatus, setBackendStatus] = useState<'online' | 'offline' | 'unknown'>('unknown')
  const [backendStatusMessage, setBackendStatusMessage] = useState<string>('Checking backend status...')

  // Registration state
  const [showRegisterForm, setShowRegisterForm] = useState(false)
  const [registerName, setRegisterName] = useState("")
  const [registerAge, setRegisterAge] = useState("")
  const [registerCaseNo, setRegisterCaseNo] = useState("")
  const [registerStatus, setRegisterStatus] = useState<string>("missing")
  const [registerMessage, setRegisterMessage] = useState<string | null>(null)
  const [registerError, setRegisterError] = useState<string | null>(null)
  const { addPerson, loading: registerLoading } = useAddPerson()
  const apiUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, '') ?? ''

  const [cameras, setCameras] = useState<any[]>([])
  const [cameraLoading, setCameraLoading] = useState(false)

  const [manualCameraName, setManualCameraName] = useState("")
  const [manualCameraLocation, setManualCameraLocation] = useState("")
  const [manualStreamUrl, setManualStreamUrl] = useState("")
  const [manualConnectError, setManualConnectError] = useState<string | null>(null)
  const [manualConnectMessage, setManualConnectMessage] = useState<string | null>(null)
  const [manualConnecting, setManualConnecting] = useState(false)

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setErrorMessage("")
      setMatchResults([])
      setBestMatch(null)
      setFileName(file.name)

      if (!file.type.startsWith("image/")) {
        setErrorMessage("Please upload an image file (JPG, PNG, GIF, etc.)")
        return
      }

      if (file.size > 10 * 1024 * 1024) {
        setErrorMessage("File size must be less than 10MB")
        return
      }

      const reader = new FileReader()
      reader.onload = (e) => setUploadedImage(e.target?.result as string)
      reader.readAsDataURL(file)
    }
  }

  const handleRegisterFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setRegisterFileNameLocal(file.name)
      if (!file.type.startsWith("image/")) {
        setRegisterMessage("Please upload an image file (JPG, PNG, GIF, etc.)")
        return
      }
      if (file.size > 10 * 1024 * 1024) {
        setRegisterMessage("File size must be less than 10MB")
        return
      }
      const reader = new FileReader()
      reader.onload = (e) => setRegisterImageData(e.target?.result as string)
      reader.readAsDataURL(file)
    }
  }

  const handleVideoFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const allowedTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo']
      if (!allowedTypes.includes(file.type)) {
        setVideoError("Please upload a video file (.mp4, .avi, .mov)")
        return
      }
      if (file.size > 100 * 1024 * 1024) { // 100MB limit for videos
        setVideoError("Video file size must be less than 100MB")
        return
      }
      setVideoFile(file)
      setVideoFileName(file.name)
      setVideoError("")
      setVideoResults([])
    }
  }

  const handleCompareImage = async () => {
    if (!uploadedImage) {
      setErrorMessage("Please upload an image first")
      return
    }
    setIsProcessing(true)
    setErrorMessage("")
    setMatchResults([])
    setBestMatch(null)
    setImageFaceMatches([])
    setImageProcessed(false)

    try {
      const parts = uploadedImage.split(',')
      const mimeMatch = parts[0].match(/:(.*?);/)
      const mime = mimeMatch ? mimeMatch[1] : 'image/png'
      const bstr = atob(parts[1])
      const n = bstr.length
      const u8arr = new Uint8Array(n)
      for (let i = 0; i < n; i += 1) {
        u8arr[i] = bstr.charCodeAt(i)
      }
      const file = new File([u8arr], fileName || 'upload.png', { type: mime })
      const result = await apiClient.matchFace(file)
      if (!result || !result.success) {
        const errorInfo = (result as any)?.error
        setErrorMessage(typeof errorInfo === 'string' ? errorInfo : JSON.stringify(errorInfo) || 'Failed to contact server')
      } else {
        const data = result.data as any
        if (data.matches && Array.isArray(data.matches) && data.matches.length > 0) {
          setImageFaceMatches(data.matches)
          console.log('[CCTV] Received matches:', JSON.stringify(data.matches, null, 2))
          
          // Process each face independently using the backend best_match result
          const allFaceMatches: MatchResult[] = data.matches.map((faceMatch: any, faceIdx: number) => {
            const bestMatch = faceMatch.best_match || { person_id: -1, name: 'Unknown', similarity: 0, confidence: 0, status: 'unknown' }
            console.log(`[CCTV] Face ${faceIdx}: best match ${bestMatch.name} (similarity: ${(bestMatch.similarity || 0).toFixed(3)})`)
            
            return {
              person_id: bestMatch.person_id ?? -1,
              name: bestMatch.name || 'Unknown',
              similarity: typeof bestMatch.similarity === 'number' ? bestMatch.similarity : 0,
              confidence: typeof bestMatch.confidence === 'number' ? bestMatch.confidence : 0
            }
          })
          setMatchResults(allFaceMatches)
          
          // Find the best match among all detected faces (above threshold only)
          const matchesAboveThreshold = allFaceMatches.filter(m => m.confidence >= 0.55)
          if (matchesAboveThreshold.length > 0) {
            const best = matchesAboveThreshold.reduce((current, next) => next.confidence > current.confidence ? next : current)
            setBestMatch(best)
          } else {
            setBestMatch(null)  // No valid matches above threshold
          }
        } else if (data.num_faces_detected === 0 || data.faces_detected === 0) {
          setImageFaceMatches([])
          setMatchResults([])
          setBestMatch(null)
        } else {
          setErrorMessage('No match found')
        }
      }
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to compare image')
    } finally {
      setIsProcessing(false)
      setImageProcessed(true)
    }
  }

  const handleProcessVideo = async () => {
    if (!videoFile) {
      setVideoError("Please upload a video file first")
      return
    }
    setIsProcessingVideo(true)
    setVideoError("")
    setVideoResults([])
    setVideoProgress(0)
    setVideoProcessed(false)

    try {
      const result = await apiClient.processVideo(videoFile, (progress) => {
        setVideoProgress(progress)
      })

      if (!result || !result.success) {
        setVideoError(typeof result?.error === 'string' ? result.error : JSON.stringify(result?.error) || 'Failed to process video')
      } else {
        const data = result.data as any
        if (data.results && Array.isArray(data.results)) {
          setVideoResults(data.results)
        } else if (data.matches && Array.isArray(data.matches)) {
          setVideoResults(data.matches)
        } else {
          setVideoResults([])
          setVideoError("No results found in video processing")
        }
      }
    } catch (err) {
      setVideoError(err instanceof Error ? err.message : 'Failed to process video')
    } finally {
      setIsProcessingVideo(false)
      setVideoProcessed(true)
    }
  }

  const fetchCameras = async () => {
    setCameraLoading(true)
    try {
      const resp = await apiClient.getCCTVs()
      if (resp && resp.success && Array.isArray(resp.data)) {
        setCameras(resp.data)
      } else {
        setCameras([])
      }
    } catch (err) {
      console.error('Failed to fetch CCTV cameras', err)
      setCameras([])
    } finally {
      setCameraLoading(false)
    }
  }

  const fetchBackendHealth = async () => {
    try {
      const resp = await apiClient.getSystemHealth()
      if (resp.success) {
        setBackendStatus('online')
        setBackendStatusMessage('Backend is online')
      } else {
        setBackendStatus('offline')
        setBackendStatusMessage(resp.error || 'Backend not reachable')
      }
    } catch (err) {
      setBackendStatus('offline')
      setBackendStatusMessage('Backend not reachable')
    }
  }

  // Poll alerts every 5 seconds to approximate realtime updates
  useEffect(() => {
    let mounted = true
    const fetchAlerts = async () => {
      setAlertsLoading(true)
      try {
        const resp = await apiClient.getAlerts(10)
        if (mounted) {
          if (resp && resp.success) setRecentAlerts(resp.data || [])
          else setRecentAlerts([])
        }
      } catch (e) {
        console.error('Failed to fetch alerts', e)
      } finally {
        if (mounted) setAlertsLoading(false)
      }
    }

    fetchAlerts()
    fetchCameras()
    fetchBackendHealth()
    const id = setInterval(fetchAlerts, 5000)
    return () => { mounted = false; clearInterval(id) }
  }, [])

  const dataUrlToBlob = (dataUrl: string) => {
    const parts = dataUrl.split(',')
    const matches = parts[0].match(/:(.*?);/)
    const mime = matches ? matches[1] : 'image/png'
    const bstr = atob(parts[1])
    let n = bstr.length
    const u8arr = new Uint8Array(n)
    while (n--) {
      u8arr[n] = bstr.charCodeAt(n)
    }
    return new Blob([u8arr], { type: mime })
  }

  const handleRegister = async () => {
    const imageForRegister = uploadedImage || registerImageData
    if (!imageForRegister) {
      setRegisterMessage('Please upload an image to register')
      return
    }
    if (!registerName.trim()) {
      setRegisterMessage('Please provide a name for registration')
      return
    }
    if (!registerCaseNo.trim()) {
      setRegisterMessage('Please provide a case number')
      return
    }

    try {
      if (backendStatus === 'offline') {
        console.warn('[CCTV Monitoring] backendStatus is offline, attempting registration anyway')
      }
      setRegisterMessage(null)
      const blob = dataUrlToBlob(imageForRegister)
      const formData = new FormData()
      formData.append('name', registerName)
      if (registerAge !== '' && !isNaN(Number(registerAge))) {
        formData.append('age', registerAge)
      }
      formData.append('case_no', registerCaseNo)
      formData.append('status', registerStatus)
      formData.append('file', blob, 'face.png')

      const response = await addPerson(formData) as { success?: boolean; error?: string | null }
      console.log('[CCTV Monitoring] register response', response)
      if (response && response.success) {
        setRegisterMessage('Person registered successfully')
        setRegisterError(null)
        setShowRegisterForm(false)
        setRegisterName("")
        setRegisterAge("")
        setRegisterCaseNo("")
        setRegisterStatus("missing")
      } else {
        const errorText = response?.error || 'Failed to register person'
        console.error('[CCTV Monitoring] register error', errorText)
        setRegisterMessage(null)
        setRegisterError(errorText)
      }
    } catch (err) {
      const errorText = err instanceof Error ? err.message : 'Registration failed'
      console.error('[CCTV Monitoring] register exception', errorText)
      setRegisterMessage(null)
      setRegisterError(errorText)
    }
  }

  const handleManualCCTVConnect = async () => {
    setManualConnectError(null)
    setManualConnectMessage(null)

    if (!manualCameraName.trim() || !manualCameraLocation.trim() || !manualStreamUrl.trim()) {
      setManualConnectError('Camera name, location and stream URL are required.')
      return
    }

    setManualConnecting(true)
    try {
      const resp = await apiClient.connectCCTV({
        name: manualCameraName,
        location: manualCameraLocation,
        stream_url: manualStreamUrl
      })
      if (resp.success) {
        setManualConnectMessage('CCTV connected successfully.')
        setManualCameraName("")
        setManualCameraLocation("")
        setManualStreamUrl("")
        await fetchCameras()
      } else {
        setManualConnectError(resp.error || 'Failed to connect CCTV manually.')
      }
    } catch (err) {
      setManualConnectError(err instanceof Error ? err.message : 'Failed to connect CCTV manually.')
    } finally {
      setManualConnecting(false)
    }
  }

  const clearUpload = () => {
    setUploadedImage(null)
    setFileName("")
    setMatchResults([])
    setBestMatch(null)
    setErrorMessage("")
    setImageFaceMatches([])
    setImageProcessed(false)
    setImageNaturalSize({ width: 1, height: 1 })
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const clearVideo = () => {
    setVideoFile(null)
    setVideoFileName("")
    setVideoResults([])
    setVideoError("")
    setVideoProgress(0)
    setVideoProcessed(false)
    if (videoFileRef.current) videoFileRef.current.value = ''
  }

  const accuracyPercentage = bestMatch ? Math.round(bestMatch.similarity * 100) : 0
  const videoHasFaces = videoResults.some((result) => Array.isArray(result.faces) && result.faces.length > 0)
  const videoHasRegisteredFaces = videoResults.some((result) =>
    Array.isArray(result.faces) &&
    result.faces.some((face: any) => face.match && face.match.name && face.match.name !== 'Unknown')
  )
  const videoFramesProcessed = videoResults.length
  const videoFacesDetected = videoResults.reduce((count, result) => count + (Array.isArray(result.faces) ? result.faces.length : 0), 0)
  const videoRegisteredFaces = videoResults.reduce(
    (count, result) => count + (Array.isArray(result.faces) ? result.faces.filter((face: any) => face.match && face.match.name && face.match.name !== 'Unknown').length : 0),
    0
  )
  const videoUnknownFaces = videoFacesDetected - videoRegisteredFaces
  const imageHasFaces = imageFaceMatches.length > 0
  const imageHasRegisteredFaces = imageFaceMatches.some((face) =>
    face.best_match?.name && face.best_match.name !== 'Unknown'
  )
  const imageUnknownFaceCount = imageFaceMatches.filter((face) =>
    !face.best_match || face.best_match.name === 'Unknown'
  ).length

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold">Face Recognition</h2>
        <p className="text-muted-foreground">Upload an image to compare with registered persons</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          {backendStatus === 'offline' && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              Backend unavailable: {backendStatusMessage}. Start the backend at http://localhost:8000 and reload.
            </div>
          )}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Upload className="h-5 w-5" /> Upload Image</CardTitle>
              <CardDescription>Select an image file from your computer</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div
                className="border-2 border-dashed border-muted-foreground/30 rounded-lg p-8 text-center cursor-pointer hover:border-primary hover:bg-muted/50 transition-colors"
                onClick={() => fileInputRef.current?.click()}
              >
                <ImageIcon className="h-12 w-12 mx-auto text-muted-foreground mb-3" />
                <p className="font-medium">Click to upload image</p>
                <p className="text-sm text-muted-foreground">or drag and drop</p>
                <p className="text-xs text-muted-foreground mt-2">PNG, JPG, GIF (max 10MB)</p>
              </div>

              <input ref={fileInputRef} type="file" accept="image/*" onChange={handleFileUpload} className="hidden" />

              {errorMessage && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-start gap-3">
                  <AlertCircle className="h-5 w-5 text-red-600" />
                  <div><p className="text-sm font-medium text-red-900">{errorMessage}</p></div>
                </div>
              )}

              {fileName && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <p className="text-sm text-blue-900"><strong>File:</strong> {fileName}</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Video className="h-5 w-5" /> Process Video</CardTitle>
              <CardDescription>Upload a video file to detect and match faces across frames</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div
                className="border-2 border-dashed border-muted-foreground/30 rounded-lg p-8 text-center cursor-pointer hover:border-primary hover:bg-muted/50 transition-colors"
                onClick={() => videoFileRef.current?.click()}
              >
                <Video className="h-12 w-12 mx-auto text-muted-foreground mb-3" />
                <p className="font-medium">Click to upload video</p>
                <p className="text-sm text-muted-foreground">or drag and drop</p>
                <p className="text-xs text-muted-foreground mt-2">MP4, AVI, MOV (max 100MB)</p>
              </div>

              <input ref={videoFileRef} type="file" accept="video/mp4,video/avi,video/quicktime,video/x-msvideo" onChange={handleVideoFileUpload} className="hidden" />

              {videoError && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-start gap-3">
                  <AlertCircle className="h-5 w-5 text-red-600" />
                  <div><p className="text-sm font-medium text-red-900">{videoError}</p></div>
                </div>
              )}

              {videoFileName && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <p className="text-sm text-blue-900"><strong>Video File:</strong> {videoFileName}</p>
                </div>
              )}

              {videoFile && (
                <div className="space-y-3">
                  {isProcessingVideo && (
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Processing video...</span>
                        <span>{videoProgress}%</span>
                      </div>
                      <Progress value={videoProgress} className="h-2" />
                    </div>
                  )}

                  <div className="flex gap-2">
                    <Button onClick={handleProcessVideo} disabled={isProcessingVideo} className="flex-1">
                      {isProcessingVideo ? <><Loader className="h-4 w-4 mr-2 animate-spin" /> Processing...</> : 'Process Video'}
                    </Button>
                    <Button onClick={clearVideo} variant="outline">Clear</Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recent Alerts</CardTitle>
              <CardDescription>Live alerts (polled every 5s)</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 max-h-48 overflow-y-auto">
              {alertsLoading && <div className="text-sm">Loading...</div>}
              {!alertsLoading && recentAlerts.length === 0 && (
                <div className="text-sm text-muted-foreground">No alerts</div>
              )}
              {recentAlerts.map((a) => (
                <div key={a.id} className="p-2 rounded border flex justify-between items-center">
                  <div>
                    <div className="font-medium text-sm">{a.person_name || 'Unknown'}</div>
                    <div className="text-xs text-muted-foreground">{new Date(a.created_at).toLocaleString()}</div>
                  </div>
                  <Badge className="text-xs">{Math.round((a.similarity || 0) * 100)}%</Badge>
                </div>
              ))}
            </CardContent>
          </Card>

          {!uploadedImage && (
            <Card>
              <CardHeader><CardTitle className="text-base">How it works</CardTitle></CardHeader>
              <CardContent className="space-y-2 text-sm text-muted-foreground">
                <p>1. Upload an image</p>
                <p>2. The system detects faces and compares them</p>
                <p>3. View matching results and accuracy</p>
                <p>4. Optionally register the person</p>
              </CardContent>
            </Card>
          )}

          {uploadedImage && (
            <Card>
              <CardHeader><CardTitle>Image Preview</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div className="relative overflow-hidden rounded-lg border border-muted bg-black">
                  <img
                    ref={imageRef}
                    onLoad={(e) => {
                      setImageNaturalSize({ width: e.currentTarget.naturalWidth, height: e.currentTarget.naturalHeight })
                      setImageDisplaySize({ width: e.currentTarget.clientWidth, height: e.currentTarget.clientHeight })
                    }}
                    src={uploadedImage}
                    alt="Uploaded preview"
                    className="w-full max-h-96 object-contain"
                  />
                  {imageFaceMatches.map((face, faceIndex) => {
                    const [x, y, w, h] = face.detection_bbox
                    const originalWidth = imageNaturalSize.width > 0 ? imageNaturalSize.width : 1
                    const originalHeight = imageNaturalSize.height > 0 ? imageNaturalSize.height : 1
                    const widthPercent = (w / originalWidth) * 100
                    const heightPercent = (h / originalHeight) * 100
                    const leftPercent = (x / originalWidth) * 100
                    const topPercent = (y / originalHeight) * 100
                    const label = face.best_match?.name || 'Unknown'

                    return (
                      <div
                        key={faceIndex}
                        className="absolute border-2 border-blue-500/95 bg-blue-500/10"
                        style={{ left: `${leftPercent}%`, top: `${topPercent}%`, width: `${widthPercent}%`, height: `${heightPercent}%` }}
                      >
                        <span className="absolute left-1/2 top-0 -translate-x-1/2 -translate-y-1/2 rounded-br bg-blue-700 px-1 text-[10px] text-white">
                          {label}
                        </span>
                      </div>
                    )
                  })}
                </div>
                <div className="flex gap-2">
                  <Button onClick={handleCompareImage} disabled={isProcessing || backendStatus === 'offline'} className="flex-1">
                    {isProcessing ? <><Loader className="h-4 w-4 mr-2 animate-spin" /> Comparing...</> : 'Compare with Database'}
                  </Button>
                  <Button onClick={() => setShowRegisterForm((v) => !v)} variant="secondary">{showRegisterForm ? 'Cancel' : 'Register'}</Button>
                  <Button onClick={clearUpload} variant="outline">Clear</Button>
                </div>

                {showRegisterForm && (
                  <div className="mt-4 space-y-3 border-t pt-4">
                    <div className="bg-blue-50 border border-blue-200 rounded p-3 mb-2">
                      <p className="text-sm text-blue-900 font-medium">Required fields marked with *</p>
                    </div>
                    <input type="text" placeholder="Name *" value={registerName} onChange={(e) => setRegisterName(e.target.value)} className="w-full px-3 py-2 border rounded-md text-sm" />
                    <div className="grid grid-cols-2 gap-2">
                      <input type="number" min="0" max="150" placeholder="Age (optional)" value={registerAge} onChange={(e) => setRegisterAge(e.target.value)} className="w-full px-3 py-2 border rounded-md text-sm" />
                      <input type="text" placeholder="Case No. *" value={registerCaseNo} onChange={(e) => setRegisterCaseNo(e.target.value)} className="w-full px-3 py-2 border rounded-md text-sm border-red-300" />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Status</label>
                      <Select value={registerStatus} onValueChange={setRegisterStatus}>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Select status" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="missing">Missing</SelectItem>
                          <SelectItem value="wanted">Wanted</SelectItem>
                          <SelectItem value="found">Found</SelectItem>
                          <SelectItem value="registered">Registered</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="flex gap-2">
                      <Button onClick={handleRegister} disabled={registerLoading || backendStatus === 'offline'} className="flex-1">{registerLoading ? 'Registering...' : 'Confirm Register'}</Button>
                      <Button onClick={() => { setShowRegisterForm(false); setRegisterName(''); setRegisterAge(''); setRegisterCaseNo(''); setRegisterStatus('missing'); }} variant="outline">Cancel</Button>
                    </div>
                    {registerMessage && <div className="text-sm p-2 rounded bg-green-50 text-green-700 border border-green-200">{registerMessage}</div>}
                    {registerError && <div className="text-sm p-2 rounded bg-red-50 text-red-700 border border-red-200"><strong>Error:</strong> {registerError}</div>}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-4">
          {/* Manual CCTV Connect */}
          <Card>
            <CardHeader>
              <CardTitle>Manual CCTV Connect</CardTitle>
              <CardDescription>Enter camera details and connect a CCTV source directly.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2">
                <label className="text-sm font-medium">Camera Name</label>
                <input type="text" value={manualCameraName} onChange={(e) => setManualCameraName(e.target.value)} className="w-full px-3 py-2 border rounded-md text-sm" placeholder="Front gate camera" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Location</label>
                <input type="text" value={manualCameraLocation} onChange={(e) => setManualCameraLocation(e.target.value)} className="w-full px-3 py-2 border rounded-md text-sm" placeholder="Main gate" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Stream URL</label>
                <input type="text" value={manualStreamUrl} onChange={(e) => setManualStreamUrl(e.target.value)} className="w-full px-3 py-2 border rounded-md text-sm" placeholder="rtsp://... or http://..." />
              </div>
              {manualConnectError && <div className="text-sm text-red-700 rounded bg-red-50 p-2">{manualConnectError}</div>}
              {manualConnectMessage && <div className="text-sm text-green-700 rounded bg-green-50 p-2">{manualConnectMessage}</div>}
              <div className="flex gap-2">
                <Button onClick={handleManualCCTVConnect} disabled={manualConnecting} className="flex-1">
                  {manualConnecting ? 'Connecting…' : 'Connect CCTV Manually'}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Recent Alerts */}
          <Card>
            <CardHeader>
              <CardTitle>Connected CCTV Cameras</CardTitle>
              <CardDescription>Live preview for cameras that are connected and streaming.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {cameraLoading ? (
                <div className="text-sm text-muted-foreground">Loading connected cameras...</div>
              ) : cameras.length === 0 ? (
                <div className="rounded-lg border border-dashed border-muted p-4 text-sm text-muted-foreground">
                  No CCTV cameras connected yet.
                </div>
              ) : (
                <div className="space-y-4">
                  {cameras.map((camera) => (
                    <Card key={camera.id} className="border">
                      <CardHeader>
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <CardTitle>{camera.name}</CardTitle>
                            <CardDescription>{camera.location}</CardDescription>
                          </div>
                          <Badge variant={camera.status === 'streaming' ? 'default' : 'secondary'}>{camera.status || 'offline'}</Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {camera.enabled && camera.connected ? (
                          <div className="overflow-hidden rounded-md border border-slate-200 bg-slate-950">
                            <img
                              alt={`Live preview for ${camera.name}`}
                              src={`${apiUrl || ''}/api/video-feed/${camera.id}`}
                              className="h-60 w-full object-cover"
                            />
                          </div>
                        ) : (
                          <div className="flex h-60 items-center justify-center rounded-md border border-dashed border-slate-300 bg-slate-50 text-sm text-slate-600">
                            {camera.connected ? 'Camera connected but stream not active' : 'Camera disconnected'}
                          </div>
                        )}

                        <div className="grid gap-2 sm:grid-cols-2 text-sm text-muted-foreground">
                          <p className="truncate">Stream URL: {camera.stream_url}</p>
                          <p>Last seen: {camera.last_seen ? new Date(camera.last_seen).toLocaleString() : 'N/A'}</p>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {bestMatch && (
            <Card className="border-green-200 bg-green-50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-green-900"><CheckCircle className="h-5 w-5" /> Best Match Found</CardTitle>
              </CardHeader>
              <CardContent>
                <div>
                  <p className="font-semibold text-lg text-green-900">{bestMatch.name}</p>
                  <p className="text-sm text-green-800">Person ID: {bestMatch.person_id}</p>

                  <div className="space-y-2 mt-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-green-900">Accuracy</span>
                      <Badge className="text-lg px-3 py-1 bg-green-600">{accuracyPercentage}%</Badge>
                    </div>
                    <Progress value={accuracyPercentage} className="h-3" />
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {imageFaceMatches.length > 1 && (
            <Card className="border-blue-200 bg-blue-50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-blue-900">Multiple Faces Detected</CardTitle>
                <CardDescription>Showing match results for each detected face (threshold: 0.55)</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {imageFaceMatches.map((face, faceIndex) => {
                  const bestMatch = face.best_match || { person_id: -1, name: 'Unknown', similarity: 0, confidence: 0, status: 'unknown' }
                  const bestSimilarity = bestMatch.similarity || 0
                  const isAboveThreshold = bestSimilarity >= 0.55
                  
                  return (
                    <div key={faceIndex} className="border rounded-lg p-3 space-y-3 bg-white">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-sm">Face #{faceIndex + 1}</span>
                        <Badge className="text-xs">Bbox: {face.detection_bbox.join(', ')}</Badge>
                      </div>
                      
                      {isAboveThreshold ? (
                        <div className="space-y-1 p-2 rounded bg-green-50 border border-green-200">
                          <p className="text-sm font-semibold text-green-900">✓ MATCHED: {bestMatch.name}</p>
                          <div className="flex justify-between text-xs text-green-700">
                            <span>Person ID: {bestMatch.person_id}</span>
                            <span>Status: {bestMatch.status || 'registered'}</span>
                          </div>
                          <div className="flex justify-between items-center text-xs text-green-700">
                            <span>Similarity:</span>
                            <Badge className="bg-green-100 text-green-800">{bestSimilarity.toFixed(3)}</Badge>
                          </div>
                          <Progress value={bestSimilarity * 100} className="h-1.5" />
                        </div>
                      ) : (
                        <div className="space-y-1 p-2 rounded bg-yellow-50 border border-yellow-200">
                          <p className="text-sm text-yellow-900">Unknown</p>
                          <p className="text-xs text-yellow-700">Similarity {bestSimilarity.toFixed(3)} is below threshold (0.55)</p>
                        </div>
                      )}
                    </div>
                  )
                })}
              </CardContent>
            </Card>
          )}

          {matchResults.length > 0 && (
            <Card>
              <CardHeader><CardTitle>All Matches ({matchResults.length})</CardTitle><CardDescription>Sorted by accuracy</CardDescription></CardHeader>
              <CardContent className="space-y-2 max-h-96 overflow-y-auto">
                {matchResults.map((match, index) => (
                  <div key={`${match.person_id}-${index}`} className={`p-3 rounded-lg border ${index === 0 ? 'bg-green-50 border-green-200' : 'bg-muted'}`}>
                    <div className="flex justify-between items-start gap-2">
                      <div className="flex-1"><p className="font-medium text-sm">{match.name}</p><p className="text-xs text-muted-foreground">ID: {match.person_id}</p></div>
                      <Badge className="text-xs">{Math.round(match.confidence * 100)}%</Badge>
                    </div>
                    <Progress value={match.confidence * 100} className="h-1.5 mt-2" />
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {!isProcessing && matchResults.length === 0 && uploadedImage && !errorMessage && (
            <Card className="border-yellow-200 bg-yellow-50">
              <CardHeader><CardTitle className="text-base text-yellow-900">No match found</CardTitle></CardHeader>
              <CardContent><p className="text-sm text-yellow-800">No match found.</p></CardContent>
            </Card>
          )}

          {imageProcessed && !isProcessing && !errorMessage && uploadedImage && !imageHasFaces && (
            <Card className="border border-slate-200 bg-slate-50">
              <CardHeader><CardTitle className="text-base">No Faces Detected</CardTitle></CardHeader>
              <CardContent><p className="text-sm text-muted-foreground">No faces were detected in the uploaded image. Please upload a clearer image or a different photo.</p></CardContent>
            </Card>
          )}

          {imageProcessed && !isProcessing && !errorMessage && uploadedImage && imageHasFaces && !imageHasRegisteredFaces && (
            <Card className="border border-yellow-200 bg-yellow-50">
              <CardHeader><CardTitle className="text-base">No match found</CardTitle></CardHeader>
              <CardContent><p className="text-sm text-muted-foreground">No match found.</p></CardContent>
            </Card>
          )}

          {videoProcessed && !isProcessingVideo && !videoError && videoResults.length === 0 && (
            <Card className="border border-slate-200 bg-slate-50">
              <CardHeader><CardTitle className="text-base">No Faces Detected</CardTitle></CardHeader>
              <CardContent><p className="text-sm text-muted-foreground">No faces were detected in the uploaded video. Please try a clearer video or different camera angle.</p></CardContent>
            </Card>
          )}

          {videoProcessed && !isProcessingVideo && !videoError && videoHasFaces && !videoHasRegisteredFaces && (
            <Card className="border border-yellow-200 bg-yellow-50">
              <CardHeader><CardTitle className="text-base">No Registered Faces Found</CardTitle></CardHeader>
              <CardContent><p className="text-sm text-muted-foreground">Faces were detected, but none matched a registered person in the database.</p></CardContent>
            </Card>
          )}

          {videoResults.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Video Processing Results</CardTitle>
                <CardDescription>Faces detected and matched across video frames</CardDescription>
              </CardHeader>
              <div className="flex flex-wrap gap-2 px-4 pb-2">
                <span className="text-xs rounded-full bg-slate-100 px-2 py-1 text-slate-700">Frames processed: {videoFramesProcessed}</span>
                <span className="text-xs rounded-full bg-slate-100 px-2 py-1 text-slate-700">Faces detected: {videoFacesDetected}</span>
                <span className="text-xs rounded-full bg-slate-100 px-2 py-1 text-slate-700">Registered faces: {videoRegisteredFaces}</span>
                <span className="text-xs rounded-full bg-slate-100 px-2 py-1 text-slate-700">Unknown faces: {videoUnknownFaces}</span>
              </div>
              <CardContent className="space-y-4 max-h-96 overflow-y-auto">
                {videoResults.map((result, index) => (
                  <div key={index} className="border rounded-lg p-4 space-y-3">
                    <div className="flex justify-between items-center">
                      <h4 className="font-medium">Frame {result.frame_number || index + 1}</h4>
                      <Badge className="text-xs">{result.timestamp || 'N/A'}</Badge>
                    </div>

                    {result.frame_image && (
                      <div className="relative overflow-hidden rounded-lg border border-slate-200 bg-slate-950">
                        <img
                          src={result.frame_image}
                          alt={`Frame ${result.frame_number || index + 1}`}
                          className="w-full h-60 object-contain bg-black"
                        />
                        <div className="absolute inset-0 pointer-events-none">
                          {result.faces?.map((face: any, faceIndex: number) => {
                            const bbox = Array.isArray(face.detection_bbox)
                              ? face.detection_bbox
                              : face.detection_bbox?.bbox || [0, 0, 0, 0]
                            const [x, y, w, h] = bbox
                            const frameWidth = result.frame_width || 1
                            const frameHeight = result.frame_height || 1
                            return (
                              <div
                                key={faceIndex}
                                className="absolute border-2 border-red-400/90 bg-red-400/10"
                                style={{
                                  left: `${(x / frameWidth) * 100}%`,
                                  top: `${(y / frameHeight) * 100}%`,
                                  width: `${(w / frameWidth) * 100}%`,
                                  height: `${(h / frameHeight) * 100}%`
                                }}
                              >
                                <span className="absolute top-0 left-0 rounded-br bg-red-600 px-1 text-[10px] text-white">
                                  {face.match && face.match.name !== 'Unknown' ? face.match.name : 'Unknown'}
                                </span>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )}

                    {result.faces && result.faces.length > 0 ? (
                      <div className="space-y-2">
                        <p className="text-sm text-muted-foreground">Faces detected: {result.faces.length}</p>
                        {result.faces.map((face: any, faceIndex: number) => (
                          <div key={faceIndex} className="bg-muted/50 rounded p-3 space-y-2">
                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium">Face {faceIndex + 1}</span>
                              {face.match && face.match.name !== 'Unknown' ? (
                                <Badge className="bg-green-100 text-green-800">{face.match.name}</Badge>
                              ) : (
                                <Badge variant="secondary">Unknown</Badge>
                              )}
                            </div>

                            {face.match && face.match.name !== 'Unknown' ? (
                              <div className="space-y-1">
                                <div className="flex justify-between text-xs">
                                  <span>Confidence:</span>
                                  <span>{Math.round((face.match.similarity || 0) * 100)}%</span>
                                </div>
                                <Progress value={(face.match.similarity || 0) * 100} className="h-1.5" />
                                <p className="text-xs text-muted-foreground">Person ID: {face.match.person_id}</p>
                              </div>
                            ) : (
                              <p className="text-xs text-muted-foreground">No registered face detected for this face.</p>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">No faces detected in this frame</p>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
          {!uploadedImage && (
            <>
              {/* Register Card visible on the right so users can register without using main preview */}
              <Card>
                <CardHeader>
                  <CardTitle>Register Person</CardTitle>
                  <CardDescription>Upload an image and provide a name to add to the database</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div
                    className="border-2 border-dashed border-muted-foreground/30 rounded-lg p-4 text-center cursor-pointer"
                    onClick={() => registerFileRef.current?.click()}
                  >
                    <p className="text-sm">Click to select image for registration</p>
                    {registerFileNameLocal && <p className="text-xs text-muted-foreground mt-2">{registerFileNameLocal}</p>}
                  </div>
                  <input ref={registerFileRef} type="file" accept="image/*" onChange={handleRegisterFileUpload} className="hidden" />

                  {registerImageData && (
                    <img src={registerImageData} alt="Register preview" className="w-full h-28 object-contain rounded-md border" />
                  )}

                  <div className="bg-blue-50 border border-blue-200 rounded p-3 mb-2">
                    <p className="text-sm text-blue-900 font-medium">Required fields marked with *</p>
                  </div>

                  <input type="text" placeholder="Name *" value={registerName} onChange={(e) => setRegisterName(e.target.value)} className="w-full px-3 py-2 border rounded-md text-sm" />

                  <div className="grid grid-cols-2 gap-2">
                    <input type="number" min="0" max="150" placeholder="Age (optional)" value={registerAge} onChange={(e) => setRegisterAge(e.target.value)} className="w-full px-3 py-2 border rounded-md text-sm" />
                    <input type="text" placeholder="Case No. *" value={registerCaseNo} onChange={(e) => setRegisterCaseNo(e.target.value)} className="w-full px-3 py-2 border rounded-md text-sm border-red-300" />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Status</label>
                    <Select value={registerStatus} onValueChange={setRegisterStatus}>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="missing">Missing</SelectItem>
                        <SelectItem value="wanted">Wanted</SelectItem>
                        <SelectItem value="found">Found</SelectItem>
                        <SelectItem value="registered">Registered</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex gap-2">
                    <Button onClick={handleRegister} disabled={registerLoading || backendStatus === 'offline'} className="flex-1">{registerLoading ? 'Registering...' : 'Register Person'}</Button>
                    <Button onClick={() => { setRegisterImageData(null); setRegisterFileNameLocal(''); setRegisterName(''); setRegisterAge(''); setRegisterCaseNo(''); setRegisterStatus('missing'); }} variant="outline">Clear</Button>
                  </div>

                  {registerMessage && <div className="text-sm p-2 rounded bg-green-50 text-green-700 border border-green-200">{registerMessage}</div>}
                  {registerError && <div className="text-sm p-2 rounded bg-red-50 text-red-700 border border-red-200"><strong>Error:</strong> {registerError}</div>}
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
