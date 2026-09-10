Page({
  data:{result:'',pileCode:'',gunNo:'01'},
  parse(text){
    const s=String(text||'').trim();let pile='',gun='01';
    const m=s.match(/zxkcharge:\/\/pile\/(\d{14})\/(\d{2})/i);
    if(m){pile=m[1];gun=m[2]}else{const d=s.replace(/\D/g,'');if(d.length>=14){pile=d.slice(0,14);gun=d.length>=16?d.slice(14,16):'01'}}
    if(!pile){wx.showToast({title:'无法识别桩编号',icon:'none'});return}
    this.setData({result:s,pileCode:pile,gunNo:gun});wx.setStorageSync('chargeTarget',{pileCode:pile,gunNo:gun});wx.showToast({title:'已识别充电桩',icon:'success'})
  },
  scan(){wx.scanCode({success:r=>this.parse(r.result),fail:()=>wx.showToast({title:'已取消扫码',icon:'none'})})},
  goCharge(){if(!this.data.pileCode){wx.showToast({title:'请先扫码',icon:'none'});return}wx.switchTab({url:'/pages/charging/charging'})}
})
