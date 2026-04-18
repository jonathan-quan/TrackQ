import api from './client'

export function listParlays() {
  return api.get('/parlays')
}

export function getParlay(id) {
  return api.get(`/parlays/${id}`)
}

export function createParlay({ name, game_date }) {
  return api.post('/parlays', { name, game_date })
}

export function deleteParlay(id) {
  return api.delete(`/parlays/${id}`)
}

export function refreshParlay(id) {
  // The backend fans out to nba.com; cap the request so the UI can surface
  // a failure instead of leaving the button stuck on "Refreshing…" forever.
  return api.post(`/parlays/${id}/refresh`, undefined, { timeout: 45_000 })
}
