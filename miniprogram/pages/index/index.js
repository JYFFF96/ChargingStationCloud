const api = require('../../utils/api')

Page({
  data: {
    loading: false,
    error: '',
    devices: []
  },

  onLoad() {
    this.loadDevices()
  },

  onPullDownRefresh() {
    this.loadDevices().finally(() => wx.stopPullDownRefresh())
  },

  async loadDevices() {
    this.setData({ loading: true, error: '' })
    try {
      const data = await api.getDevices()
      this.setData({ devices: data.items || [] })
    } catch (err) {
      this.setData({ error: err.errMsg || err.message || '请求失败' })
    } finally {
      this.setData({ loading: false })
    }
  }
})
