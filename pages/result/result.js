Page({
  data:{ record:{} },
  onLoad(query) {
    try { this.setData({ record:JSON.parse(decodeURIComponent(query.record || '{}')) }) } catch (e) {}
  },
  backHome() { wx.switchTab({ url:'/pages/index/index' }) },
  viewRecords() { wx.switchTab({ url:'/pages/records/records' }) }
})