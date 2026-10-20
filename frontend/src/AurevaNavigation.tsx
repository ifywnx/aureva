import {ArrowUpRight, CircleHelp, HeartHandshake, Layers3, LogOut, ShieldCheck, Wallet} from 'lucide-react';
import {AurevaMark} from './AurevaStory';

type UserHeader={name:string;role:'donor'|'manager'|'approver'};
const roleName={donor:'Người đóng góp',manager:'Người phụ trách',approver:'Người phê duyệt'};
export function AurevaHeader({page,user,onNavigate,onLogin,onLogout}:{
  page:string;user:UserHeader|null;
  onNavigate:(page:string)=>void;onLogin:()=>void;onLogout:()=>void;
}){
  return <header className="site-header">
    <div className="site-header-inner">
      <button className="brand brand-original" onClick={()=>onNavigate('overview')} aria-label="AUREVA trang chủ">
        <span className="brand-monogram"><AurevaMark size={35}/></span>
        <span className="brand-wordmark">AUREVA<small>Trao gửi yêu thương, rõ từng đóng góp.</small></span>
      </button>
      <nav className="site-nav" aria-label="Điều hướng chính">
        <button className={page==='overview'?'active':''} aria-current={page==='overview'?'page':undefined} onClick={()=>onNavigate('overview')}><Layers3 size={16}/> Tổng quan công khai</button>
        <button className={page==='campaigns'||page==='detail'?'active':''} aria-current={page==='campaigns'||page==='detail'?'page':undefined} onClick={()=>onNavigate('campaigns')}><HeartHandshake size={16}/> Chiến dịch</button>
        <button className={page==='transparency'?'active':''} aria-current={page==='transparency'?'page':undefined} onClick={()=>onNavigate('transparency')}><ShieldCheck size={16}/> Minh bạch</button>
        {user&&<button className={page==='workspace'?'active':''} aria-current={page==='workspace'?'page':undefined} onClick={()=>onNavigate('workspace')}><Wallet size={16}/> Không gian làm việc</button>}
      </nav>
      <div className="site-account">
        {user?<><div className="site-user"><span className="user-avatar">{user.name.trim().charAt(0).toUpperCase()}</span><span><strong>{user.name}</strong><small>{roleName[user.role]}</small></span></div><button className="icon-btn" title="Đăng xuất" aria-label="Đăng xuất" onClick={onLogout}><LogOut size={18}/></button></>:
          <button className="btn account-login" onClick={onLogin}>Đăng nhập <ArrowUpRight size={16}/></button>}
      </div>
    </div>
  </header>;
}

type DonationItem={id:string;campaign_id:string;campaign_title:string;amount:number;reference?:string;status:string;created:string};
const money=(v:number)=>new Intl.NumberFormat('vi-VN',{style:'currency',currency:'VND',maximumFractionDigits:0}).format(v);
export function ContributionTrail({items,onOpenCampaign}:{items:DonationItem[];onOpenCampaign:(campaignId:string)=>void}){
  return <section className="contribution-trail" aria-labelledby="contribution-journey-title">
    <div className="trail-intro"><div><span className="eyebrow"><CircleHelp size={15}/> GÓC CỦA NGƯỜI ĐÓNG GÓP</span><h2 id="contribution-journey-title">Hành trình đóng góp của bạn</h2><p>Kiểm tra từng khoản đã ghi nhận và trạng thái đối soát. Đây không phải chức năng theo dõi một tờ tiền đến từng khoản chi cụ thể.</p></div></div>
    {!items.length?<div className="trail-empty"><HeartHandshake size={24}/><p>Bạn chưa ghi nhận khoản đóng góp nào. Hãy mở một chiến dịch để bắt đầu.</p></div>:<div className="trail-records">{items.map(r=><article key={r.id} className="trail-record">
      <div className="trail-record-head">
        <div><span className="eyebrow">MÃ GIAO DỊCH · {r.id.slice(0,8).toUpperCase()}</span><h3>{r.campaign_title}</h3><small>{new Date(r.created).toLocaleString('vi-VN')}</small></div>
        <div className="trail-amount">{money(r.amount)}<span className={'badge '+r.status}>{r.status==='confirmed'?'Đã đối soát':'Chờ đối soát'}</span></div>
      </div>
      <div className="trail-stages">
        <div className="trail-stage complete"><span>01</span><div><b>Đã ghi nhận</b><small>Thông tin chuyển khoản đã được gửi vào hệ thống</small></div></div>
        <div className={'trail-stage '+(r.status==='confirmed'?'complete':'waiting')}><span>02</span><div><b>{r.status==='confirmed'?'Đã xác nhận tiền thực nhận':'Đợi người phụ trách đối soát'}</b><small>Khoản đóng góp chỉ tính vào tổng khi được xác nhận</small></div></div>
        <div className="trail-stage outlined"><span>03</span><div><b>Kiểm tra thu – chi chiến dịch</b><small>Xem tổng hợp khoản chi được duyệt và báo cáo công khai</small></div></div>
      </div>
      <button className="btn trail-link" onClick={()=>onOpenCampaign(r.campaign_id)}>Mở thu chi của chiến dịch <ArrowUpRight size={16}/></button>
    </article>)}</div>}
    <p className="trail-disclosure">Các khoản chi thuộc về quỹ chung của chiến dịch; hệ thống chưa định danh tiền của từng người đến từng hóa đơn. Blockchain chỉ xác thực quyết định/báo cáo nếu giao dịch Sepolia được xác nhận.</p>
  </section>;
}
