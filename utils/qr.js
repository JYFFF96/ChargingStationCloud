function parseQr(raw) {
  const text = String(raw || '').trim()
  if (!text) throw new Error('二维码内容为空')
  return { raw: text, deviceId: text, gunId: '' }
}

module.exports = { parseQr }
