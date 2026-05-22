import api from './index.js'

export function fetchWeather({ lat, lng, location } = {}) {
  const params = {}
  if (lat != null && lng != null) {
    params.lat = lat
    params.lng = lng
  } else if (location) {
    params.location = location
  }
  return api.get('/api/weather', { params }).then((r) => r.data)
}
