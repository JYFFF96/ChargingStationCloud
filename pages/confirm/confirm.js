const { parseQr } = require('../../utils/qr')
Page({
  data: { device: {}, ready: false, starting: false, price: '1.20', serviceFee: '0.30' },
  onLoad(query) {
    try {
      const device = parseQr(decodeURIComponent(query.raw || ''))
      this.setData({ device, ready: true })
    } catch (e) {
      wx.showModal({ title: '二维码无效', content: e.message || '无法解析二维码', showCancel: false })
    }
  },
  startCharge() {
    if (!this.data.ready || this.data.starting) return
    this.setData({ starting: true })
    wx.showLoading({ title: '正在启动' })
    setTimeout(() => {
      wx.hideLoading()
      wx.navigateTo({
        url: '/pages/charging/charging?deviceId=' + encodeURIComponent(this.data.device.deviceId) +
             '&gunId=' + encodeURIComponent(this.data.device.gunId || '01')
      })
      this.setData({ starting: false })
    }, 700)
  }
})