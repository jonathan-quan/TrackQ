import api from './client'

export function addLeg(parlayId, { player_name, player_id, stat_type, line, over_under }) {
  return api.post(`/parlays/${parlayId}/legs`, {
    player_name,
    player_id,
    stat_type,
    line,
    over_under,
  })
}

export function deleteLeg(legId) {
  return api.delete(`/legs/${legId}`)
}
