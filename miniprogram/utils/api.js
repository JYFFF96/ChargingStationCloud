const { getBaseUrl } = require('../config')

function request(path, options = {}) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${getBaseUrl()}${path}`,
      method: options.method || 'GET',
      data: options.data || {},
      timeout: 5000,
      header: {'content-type':'application/json'},
      success: res => {
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data)
        else reject(new Error((res.data && res.data.detail) || `HTTP ${res.statusCode}`))
      },
      fail: reject
    })
  })
}

const getDevices = () => request('/api/devices')
const getRealtime = pileCode => request(`/api/devices/${pileCode}/realtime`)
const startCharge = data => request('/api/charge/start',{method:'POST',data})
const stopCharge = data => request('/api/charge/stop',{method:'POST',data})
const getTransactions = () => request('/api/transactions')
const getTariff = () => request('/api/tariff')

module.exports = {request,getDevices,getRealtime,startCharge,stopCharge,getTransactions,getTariff}
