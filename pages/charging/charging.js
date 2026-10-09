Page({
  data: { deviceId: '', charging: true, seconds: 0, energy: '0.00', amount: '0.00' },
  onLoad(query) {
    this.setData({ deviceId: decodeURIComponent(query.deviceId || '') })
    this.timer = setInterval(() => {
      const seconds = this.data.seconds + 1
      this.setData({ seconds, energy: (seconds * 0.002).toFixed(2), amount: (seconds * 0.003).toFixed(2) })
    }, 1000)
  },
  onUnload() { clearInterval(this.timer) },
  stopCharge() {
    clearInterval(this.timer)
    this.setData({ charging: false })
    wx.showToast({ title: '模拟充电已停止', icon: 'none' })
  }
})
