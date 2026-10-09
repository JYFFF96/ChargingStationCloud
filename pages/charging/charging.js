function pad(n) { return String(n).padStart(2, '0') }
Page({
  data: { deviceId:'', gunId:'01', charging:true, seconds:0, duration:'00:00', energy:'0.00', amount:'0.00', power:'7.0', voltage:'220', current:'31.8' },
  onLoad(query) {
    this.setData({ deviceId:decodeURIComponent(query.deviceId || ''), gunId:decodeURIComponent(query.gunId || '01') })
    this.timer = setInterval(() => {
      const seconds = this.data.seconds + 1
      this.setData({
        seconds,
        duration: pad(Math.floor(seconds / 60)) + ':' + pad(seconds % 60),
        energy: (seconds * 0.002).toFixed(2),
        amount: (seconds * 0.003).toFixed(2)
      })
    }, 1000)
  },
  onUnload() { clearInterval(this.timer) },
  stopCharge() {
    wx.showModal({
      title:'结束充电',
      content:'确认停止本次充电吗？',
      confirmText:'停止充电',
      confirmColor:'#d84a42',
      success: res => {
        if (!res.confirm) return
        clearInterval(this.timer)
        const record = {
          id:'MOCK-' + Date.now(),
          deviceId:this.data.deviceId,
          gunId:this.data.gunId,
          duration:this.data.duration,
          energy:this.data.energy,
          amount:this.data.amount,
          time:this.formatTime(new Date())
        }
        const records = wx.getStorageSync('chargeRecords') || []
        wx.setStorageSync('chargeRecords', [record].concat(records).slice(0, 20))
        wx.redirectTo({ url:'/pages/result/result?record=' + encodeURIComponent(JSON.stringify(record)) })
      }
    })
  },
  formatTime(d) {
    return d.getFullYear() + '-' + pad(d.getMonth()+1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes())
  }
})