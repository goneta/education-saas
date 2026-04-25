import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Validate email
    if (!body.email) {
      return NextResponse.json(
        { detail: 'Email is required' },
        { status: 400 }
      );
    }

    // Call backend newsletter endpoint
    const response = await fetch(`${BACKEND_URL}/api/newsletter/subscribe`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: body.email,
        firstName: body.firstName,
        tags: body.tags,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(
        { detail: errorData.detail || 'Failed to subscribe' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Newsletter subscription error:', error);
    return NextResponse.json(
      { detail: 'An error occurred while processing your subscription' },
      { status: 500 }
    );
  }
}

export async function GET() {
  return NextResponse.json({ message: 'Newsletter endpoint' });
}
