'use client';

import { useState } from 'react';
import NewsletterForm from '@/components/NewsletterForm';

export default function NewsletterPage() {
  const [subscribed, setSubscribed] = useState(false);
  const [error, setError] = useState('');

  const handleSubscribeSuccess = () => {
    setSubscribed(true);
    setError('');
    setTimeout(() => setSubscribed(false), 5000);
  };

  const handleSubscribeError = (errorMsg: string) => {
    setError(errorMsg);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2 text-center">
          Join Our Newsletter
        </h1>
        <p className="text-gray-600 text-center mb-6">
          Get the latest automation tips and educational resources delivered to your inbox.
        </p>

        {subscribed && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-md">
            <p className="text-green-800 text-center">
              ✓ Successfully subscribed! Check your email for the welcome message.
            </p>
          </div>
        )}

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-800 text-center">{error}</p>
          </div>
        )}

        <NewsletterForm
          onSuccess={handleSubscribeSuccess}
          onError={handleSubscribeError}
        />

        <p className="text-xs text-gray-500 text-center mt-6">
          We respect your privacy. Unsubscribe at any time.
        </p>
      </div>
    </div>
  );
}
