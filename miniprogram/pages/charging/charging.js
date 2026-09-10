Page({
  data:{charging:false,soc:46,voltage:'399.0',current:'99.9',power:'39.9',energy:'23.4567',amount:'30.3838',minutes:35},
  toggle(){this.setData({charging:!this.data.charging});wx.showToast({title:this.data.charging?'已开始充电':'已停止充电',icon:'none'})}
})
