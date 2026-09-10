const { getBaseUrl } = require('../config')

function request(path, options = {}) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${getBaseUrl()}${path}`,
      method: options.method || 'GET',
      data: options.data || {},
      timeout: 5000,
      success: res => {
        if (res.statusCode >= 200 && res.statusCode < 300) resolve(res.data)
        else reject(new Error(`HTTP ${res.statusCode}`))
      },
      fail: reject
    })
  })
}

function getDevices() {
  return request('/api/devices')
}

module.exports = {
  request,
  getDevices
}
