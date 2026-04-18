import api from './client'

export function searchPlayers(name, limit = 10) {
  return api.get('/search/nba', { params: { name, limit } })
}
