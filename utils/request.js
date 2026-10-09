const config = require('../config')

function request(options = {}) {
  if (config.mockEnabled) return Promise.resolve({ code: 0, data: options.mockData || {} })
  return new Promise((resolve, reject) => {
    wx.request({
      url: config.apiBaseUrl + options.url,
      method: options.method || 'GET',
      data: options.data || {},
      header: options.header || {},
      success: res => resolve(res.data),
      fail: reject
    })
  })
}

module.exports = { request }
