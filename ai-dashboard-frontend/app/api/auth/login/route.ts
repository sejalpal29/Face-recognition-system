import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const { email } = await request.json()

    // Create response
    const response = NextResponse.json({ success: true, message: 'Logged in' })

    // Set HTTPOnly authentication cookie (valid for 7 days)
    response.cookies.set('auth_token', email, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 7 * 24 * 60 * 60 // 7 days
    })

    return response
  } catch (error) {
    return NextResponse.json({ success: false, error: 'Login failed' }, { status: 500 })
  }
}
