function parseQr(raw) {
  const text = String(raw || '').trim()
  if (!text) throw new Error('二维码内容为空')
  let deviceId = text
  let gunId = ''
  try {
    if (/^https?:\/\//i.test(text)) {
      const query = text.split('?')[1] || ''
      const params = {}
      query.split('&').forEach(x => {
        const pair = x.split('=')
        if (pair[0]) params[decodeURIComponent(pair[0])] = decodeURIComponent(pair[1] || '')
      })
      deviceId = params.deviceId || params.pileId || params.device || text
      gunId = params.gunId || params.gun || ''
    } else if (text.includes('|')) {
      const parts = text.split('|')
      deviceId = parts[0] || text
      gunId = parts[1] || ''
    }
  } catch (e) {}
  return { raw:text, deviceId, gunId }
}
module.exports = { parseQr }