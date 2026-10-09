const { parseQr } = require('../../utils/qr')
Page({
  goConfirm(raw) {
    try {
      const device = parseQr(raw)
      wx.navigateTo({ url: '/pages/confirm/confirm?raw=' + encodeURIComponent(device.raw) })
    } catch (e) {
      wx.showToast({ title: e.message || '二维码无效', icon: 'none' })
    }
  },
  scan() {
    wx.scanCode({
      scanType: ['qrCode'],
      success: res => this.goConfirm(res.result),
      fail: err => {
        if (!String(err.errMsg || '').includes('cancel')) wx.showToast({ title: '扫码失败，请重试', icon: 'none' })
      }
    })
  },
  mockScan() { this.goConfirm('CS-DEMO-0001') }
})