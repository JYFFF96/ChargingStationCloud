const { parseQr } = require('../../utils/qr')
Page({
  data: { device: {}, ready: false },
  onLoad(query) {
    try {
      const device = parseQr(decodeURIComponent(query.raw || ''))
      this.setData({ device, ready: true })
    } catch (e) {
      wx.showModal({ title: '二维码无效', content: e.message || '无法解析二维码', showCancel: false })
    }
  },
  startCharge() {
    if (!this.data.ready) return
    wx.navigateTo({ url: '/pages/charging/charging?deviceId=' + encodeURIComponent(this.data.device.deviceId) })
  }
})
