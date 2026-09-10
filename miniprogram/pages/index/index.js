const api = require('../../utils/api')

Page({
  data: { loading:false, error:'', devices:[], onlineCount:0, chargingCount:0, faultCount:0 },
  onLoad(){ this.loadDevices() },
  onShow(){ this.loadDevices() },
  onPullDownRefresh(){ this.loadDevices().finally(()=>wx.stopPullDownRefresh()) },
  async loadDevices(){
    this.setData({loading:true,error:''})
    try{
      const data=await api.getDevices(), devices=data.items||[]
      this.setData({devices,onlineCount:devices.filter(x=>x.online).length,chargingCount:0,faultCount:0})
    }catch(err){this.setData({error:err.errMsg||err.message||'请求失败'})}
    finally{this.setData({loading:false})}
  },
  goScan(){ wx.switchTab({url:'/pages/scan/scan'}) },
  goCharging(){ wx.switchTab({url:'/pages/charging/charging'}) }
})
