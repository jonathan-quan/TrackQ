export function apiErrorMessage(err, fallback = 'Something went wrong') {
  if (err?.response) {
    const detail = err.response.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
    return `${fallback} (${err.response.status})`
  }
  if (err?.request) {
    return 'Cannot reach server — is the backend running on localhost:8000?'
  }
  return err?.message || fallback
}
