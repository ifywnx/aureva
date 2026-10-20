import {useState,type FormEvent} from 'react';
import {Activity, ArrowRight, ArrowUpRight, CheckCircle2, CircleAlert, ClipboardCheck, FileClock, FileText, HeartHandshake, LayoutDashboard, Plus, SearchCheck, ShieldCheck, Wallet} from 'lucide-react';
import {ContributionTrail} from './AurevaNavigation';
import {EvidencePanel,type DocumentInfo,type Attestation} from './Evidence';

type Campaign={id:string;title:string;owner_id:string;raised:number;spent:number;location:string};
type RecordItem={id:string;campaign_id:string;campaign_title:string;amount:number;status:string;reference?:string;purpose?:string;vendor?:string;reason?:string;created:string;document?:DocumentInfo|null;attestation?:Attestation|null};
type User={id:string;name:string;role:'donor'|'manager'|'approver'};
const money=(n:number)=>new Intl.NumberFormat('vi-VN',{style:'currency',currency:'VND',maximumFractionDigits:0}).format(n);
const statusLabels:Record<string,string>={pending:'Đang chờ xử lý',confirmed:'Đã đối soát',approved:'Đã duyệt',rejected:'Đã từ chối'};
export function WorkspaceConsole({user,owned,donations,expenses,busy,onCreateCampaign,onProposeExpense,onConfirmDonation,onDecision,onRefresh,onOpenCampaign}:{
 user:User;owned:Campaign[];donations:RecordItem[];expenses:RecordItem[];busy:boolean;
 onCreateCampaign:()=>void;onProposeExpense:(c:Campaign)=>void;onConfirmDonation:(id:string)=>void;
 onDecision:(e:FormEvent<HTMLFormElement>,id:string)=>void;onRefresh:()=>Promise<void>;onOpenCampaign:(id:string)=>void;
}){
 const [tab,setTab]=useState('overview');
 const manager=user.role==='manager',approver=user.role==='approver',donor=user.role==='donor';
 const pendingDonations=donations.filter(r=>r.status==='pending');
 const pendingExpenses=expenses.filter(r=>r.status==='pending');
 const tabs=[{id:'overview',name:'Tổng quan',icon:<LayoutDashboard size={17}/>},
   ...(donor?[]:[{id:'donations',name:'Đối soát đóng góp',icon:<Wallet size={17}/>},{id:'expenses',name:approver?'Chờ phê duyệt':'Khoản chi & AI',icon:<ClipboardCheck size={17}/>}])];
 const totalConfirmed=donations.filter(r=>r.status==='confirmed').reduce((sum,r)=>sum+r.amount,0);
 const approved=expenses.filter(r=>r.status==='approved').reduce((sum,r)=>sum+r.amount,0);
 const summary=[{label:'Đóng góp đã xác nhận',value:money(totalConfirmed),icon:<Wallet size={19}/>},
  {label:'Khoản chi đã duyệt',value:money(approved),icon:<CheckCircle2 size={19}/>},
  {label:approver?'Chờ phê duyệt':'Cần đối soát',value:String(approver?pendingExpenses.length:pendingDonations.length).padStart(2,'0'),icon:<FileClock size={19}/>}];
 return <div className="work-console">
  <div className="work-welcome">
   <div><span className="eyebrow">AUREVA / KHÔNG GIAN LÀM VIỆC</span><h1>{donor?'Đóng góp của tôi':approver?'Trung tâm phê duyệt':'Bảng điều hành cứu trợ'}</h1><p>{donor?'Theo dõi những khoản bạn đã ghi nhận và quá trình đối soát.':approver?'Đánh giá chứng từ, kiểm tra cảnh báo AI và lưu quyết định có trách nhiệm.':'Quản lý chiến dịch, xác nhận đóng góp thực nhận và hoàn thiện hồ sơ khoản chi.'}</p></div>
   {manager&&<button className="btn primary" onClick={onCreateCampaign}><Plus size={17}/> Tạo chiến dịch</button>}
  </div>
  {donor?<ContributionTrail items={donations} onOpenCampaign={onOpenCampaign}/>:<div className="work-body">
   <nav className="work-sidebar" aria-label="Chức năng quản lý">
    <div className="work-side-caption">QUẢN TRỊ & KIỂM SOÁT</div>
    {tabs.map(t=><button key={t.id} className={tab===t.id?'active':''} onClick={()=>setTab(t.id)} aria-current={tab===t.id?'page':undefined}>{t.icon}<span>{t.name}</span>{t.id==='expenses'&&pendingExpenses.length>0&&<small>{pendingExpenses.length}</small>}{t.id==='donations'&&pendingDonations.length>0&&<small>{pendingDonations.length}</small>}</button>)}
    <div className="work-side-note"><ShieldCheck size={20}/><b>Phân quyền theo vai trò</b><p>Mọi thao tác xác nhận, phân tích và phê duyệt được kiểm soát tại API.</p></div>
   </nav>
   <div className="work-main">
    {tab==='overview'&&<>
     <div className="work-panel-heading"><div><span className="eyebrow">01 / TỔNG QUAN NGHIỆP VỤ</span><h2>Những việc cần theo dõi</h2></div><span className="work-current-role">{approver?'Người phê duyệt':'Người phụ trách'}</span></div>
     <div className="work-stats">{summary.map(s=><div className="work-stat" key={s.label}><span className="work-stat-icon">{s.icon}</span><span>{s.label}</span><strong>{s.value}</strong></div>)}</div>
     <div className="work-task"><div><span className="work-task-icon"><Activity size={21}/></span><div><h3>{approver?pendingExpenses.length?pendingExpenses.length+' khoản chi đang chờ kiểm tra':'Không có khoản chi chờ duyệt':pendingDonations.length?pendingDonations.length+' khoản đóng góp cần đối soát':'Không có khoản đóng góp chờ đối soát'}</h3><p>{approver?'Đọc kết quả AI và đối chiếu chứng từ trước khi quyết định.':'Chỉ xác nhận khoản đóng góp khi đã kiểm tra số tiền thực nhận.'}</p></div></div><button className="btn light" onClick={()=>setTab(approver?'expenses':'donations')}>Mở danh sách <ArrowRight size={15}/></button></div>
     {manager&&<section className="work-campaigns"><div className="work-panel-heading"><div><span className="eyebrow">CHIẾN DỊCH CỦA BẠN</span><h2>Đang quản lý</h2></div></div>{owned.length===0?<div className="work-empty"><HeartHandshake size={22}/> Chưa có chiến dịch do bạn phụ trách.</div>:<div className="work-campaign-list">{owned.map(c=><article key={c.id}><div><b>{c.title}</b><small>{c.location} · Đã đối soát {money(c.raised)}</small></div><button className="btn light" onClick={()=>onOpenCampaign(c.id)}>Xem <ArrowUpRight size={14}/></button><button className="btn primary" onClick={()=>onProposeExpense(c)}>Đề xuất khoản chi</button></article>)}</div>}</section>}
    </>}
    {tab==='donations'&&<section className="work-ledger"><div className="work-panel-heading"><div><span className="eyebrow">02 / ĐỐI SOÁT THU</span><h2>Danh sách đóng góp</h2><p>Không tính các khoản chờ xác nhận vào số tiền đã nhận.</p></div></div>{!donations.length?<div className="work-empty"><Wallet size={25}/> Chưa có khoản đóng góp để đối soát.</div>:donations.map(r=><article className="ledger-row" key={r.id}><div className="ledger-row-main"><span className="ledger-avatar"><HeartHandshake size={19}/></span><div><b>{r.campaign_title}</b><small>{new Date(r.created).toLocaleString('vi-VN')}{r.reference?' · Tham chiếu: '+r.reference:''}</small></div></div><div className="ledger-right"><strong>{money(r.amount)}</strong><span className={'badge '+r.status}>{statusLabels[r.status]??r.status}</span></div>{r.status==='pending'&&<button className="btn primary" disabled={busy} onClick={()=>onConfirmDonation(r.id)}><CheckCircle2 size={16}/> Xác nhận đã nhận tiền</button>}</article>)}</section>}
    {tab==='expenses'&&<section className="work-expenses"><div className="work-panel-heading"><div><span className="eyebrow">03 / CHỨNG TỪ & TRÁCH NHIỆM</span><h2>{approver?'Hàng chờ phê duyệt':'Hồ sơ khoản chi'}</h2><p>AI chỉ hỗ trợ phát hiện chênh lệch; người có thẩm quyền quyết định cuối cùng.</p></div></div>{!expenses.length?<div className="work-empty"><FileText size={24}/> Chưa có khoản chi nào.</div>:expenses.map(r=><article className="expense-review" key={r.id}>
     <div className="expense-review-top"><div className="expense-icon"><FileText size={22}/></div><div className="expense-title"><span className="eyebrow">HỒ SƠ KHOẢN CHI · {r.id.slice(0,8).toUpperCase()}</span><h3>{r.purpose??'Khoản chi cứu trợ'}</h3><p>{r.campaign_title} · {new Date(r.created).toLocaleString('vi-VN')}</p></div><div className="expense-amount"><b>{money(r.amount)}</b><span className={'badge '+r.status}>{statusLabels[r.status]??r.status}</span></div></div>
     <div className="expense-review-meta"><div><small>Đơn vị nhận tiền</small><b>{r.vendor??'Chưa khai báo'}</b></div><div><small>Trạng thái</small><b>{statusLabels[r.status]??r.status}</b></div></div>
     {r.reason&&<div className="expense-decision-note"><SearchCheck size={17}/> Lý do quyết định: {r.reason}</div>}
     <EvidencePanel id={r.id} amount={r.amount} vendor={r.vendor} status={r.status} document={r.document} attestation={r.attestation} manager={manager} onRefresh={onRefresh}/>
     {approver&&r.status==='pending'&&<form className="decision work-decision" onSubmit={e=>onDecision(e,r.id)}><label>Lý do phê duyệt hoặc từ chối<input name="reason" required minLength={5} maxLength={1000} placeholder="Nêu rõ nội dung đã kiểm tra…"/></label><label>Quyết định<select name="status"><option value="approved">Phê duyệt</option><option value="rejected">Từ chối</option></select></label><button disabled={busy} className="btn primary"><ClipboardCheck size={16}/> Lưu quyết định</button><small><CircleAlert size={14}/> Phê duyệt chỉ thực hiện được khi chứng từ đã được phân tích AI.</small></form>}
    </article>)}</section>}
   </div>
  </div>}
 </div>;
}
