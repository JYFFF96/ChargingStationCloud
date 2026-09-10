const DEVTOOLS_BASE_URL = 'http://127.0.0.1:8000'
const LAN_BASE_URL = 'http://172.20.10.6:8000'

function getBaseUrl() {
  const info = wx.getSystemInfoSync()
  return info.platform === 'devtools' ? DEVTOOLS_BASE_URL : LAN_BASE_URL
}

module.exports = {
  DEVTOOLS_BASE_URL,
  LAN_BASE_URL,
  getBaseUrl
}
