import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const response = NextResponse.json({ success: true, message: 'Logged out' })

    // Clear auth token cookie
    response.cookies.delete('auth_token')

    return response
  } catch (error) {
    return NextResponse.json({ success: false, error: 'Logout failed' }, { status: 500 })
  }
}
