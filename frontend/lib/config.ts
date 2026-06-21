const configuredApiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "/api/backend"

// A trailing slash in production configuration would create paths such as
// `/api/backend//students`, which can bypass Next rewrites or return 404.
export const API_BASE_URL = configuredApiBaseUrl.replace(/\/+$/, "")
