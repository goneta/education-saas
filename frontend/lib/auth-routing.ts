export type AuthUser = {
  role?: string | null
  school_id?: number | null
  account_type?: string | null
  dashboard_path?: string | null
  recruiter_payment_status?: string | null
  is_external_student?: boolean | null
}

const SCHOOL_ADMIN_ROLES = new Set(["school_admin", "admin"])
const STUDENT_ROLES = new Set(["student", "pupil"])

function normalizedDestination(path: string | null | undefined) {
  if (!path || !path.startsWith("/dashboard")) return "/dashboard"
  return path
}

export function accountTypeForUser(user: AuthUser | null | undefined) {
  if (!user) return "anonymous"
  if (user.account_type) return user.account_type
  if (user.role === "recruiter") return "recruiter"
  if (user.is_external_student) return "external_student"
  if (user.role === "super_admin") return "super_admin"
  if (STUDENT_ROLES.has(user.role || "")) return user.school_id ? "student" : "external_student"
  if (SCHOOL_ADMIN_ROLES.has(user.role || "")) return "school_admin"
  return "staff"
}

export function dashboardPathForUser(user: AuthUser | null | undefined, locale: string) {
  const accountType = accountTypeForUser(user)
  const basePath = accountType === "recruiter"
    ? "/dashboard/emploi-recruteur"
    : accountType === "external_student"
      ? "/dashboard/emploi"
      : normalizedDestination(user?.dashboard_path)
  return `/${locale}${basePath}`
}

export function canAccessDashboardPath(user: AuthUser | null | undefined, pathname: string | null | undefined, locale: string) {
  if (!user || !pathname) return false
  const accountType = accountTypeForUser(user)
  const dashboardPrefix = `/${locale}/dashboard`
  if (!pathname.startsWith(dashboardPrefix)) return true
  const relativePath = pathname.slice(`/${locale}`.length) || "/dashboard"
  if (accountType === "recruiter") {
    return relativePath.startsWith("/dashboard/emploi-recruteur") || relativePath.startsWith("/dashboard/checkout") || relativePath.startsWith("/dashboard/account") || relativePath.startsWith("/dashboard/help")
  }
  if (accountType === "external_student") {
    return (relativePath.startsWith("/dashboard/emploi") && !relativePath.startsWith("/dashboard/emploi-recruteur")) || relativePath.startsWith("/dashboard/account") || relativePath.startsWith("/dashboard/help")
  }
  if (relativePath.startsWith("/dashboard/emploi-recruteur")) return false
  if (relativePath.startsWith("/dashboard/emploi") && accountType !== "student") return false
  return true
}
