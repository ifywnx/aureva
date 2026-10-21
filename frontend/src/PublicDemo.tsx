import {useEffect, useState, type FormEvent} from 'react';
import {
 ArrowLeft, ArrowRight, CheckCircle2, ClipboardCheck, FileCheck2,
 FileText, HeartHandshake, LayoutDashboard, LockKeyhole, Plus,
 RotateCcw, ShieldCheck, Sparkles, AlertTriangle
} from 'lucide-react';
import './PublicDemo.css';

/**
 * Public classroom sandbox: local browser state ONLY.
 *
 * No privileged production accounts, database writes, paid AI API calls,
 * blockchain transactions or real payments are made from this component.
 * This intentionally differs from the protected Preview 3-role demo, which
 * exercises real server endpoints against its isolated PostgreSQL schema.
 */
type Role = 'donor' | 'manager' | 'approver';
type Status = 'pending' | 'confirmed' | 'approved' | 'rejected';
type Campaign = {id:string;title:string;location:string;target:number};
type Donation = {id:string;campaignId:string;amount:number;status:Status};
type Expense = {id:string;campaignId:string;amount:number;purpose:string;vendor:string;status:Status;receiptName:string;invoiceTotal:number|null;reviewed:boolean;warnings:string[];reason:string;digest:string};
type DemoState = {campaigns:Campaign[];donations:Donation[];expenses:Expense[];activity:string[]};
const STORAGE_KEY='aureva:public-classroom-demo:v1';
const MAX_AMOUNT=1_000_000_000_000;
const currency=(value:number)=>new Intl.NumberFormat('vi-VN',{style:'currency',currency:'VND',maximumFractionDigits:0}).format(value);
const makeId=()=>Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,8);
const roles:{id:Role;name:string;description:string}[]=[
 {id:'donor',name:'Người đóng góp',description:'Gửi thông tin đóng góp giả định'},
 {id:'manager',name:'Người quản lý',description:'Đối soát và đề xuất khoản chi'},
 {id:'approver',name:'Người phê duyệt',description:'Đọc hồ sơ và ra quyết định'}
];
const initialData=():DemoState=>({
 campaigns:[{id:'example-1',title:'[DEMO] Hỗ trợ người dân vùng lũ',location:'Miền Trung (dữ liệu giả định)',target:20_000_000}],
 donations:[{id:'seed-donation',campaignId:'example-1',amount:1_000_000,status:'confirmed'}],
 expenses:[],
 activity:['Đã tạo dữ liệu khởi đầu giả định để cả nhóm luyện quy trình.']
});
function restore():DemoState {
 try {
  const raw=sessionStorage.getItem(STORAGE_KEY);
  if(raw){
   const value:unknown=JSON.parse(raw);
   if(value && typeof value==='object' && 'campaigns' in value && 'donations' in value && 'expenses' in value && 'activity' in value){
    const data=value as DemoState;
    if(Array.isArray(data.campaigns)&&Array.isArray(data.donations)&&Array.isArray(data.expenses)&&Array.isArray(data.activity))return data;
   }
  }
 }catch{ /* Disabled storage simply starts a fresh, local-only sandbox. */ }
 return initialData();
}
async function sha256(value:string):Promise<string> {
 const bytes=new TextEncoder().encode(value);
 const hash=await crypto.subtle.digest('SHA-256',bytes);
 return Array.from(new Uint8Array(hash)).map(b=>b.toString(16).padStart(2,'0')).join('');
}
function totals(data:DemoState, campaignId:string){
 const raised=data.donations.filter(d=>d.campaignId===campaignId&&d.status==='confirmed').reduce((sum,d)=>sum+d.amount,0);
 const spent=data.expenses.filter(e=>e.campaignId===campaignId&&e.status==='approved').reduce((sum,e)=>sum+e.amount,0);
 return {raised,spent,available:raised-spent};
}
function validAmount(value:number):boolean{return Number.isSafeInteger(value)&&value>0&&value<=MAX_AMOUNT;}

export function PublicDemo(){
 const [role,setRole]=useState<Role>('manager');
 const [data,setData]=useState<DemoState>(restore);
 const [message,setMessage]=useState('');
 const [selectedId,setSelectedId]=useState('example-1');
 const [reviewing,setReviewing]=useState<string|null>(null);
 const [decisionReason,setDecisionReason]=useState('');
 const [warningAcknowledged,setWarningAcknowledged]=useState(false);
 useEffect(()=>{try{sessionStorage.setItem(STORAGE_KEY,JSON.stringify(data));}catch{/* local-only */}},[data]);
 const selected=data.campaigns.find(c=>c.id===selectedId)??data.campaigns[0];
 const selectedCampaignId=selected?.id??'';
 const amounts=totals(data,selectedCampaignId);
 const donations=data.donations.filter(d=>d.campaignId===selectedCampaignId);
 const expenses=data.expenses.filter(e=>e.campaignId===selectedCampaignId);
 function update(next:DemoState,note:string){
  setData({...next,activity:[note,...next.activity].slice(0,25)});
  setMessage(note);
 }
 function addCampaign(event:FormEvent<HTMLFormElement>){
  event.preventDefault();const f=new FormData(event.currentTarget);
  const title=String(f.get('title')??'').trim();
  const location=String(f.get('location')??'').trim();
  const target=Number(f.get('target'));
  if(title.length<5||location.length<2||!validAmount(target)){setMessage('Vui lòng nhập tên, địa điểm và mục tiêu hợp lệ.');return;}
  const campaign={id:makeId(),title:'[DEMO] '+title,location,target};
  update({...data,campaigns:[...data.campaigns,campaign]},'Đã tạo chiến dịch DEMO: '+title);
  setSelectedId(campaign.id);
  event.currentTarget.reset();
 }
 function addDonation(event:FormEvent<HTMLFormElement>){
  event.preventDefault();const amount=Number(new FormData(event.currentTarget).get('amount'));
  if(!validAmount(amount)){setMessage('Số tiền mô phỏng phải là số nguyên dương hợp lệ.');return;}
  update({...data,donations:[...data.donations,{id:makeId(),campaignId:selectedCampaignId,amount,status:'pending'}]},
    'Donor đã ghi nhận '+currency(amount)+' (mô phỏng, chưa có chuyển tiền).');
  event.currentTarget.reset();
 }
 function decideDonation(id:string,status:'confirmed'|'rejected'){
  const donation=donations.find(x=>x.id===id);
  if(!donation||donation.status!=='pending')return;
  update({...data,donations:data.donations.map(d=>d.id===id?{...d,status}:d)},
   'Manager '+(status==='confirmed'?'xác nhận đối soát GIẢ ĐỊNH':'từ chối')+' khoản '+currency(donation.amount)+'.');
 }
 function addExpense(event:FormEvent<HTMLFormElement>){
  event.preventDefault();const f=new FormData(event.currentTarget);
  const amount=Number(f.get('amount'));
  const purpose=String(f.get('purpose')??'').trim();
  const vendor=String(f.get('vendor')??'').trim();
  if(!validAmount(amount)||purpose.length<5||vendor.length<2){setMessage('Thông tin khoản chi chưa hợp lệ.');return;}
  const item:Expense={id:makeId(),campaignId:selectedCampaignId,amount,purpose,vendor,status:'pending',receiptName:'',invoiceTotal:null,reviewed:false,warnings:[],reason:'',digest:''};
  update({...data,expenses:[...data.expenses,item]},'Manager đề xuất khoản chi '+currency(amount)+'; đang chờ chứng từ.');
  event.currentTarget.reset();
 }
 function reviewExpense(event:FormEvent<HTMLFormElement>,item:Expense){
  event.preventDefault();const f=new FormData(event.currentTarget);
  const file=f.get('receipt');
  const total=Number(f.get('invoiceTotal'));
  if(!(file instanceof File)||file.size===0||file.size>2_000_000||!['image/jpeg','image/png','application/pdf'].includes(file.type)){
   setMessage('Hãy chọn ảnh JPG/PNG hoặc PDF thử nghiệm (tối đa 2 MB).');return;
  }
  if(!validAmount(total)){setMessage('Nhập số tiền giả định thể hiện trên hóa đơn.');return;}
  const warnings=item.amount===total?[]:['Chênh lệch '+currency(Math.abs(item.amount-total))+' giữa khoản chi và số tiền nhập từ hóa đơn.'];
  const replacement={...item,receiptName:file.name,invoiceTotal:total,reviewed:true,warnings};
  update({...data,expenses:data.expenses.map(e=>e.id===item.id?replacement:e)},
   'Đã đối chiếu chứng từ bằng QUY TẮC GIẢ LẬP (không sử dụng AI thật).');
  setReviewing(null);
 }
 async function decideExpense(item:Expense,status:'approved'|'rejected'){
  if(item.status!=='pending')return;
  const reason=decisionReason.trim();
  if(reason.length<5){setMessage('Lý do quyết định cần ít nhất 5 ký tự.');return;}
  if(status==='approved'){
   if(!item.reviewed){setMessage('Cần đối chiếu chứng từ trước khi phê duyệt.');return;}
   if(item.amount>totals(data,item.campaignId).available){setMessage('Từ chối duyệt: khoản chi lớn hơn số dư đã đối soát.');return;}
   if(item.warnings.length&&(!warningAcknowledged||reason.length<15)){setMessage('Có cảnh báo: hãy xác nhận đã kiểm tra và giải trình ít nhất 15 ký tự.');return;}
  }
  // The digest demonstrates hashing; it is NOT broadcast to Sepolia.
  const payload=JSON.stringify({id:item.id,campaignId:item.campaignId,amount:item.amount,status,reason,invoiceTotal:item.invoiceTotal,receiptName:item.receiptName});
  const digest=await sha256(payload);
  update({...data,expenses:data.expenses.map(e=>e.id===item.id?{...e,status,reason,digest}:e)},
   'Approver đã '+(status==='approved'?'duyệt':'từ chối')+' khoản chi DEMO; chỉ tạo SHA-256 cục bộ, không ghi Blockchain.');
  setReviewing(null);setDecisionReason('');setWarningAcknowledged(false);
 }
 function reset(){
  if(!window.confirm('Xóa dữ liệu DEMO của riêng tab này và khôi phục mẫu ban đầu?'))return;
  const initial=initialData();setData(initial);setRole('manager');setSelectedId('example-1');setMessage('Đã đặt lại dữ liệu DEMO của tab này.');
  try{sessionStorage.setItem(STORAGE_KEY,JSON.stringify(initial));}catch{/* local-only */}
 }
 return <div className="pd-root">
  <header className="pd-header">
   <div className="pd-brand"><span className="pd-logo"><HeartHandshake size={23}/></span><span><strong>AUREVA <em>DEMO</em></strong><small>Phòng thực hành quyên góp minh bạch</small></span></div>
   <div className="pd-header-actions"><span className="pd-safe"><LockKeyhole size={15}/> Tách biệt Production</span><button className="pd-ghost" onClick={reset}><RotateCcw size={15}/> Đặt lại</button><a className="pd-exit" href="/"><ArrowLeft size={16}/> Website chính</a></div>
  </header>
  <main className="pd-main">
   <section className="pd-intro">
    <div><span className="pd-kicker"><Sparkles size={15}/> CHẾ ĐỘ TRẢI NGHIỆM DÀNH CHO NHÓM</span><h1>Thử đủ 3 vai trò.<br/><span>Hiểu trọn một quy trình.</span></h1>
    <p>Chuyển vai trò chỉ bằng một nút. Thao tác thu–chi, dữ liệu chiến dịch và mã băm đều là mô phỏng ngay trong trình duyệt của bạn.</p></div>
    <div className="pd-notice"><ShieldCheck size={27}/><b>Không giao dịch thật</b><span>Không ghi Supabase Production · Không thanh toán · Không gọi AI có phí · Không ký Sepolia. Mỗi tab có dữ liệu DEMO riêng.</span></div>
   </section>
   <section className="pd-role-section" aria-label="Chuyển 3 tài khoản DEMO">
    <div className="pd-section-title"><span>01 / TÀI KHOẢN MÔ PHỎNG</span><h2>Chọn vai trò để thao tác</h2></div>
    <div className="pd-roles">
     {roles.map(r=><button key={r.id} onClick={()=>{setRole(r.id);setMessage('Đã chuyển sang vai trò DEMO: '+r.name);setReviewing(null);}} className={'pd-role '+(role===r.id?'selected':'')} aria-pressed={role===r.id}>
      <span className="pd-role-icon">{r.id==='donor'?<HeartHandshake size={23}/>:r.id==='manager'?<LayoutDashboard size={23}/>:<ShieldCheck size={23}/>}</span>
      <span><strong>{r.name}</strong><small>{r.description}</small></span>{role===r.id&&<CheckCircle2 size={19} className="pd-check"/>}
     </button>)}
    </div>
   </section>
   <div className="pd-layout">
    <div className="pd-primary">
     {message&&<div className="pd-flash" role="status">{message}</div>}
     <section className="pd-panel">
      <div className="pd-section-title"><span>02 / CHIẾN DỊCH</span><h2>Quỹ cứu trợ thử nghiệm</h2></div>
      <label className="pd-field">Đang làm việc với chiến dịch
       <select value={selectedCampaignId} onChange={e=>setSelectedId(e.target.value)} aria-label="Chọn chiến dịch DEMO">{data.campaigns.map(c=><option value={c.id} key={c.id}>{c.title}</option>)}</select>
      </label>
      <p className="pd-context">Địa bàn: {selected?.location} · Mục tiêu: {currency(selected?.target??0)}</p>
      <div className="pd-stats"><div><small>Đã đối soát (DEMO)</small><strong>{currency(amounts.raised)}</strong></div><div><small>Khoản chi đã duyệt</small><strong>{currency(amounts.spent)}</strong></div><div><small>Số dư tính toán</small><strong>{currency(amounts.available)}</strong></div></div>
      {role==='manager'&&<details className="pd-details"><summary><Plus size={16}/> Tạo chiến dịch DEMO mới</summary><form onSubmit={addCampaign} className="pd-form">
       <label>Tên chiến dịch<input name="title" required minLength={5} placeholder="Ví dụ: Hỗ trợ học sinh" /></label>
       <label>Khu vực<input name="location" required minLength={2} placeholder="Ví dụ: Quảng Ninh"/></label>
       <label>Mục tiêu (VND)<input type="number" name="target" min="1" max={MAX_AMOUNT} step="1" required /></label><button className="pd-button">Tạo chiến dịch</button>
      </form></details>}
     </section>
     {role==='donor'&&<section className="pd-panel"><div className="pd-section-title"><span>03 / NGƯỜI ĐÓNG GÓP</span><h2>Ghi nhận khoản ủng hộ mô phỏng</h2></div>
      <p>Khoản bạn nhập ban đầu có trạng thái <b>Chờ đối soát</b>. Hãy chuyển sang Manager để xác nhận.</p>
      <form className="pd-form pd-inline" onSubmit={addDonation}><label>Số tiền giả định (VND)<input name="amount" type="number" min="1" step="1" max={MAX_AMOUNT} required placeholder="500000"/></label><button className="pd-button"><HeartHandshake size={17}/> Ghi nhận DEMO</button></form>
     </section>}
     {role==='manager'&&<section className="pd-panel"><div className="pd-section-title"><span>03 / ĐỐI SOÁT THU</span><h2>Chờ xác nhận đóng góp</h2></div>
      {donations.filter(d=>d.status==='pending').length===0?<div className="pd-empty">Chưa có đóng góp chờ xử lý. Chuyển sang Donor để tạo một khoản mới.</div>:
      donations.filter(d=>d.status==='pending').map(d=><div className="pd-record" key={d.id}><div><strong>{currency(d.amount)}</strong><small>Chờ đối soát · tiền giả định</small></div><div className="pd-actions"><button className="pd-button" onClick={()=>decideDonation(d.id,'confirmed')}>Xác nhận DEMO</button><button className="pd-ghost" onClick={()=>decideDonation(d.id,'rejected')}>Từ chối</button></div></div>)}
     </section>}
     {role==='manager'&&<section className="pd-panel"><div className="pd-section-title"><span>04 / ĐỀ XUẤT CHI</span><h2>Tạo hồ sơ khoản chi</h2></div><p>Tạo khoản chi, sau đó tải chứng từ và nhập số tiền trên hóa đơn để mô phỏng bước đối chiếu.</p>
      <form className="pd-form" onSubmit={addExpense}>
       <label>Nội dung khoản chi<input name="purpose" required minLength={5} placeholder="Mua nhu yếu phẩm cứu trợ"/></label>
       <label>Nhà cung cấp<input name="vendor" required minLength={2} placeholder="Cửa hàng thực phẩm mẫu"/></label>
       <label>Số tiền (VND)<input name="amount" type="number" min="1" step="1" max={MAX_AMOUNT} required placeholder="200000"/></label>
       <button className="pd-button"><Plus size={16}/> Gửi chờ phê duyệt</button>
      </form>
     </section>}
     {(role==='manager'||role==='approver')&&<section className="pd-panel"><div className="pd-section-title"><span>{role==='manager'?'05 / CHỨNG TỪ':'04 / PHÊ DUYỆT'}</span><h2>{role==='manager'?'Đối chiếu chứng từ DEMO':'Quyết định khoản chi'}</h2></div>
      {expenses.length===0?<div className="pd-empty">Chưa có khoản chi. Chuyển sang Manager để tạo hồ sơ.</div>:expenses.map(item=><article className="pd-expense" key={item.id}>
       <div className="pd-record"><div><strong>{item.purpose}</strong><small>{item.vendor} · {currency(item.amount)}</small></div><span className={'pd-status '+item.status}>{item.status==='pending'?'Chờ phê duyệt':item.status==='approved'?'Đã duyệt':'Từ chối'}</span></div>
       {item.reviewed&&<div className="pd-receipt"><FileCheck2 size={17}/><div><strong>Đã đối chiếu giả lập</strong><small>File: {item.receiptName} · Số tiền nhập tay: {currency(item.invoiceTotal??0)}</small></div></div>}
       {item.warnings.length>0&&item.warnings.map(w=><div className="pd-warning" key={w}><AlertTriangle size={16}/>{w}</div>)}
       {role==='manager'&&item.status==='pending'&&!item.reviewed&&<><button className="pd-ghost" onClick={()=>setReviewing(reviewing===item.id?null:item.id)}><FileText size={17}/> Thêm chứng từ và đối chiếu</button>
        {reviewing===item.id&&<form className="pd-form" onSubmit={e=>reviewExpense(e,item)}>
         <label>Chứng từ mẫu<input name="receipt" type="file" accept="image/jpeg,image/png,application/pdf" required/></label>
         <label>Số tiền trên chứng từ (VND, nhập tay)<input name="invoiceTotal" type="number" min="1" step="1" max={MAX_AMOUNT} required/></label>
         <p className="pd-disclaimer">Đây là phép so sánh số do bạn nhập, KHÔNG phải kết quả phân tích AI hay chứng nhận hóa đơn.</p><button className="pd-button">Đối chiếu mô phỏng</button>
        </form>}
       </>}
       {role==='approver'&&item.status==='pending'&&<div className="pd-decision">
        <label>Lý do duyệt hoặc từ chối<textarea value={reviewing===item.id?decisionReason:''} onFocus={()=>{if(reviewing!==item.id){setReviewing(item.id);setDecisionReason('');setWarningAcknowledged(false)}}} onChange={e=>setDecisionReason(e.target.value)} placeholder="Tôi đã kiểm tra chứng từ mẫu và đối chiếu số tiền..." rows={3}/></label>
        {item.warnings.length>0&&<label className="pd-check-field"><input type="checkbox" checked={reviewing===item.id&&warningAcknowledged} onChange={e=>{setReviewing(item.id);setWarningAcknowledged(e.target.checked)}}/> Tôi đã xem cảnh báo và ghi giải trình ít nhất 15 ký tự.</label>}
        <div className="pd-actions"><button className="pd-button" disabled={!item.reviewed} onClick={()=>void decideExpense(item,'approved')}><ClipboardCheck size={16}/> Phê duyệt DEMO</button><button className="pd-ghost" onClick={()=>void decideExpense(item,'rejected')}>Từ chối</button></div>
        {!item.reviewed&&<small>Manager phải đối chiếu chứng từ trước khi có thể duyệt.</small>}
       </div>}
       {item.status!=='pending'&&<div className="pd-hash"><b>SHA-256 mô phỏng trên trình duyệt</b><code>{item.digest}</code><small>Chưa gửi giao dịch lên Sepolia. Không có TX hash hay chứng thực Blockchain thật.</small><p>Lý do: {item.reason}</p></div>}
      </article>)}
     </section>}
     {role==='donor'&&<section className="pd-panel"><div className="pd-section-title"><span>04 / LỊCH SỬ</span><h2>Các đóng góp giả định</h2></div>
       {donations.map(d=><div key={d.id} className="pd-record"><strong>{currency(d.amount)}</strong><span className={'pd-status '+d.status}>{d.status==='confirmed'?'Đã đối soát':d.status==='rejected'?'Từ chối':'Chờ đối soát'}</span></div>)}
     </section>}
    </div>
    <aside className="pd-aside">
     <div className="pd-aside-head"><Sparkles size={20}/><strong>Luồng demo 6 bước</strong></div>
     <ol className="pd-steps"><li><b>Manager</b><span>Tạo chiến dịch thử</span></li><li><b>Donor</b><span>Ghi nhận khoản đóng góp</span></li><li><b>Manager</b><span>Xác nhận đối soát giả định</span></li><li><b>Manager</b><span>Đề xuất chi và đối chiếu chứng từ</span></li><li><b>Approver</b><span>Duyệt hoặc từ chối</span></li><li><b>Cả nhóm</b><span>Kiểm tra số dư và mã SHA-256 cục bộ</span></li></ol>
     <p className="pd-aside-note">Muốn kiểm tra AI thật hoặc giao dịch Sepolia thật, dùng môi trường kiểm thử được cấp quyền riêng; bản công khai này không tự nhận là đã thực hiện các bước đó.</p>
     <div className="pd-section-title"><span>NHẬT KÝ DEMO</span></div>
     <div className="pd-activity">{data.activity.slice(0,8).map((note,i)=><p key={i}>{note}</p>)}</div>
     <a className="pd-aside-link" href="/">Về AUREVA chính <ArrowRight size={15}/></a>
    </aside>
   </div>
  </main>
 </div>;
}
