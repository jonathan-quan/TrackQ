import api from './client'

export function register({ username, email, password }) {
  return api.post('/auth/register', { username, email, password })
}

export function login({ email, password }) {
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', password)
  return api.post('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
}

export function me() {
  return api.get('/auth/me')
}
