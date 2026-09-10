const api=require('../../utils/api')
Page({
  data:{items:[],loading:false,error:''},
  onShow(){this.load()},
  async load(){this.setData({loading:true,error:''});try{const d=await api.getTransactions();this.setData({items:d.items||[]})}catch(e){this.setData({error:e.message||'获取记录失败'})}finally{this.setData({loading:false})}}
})
