import api from './index.js'

export function addParcel(trackingNo, carrier, remark) {
  return api.post('/api/parcel', { trackingNo, carrier, remark }).then((r) => r.data)
}

export function getParcels() {
  return api.get('/api/parcel').then((r) => r.data)
}

export function deleteParcel(id) {
  return api.delete(`/api/parcel/${id}`).then((r) => r.data)
}
