Page({
  data:{result:''},
  scan(){
    wx.scanCode({success:r=>{this.setData({result:r.result||''});wx.showToast({title:'扫码成功',icon:'success'})},fail:()=>wx.showToast({title:'已取消扫码',icon:'none'})})
  }
})
