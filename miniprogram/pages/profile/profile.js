Page({
  data:{userName:'实训用户',balance:'1000.00'},
  goRecords(){wx.navigateTo({url:'/pages/records/records'})},
  placeholder(e){wx.showToast({title:(e.currentTarget.dataset.name||'功能')+'暂保留为RC1界面',icon:'none'})}
})
