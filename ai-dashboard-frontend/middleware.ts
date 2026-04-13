import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Public routes that don't require authentication
const publicRoutes = ['/login', '/api']

// Protected routes
const protectedRoutes = ['/', '/dashboard', '/cctv', '/cctv-monitoring', '/database', '/reports', '/settings', '/profile']

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname

  // Allow public routes
  if (publicRoutes.some(route => pathname.startsWith(route))) {
    return NextResponse.next()
  }

  // Check for auth token in cookies
  const authToken = request.cookies.get('auth_token')
  const hasAuth = !!authToken

  // If trying to access protected route without auth, redirect to login
  if (protectedRoutes.some(route => pathname === route || pathname.startsWith(route))) {
    if (!hasAuth) {
      // Redirect to login with return URL
      const loginUrl = new URL('/login', request.url)
      loginUrl.searchParams.set('redirectUrl', pathname)
      return NextResponse.redirect(loginUrl)
    }
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|public).*)',
  ],
}
