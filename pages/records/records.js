Page({
  data:{ records:[] },
  onShow(){ this.setData({ records:wx.getStorageSync('chargeRecords') || [] }) },
  clearRecords(){
    if (!this.data.records.length) return
    wx.showModal({ title:'清空记录', content:'确认清空本地模拟充电记录吗？', success:res=>{
      if (res.confirm) { wx.removeStorageSync('chargeRecords'); this.setData({records:[]}) }
    }})
  }
})