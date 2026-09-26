'use client';

import { useEffect } from 'react';
import * as Sentry from '@sentry/nextjs';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);

  return (
    <html lang="fr">
      <body>
        <main style={{ margin: '5rem auto', maxWidth: '32rem', padding: '0 1rem', fontFamily: 'sans-serif' }}>
          <h1>Une erreur est survenue</h1>
          <p>Veuillez recharger la page ou r&eacute;essayer dans quelques instants.</p>
          <button type="button" onClick={reset}>R&eacute;essayer</button>
        </main>
      </body>
    </html>
  );
}
