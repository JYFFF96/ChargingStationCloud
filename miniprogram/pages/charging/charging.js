const api = require('../../utils/api')

Page({
  data:{
    pileCode:'',charging:false,soc:0,voltage:'0.0',current:'0.0',power:'0.0',energy:'0.0000',amount:'0.0000',minutes:0,remaining:0,temp:0,statusText:'等待实时数据',faultText:'无',error:''
  },
  onShow(){this.refresh();this.startTimer()},
  onHide(){this.stopTimer()},
  onUnload(){this.stopTimer()},
  startTimer(){this.stopTimer();this.timer=setInterval(()=>this.refresh(),3000)},
  stopTimer(){if(this.timer){clearInterval(this.timer);this.timer=null}},
  async refresh(){
    try{
      const devices=await api.getDevices();const list=(devices.items||[]).filter(x=>x.online);if(!list.length)throw new Error('暂无在线充电桩');
      const pile=this.data.pileCode&&list.find(x=>x.pile_code===this.data.pileCode)?this.data.pileCode:list[0].pile_code;
      const d=await api.getRealtime(pile);const power=((d.voltage_v||0)*(d.current_a||0)/1000).toFixed(1);
      const statusMap={0:'离线',1:'故障',2:'空闲',3:'充电中'};
      this.setData({pileCode:pile,charging:d.work_status===3,soc:d.soc_pct||0,voltage:Number(d.voltage_v||0).toFixed(1),current:Number(d.current_a||0).toFixed(1),power,energy:Number(d.energy_kwh||0).toFixed(4),amount:Number(d.amount_yuan||0).toFixed(4),minutes:d.elapsed_min||0,remaining:d.remaining_min||0,temp:d.gun_temp_c||0,statusText:statusMap[d.work_status]||'未知',faultText:(d.faults||[]).length?`Bit ${d.faults.join(', ')}`:'无故障',error:''})
    }catch(err){this.setData({error:err.message||err.errMsg||'实时数据获取失败'})}
  },
  toggle(){wx.showToast({title:'远程启停接口将在下一版接入',icon:'none'})}
})
