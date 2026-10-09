Page({
  scan() {
    wx.scanCode({
      scanType: ['qrCode'],
      success: res => {
        try {
          const device = require('../../utils/qr').parseQr(res.result)
          wx.navigateTo({ url: '/pages/confirm/confirm?raw=' + encodeURIComponent(device.raw) })
        } catch (e) {
          wx.showToast({ title: e.message || '二维码无效', icon: 'none' })
        }
      }
    })
  }
})
