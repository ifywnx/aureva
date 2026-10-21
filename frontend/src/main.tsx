import React, {useEffect,useState,type FormEvent} from 'react';
import {createRoot} from 'react-dom/client';
import {HeartHandshake, ArrowUpRight, ShieldCheck, Plus, X, MapPin, Search} from 'lucide-react';
import {AnimatePresence, motion, useReducedMotion} from 'framer-motion';
import {PageMotion, ScrollProgress, StatValue} from './Motion';

import {AurevaHeader} from './AurevaNavigation';
import {WorkspaceConsole} from './WorkspaceConsole';
import {CampaignCoverEditor} from './CampaignCoverEditor';
import {ActivityInsights} from './ActivityInsights';
import {JourneyFlow} from './JourneyFlow';
import {AurevaChat} from './AurevaChat';
import {PublicDemo} from './PublicDemo';
import {DemoRoleBar,type DemoRole} from './DemoRoleBar';
import {PublicIntro,HumanStory,TechnologyShowcase,TransparencyHub} from './AurevaStory';
import './style.css';
import './identity.css';
import './premium.css';
import './lively.css';
import './blueimpact.css';
import {Reports,type DocumentInfo,type Attestation,type ReportInfo} from './Evidence';
import './typography.css';
type User={id:string;name:string;email:string;role:'donor'|'manager'|'approver'};
type Campaign={id:string;title:string;description:string;location:string;target:number;raised:number;spent:number;owner_id:string;manager_name:string;contribution_count:number;cover_url:string|null;is_closed:boolean|number};
type RecordItem={id:string;campaign_id:string;campaign_title:string;amount:number;status:string;reference?:string;purpose?:string;vendor?:string;reason?:string;created:string;document?:DocumentInfo|null;attestation?:Attestation|null};
type Dashboard={campaigns:Campaign[];raised:number;spent:number;contribution_count:number;integrations:{ai:string;blockchain:string}};
type Detail={campaign:Campaign;donations:RecordItem[];expenses:RecordItem[]};
const money=(v:number)=>new Intl.NumberFormat('vi-VN',{style:'currency',currency:'VND',maximumFractionDigits:0}).format(v);
const statuses:Record<string,string>={pending:'Chờ xử lý',confirmed:'Đã đối soát',approved:'Đã duyệt',rejected:'Từ chối'};
async function api<T>(path:string,body?:unknown):Promise<T>{const r=await fetch('/api'+path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json','X-Aureva-Request':'1'},credentials:'same-origin',body:body===undefined?undefined:JSON.stringify(body)});const d=await r.json().catch(()=>null);if(!r.ok)throw new Error(typeof d?.detail==='string'?d.detail:r.status>=500?'Máy chủ tạm thời chưa kết nối được dữ liệu. Vui lòng thử lại sau.':'Thông tin chưa hợp lệ. Vui lòng kiểm tra các trường.');if(d===null)throw new Error('Máy chủ trả về dữ liệu không hợp lệ. Vui lòng thử lại sau.');return d as T;}
function App(){
 const reducedMotion = useReducedMotion();
 const [user,setUser]=useState<User|null>(null),[data,setData]=useState<Dashboard|null>(null),[workspace,setWorkspace]=useState<{donations:RecordItem[];expenses:RecordItem[]}>({donations:[],expenses:[]});
 const [reports,setReports]=useState<ReportInfo[]>([]);
 const [dashboardState,setDashboardState]=useState<'loading'|'ready'|'failed'>('loading');
 const [page,setPage]=useState('overview'),[modal,setModal]=useState(''),[selected,setSelected]=useState<Campaign|null>(null),[detail,setDetail]=useState<Detail|null>(null),[error,setError]=useState(''),[notice,setNotice]=useState(''),[busy,setBusy]=useState(false),[campaignQuery,setCampaignQuery]=useState('');
 const [demoEnabled,setDemoEnabled]=useState(false);
 async function refresh(u:User|null=user,keepDetail=true){
   try{
     const dashboard=await api<Dashboard>('/public/dashboard');
     setData(dashboard);setDashboardState('ready');
   }catch(e){setDashboardState('failed');throw e;}
   if(u)setWorkspace(await api('/workspace'));else setWorkspace({donations:[],expenses:[]});
   if(keepDetail&&selected){setDetail(await api('/public/campaigns/'+selected.id));setReports(await api('/public/campaigns/'+selected.id+'/reports'));}
 }
 useEffect(()=>{api<User>('/auth/me').then(u=>{setUser(u);return refresh(u)}).catch(()=>refresh(null).catch(e=>setError(e.message)));},[]);
 useEffect(()=>{api<{enabled:boolean}>('/demo/status').then(data=>setDemoEnabled(data.enabled===true)).catch(()=>setDemoEnabled(false));},[]);
 async function run(action:()=>Promise<void>){setBusy(true);setError('');setNotice('');try{await action();return true}catch(e){setError(e instanceof Error?e.message:'Không kết nối được máy chủ.');return false}finally{setBusy(false)}}
 async function switchDemo(role:DemoRole){await run(async()=>{
   const account=await api<User>('/demo/switch',{role});
   setUser(account);setSelected(null);setDetail(null);setReports([]);setModal('');
   await refresh(account,false);
   setPage(role==='donor'?'campaigns':'workspace');
   window.scrollTo({top:0,behavior:'auto'});
   setNotice('Đang sử dụng tài khoản DEMO: '+({donor:'Người đóng góp',manager:'Người quản lý',approver:'Người phê duyệt'}[role])+'. Chỉ dùng dữ liệu thử nghiệm.');
 });}
 function open(type:string,c?:Campaign){setModal(type);setSelected(c??null);setError('');}
 async function submit(e:FormEvent<HTMLFormElement>){e.preventDefault();const f=new FormData(e.currentTarget);const value=(k:string)=>String(f.get(k)||'');const amount=Number(value('amount'));
 const success=await run(async()=>{
 if(modal==='login'){const u=await api<User>('/auth/login',{email:value('email'),password:value('password')});setUser(u);await refresh(u);setNotice('Đăng nhập thành công.');}
 if(modal==='register'){await api('/auth/register',{name:value('name'),email:value('email'),password:value('password')});setModal('login');setNotice('Đã tạo tài khoản. Hãy đăng nhập.');return;}
 if(modal==='campaign'){await api('/campaigns',{title:value('title'),description:value('description'),location:value('location'),target:amount});await refresh();setNotice('Đã tạo chiến dịch.');}
 if(modal==='donation'&&selected){
   if(demoEnabled&&user?.id==='aureva_demo_donor_v1'){
    await api('/demo/donations',{campaign_id:selected.id,amount});
    await refresh();setNotice('Đã ghi nhận đóng góp mô phỏng. KHÔNG có chuyển tiền hoặc thanh toán thật.');
   }else{
    await api(`/campaigns/${selected.id}/donations`,{amount,reference:value('reference')});
    await refresh();setNotice('Đã ghi nhận thông tin chuyển khoản; chờ người phụ trách đối soát bên ngoài website.');
   }
  }
 if(modal==='expense'&&selected){await api(`/campaigns/${selected.id}/expenses`,{amount,purpose:value('purpose'),vendor:value('vendor')});await refresh();setNotice('Khoản chi đã được gửi chờ phê duyệt.');}
 });if(success&&modal!=='register')setModal('');}
 async function closeCampaign(id:string){
  if(!window.confirm('Kết thúc chiến dịch? Thao tác này không thể hoàn tác và hệ thống sẽ ngừng nhận đóng góp hoặc đề xuất chi mới.'))return;
  await run(async()=>{await api('/campaigns/'+id+'/close',{});await refresh();setNotice('Đã kết thúc chiến dịch. Lịch sử thu chi và báo cáo vẫn công khai.');});
 }
 async function inspect(c:Campaign){await run(async()=>{setDetail(await api('/public/campaigns/'+c.id));setReports(await api('/public/campaigns/'+c.id+'/reports'));setSelected(c);setPage('detail');window.scrollTo({top:0,behavior:'auto'})})}
 async function decision(e:FormEvent<HTMLFormElement>,id:string){e.preventDefault();const f=new FormData(e.currentTarget);await run(async()=>{await api('/expenses/'+id+'/decision',{status:f.get('status'),reason:f.get('reason'),warnings_acknowledged:f.get('warnings_acknowledged')==='true'});await refresh();setNotice('Đã lưu quyết định. Chưa ghi lên Blockchain.');});}
 const isDemoDonor=demoEnabled&&user?.id==='aureva_demo_donor_v1';
 const owned=data?.campaigns.filter(c=>c.owner_id===user?.id)||[];
 const visibleCampaigns=(data?.campaigns??[]).filter(c=>(c.title+' '+c.location+' '+c.description).toLocaleLowerCase('vi').includes(campaignQuery.toLocaleLowerCase('vi').trim()));
 function navigate(nextPage:string){setPage(nextPage);window.scrollTo({top:0,behavior:'auto'});}
 return <div className="shell identity-shell"><ScrollProgress/>
 <AurevaHeader page={page} user={user} onNavigate={navigate} onLogin={()=>open('login')} onLogout={()=>run(async()=>{await api('/auth/logout',{});setUser(null);setWorkspace({donations:[],expenses:[]});navigate('overview');setNotice('Đã đăng xuất.');})}/>
 <DemoRoleBar enabled={demoEnabled} user={user} busy={busy} onSwitch={role=>void switchDemo(role)}/>
 <div className="main">
 <main className="aureva-main"><PageMotion page={page}>{error&&!modal&&<div role="alert" className="alert error">{error}</div>}{notice&&<div role="status" className="alert success">{notice}</div>}
 {(page==='overview'||page==='campaigns')&&<>{page==='overview'&&<><PublicIntro data={data} dataUnavailable={dashboardState==='failed'} onExplore={()=>navigate('campaigns')} onTransparency={()=>navigate('transparency')}/><JourneyFlow onTransparency={()=>navigate('transparency')}/></>}
 {page==='campaigns'&&<div className="campaigns-page-intro"><span className="eyebrow">NƠI NHỮNG TẤM LÒNG GẶP NHAU</span><h1>Một hành động nhỏ.<br/><em>Một thay đổi có thật.</em></h1><p>Khám phá các chiến dịch, xem tiến độ đối soát và tự kiểm tra các quyết định thu chi.</p></div>}
 {page==='overview'&&data!==null&&data.campaigns.length===0&&<TechnologyShowcase data={data} onTransparency={()=>navigate('transparency')}/>} <section id="campaigns" className="campaign-section v5-campaign-section"><div className="section-head"><div><div className="eyebrow">CHUNG SỨC VÌ CỘNG ĐỒNG · VIỆT NAM</div><h2>Nơi yêu thương được lan tỏa <span className="count">{data?.campaigns.length??0}</span></h2></div>{user?.role==='manager'&&<button className="btn primary" onClick={()=>open('campaign')}><Plus size={17}/>Tạo chiến dịch</button>}</div>{!data?dashboardState==='failed'?<div className="empty data-unavailable"><ShieldCheck size={24}/><div><h3>Chưa kết nối được dữ liệu công khai</h3><p>Không thể tải chiến dịch lúc này. AUREVA sẽ không thay bằng số tiền hoặc chiến dịch giả. Các phần giới thiệu quy trình vẫn có thể xem bình thường.</p><button className="btn light" onClick={()=>{setDashboardState('loading');setError('');void refresh(null).catch(e=>setError(e instanceof Error?e.message:'Chưa kết nối được máy chủ.'));}}>Thử kết nối lại <ArrowUpRight size={16}/></button></div></div>:<div className="empty">Đang tải dữ liệu…</div>:!data.campaigns.length?<div className="empty heart-empty"><div className="heart-empty-copy"><span className="eyebrow">MỖI HÀNH TRÌNH CÓ MỘT KHỞI ĐẦU</span><h3>Chiến dịch đầu tiên có thể bắt đầu từ đây.</h3><p>Chưa có chiến dịch được tạo. AUREVA không hiển thị quỹ hoặc hoạt động mẫu như dữ liệu thật — hãy bắt đầu bằng một chiến dịch có người phụ trách rõ ràng.</p><button className="btn light" onClick={()=>page==='overview'?document.getElementById('journey-flow')?.scrollIntoView({behavior:'smooth'}):navigate('overview')}>Khám phá quy trình 6 bước <ArrowUpRight size={16}/></button>{user?.role==='manager'&&<button className="btn primary" onClick={()=>open('campaign')}><Plus size={16}/> Tạo chiến dịch đầu tiên</button>}</div><div className="heart-empty-photo"><img loading="lazy" src="https://images.pexels.com/photos/33670808/pexels-photo-33670808.jpeg?auto=compress&cs=tinysrgb&w=900" alt="Tình nguyện viên trẻ tham gia hoạt động cộng đồng tại Hà Nội"/><span>Ảnh tình nguyện tại Hà Nội · Thang Nguyen / Pexels · không phải chiến dịch AUREVA</span></div></div>:<><div className="campaign-toolbar"><label className="campaign-search"><Search size={18}/><input value={campaignQuery} onChange={e=>setCampaignQuery(e.target.value)} aria-label="Tìm kiếm chiến dịch" placeholder="Tìm theo tên hoặc khu vực cứu trợ…"/></label><span>{visibleCampaigns.length} chiến dịch phù hợp</span></div>{!visibleCampaigns.length?<div className="empty compact">Không tìm thấy chiến dịch phù hợp. Hãy thử từ khóa khác.</div>:<div className="campaign-grid">{visibleCampaigns.map((c,i)=><motion.article className={'campaign campaign-variant-'+(i%3)} key={c.id} initial={false} whileHover={reducedMotion?undefined:{y:-6}} transition={{type:'spring',stiffness:210,damping:23}}><div className="campaign-visual" aria-hidden="true">{c.cover_url&&<img className="campaign-photo" src={c.cover_url} alt="" loading="lazy"/>}<div className="campaign-landscape"><span className="landscape-sun"/><span className="landscape-hill hill-one"/><span className="landscape-hill hill-two"/></div><span className="campaign-visual-word">CÙNG NHAU LAN TỎA</span><span className="campaign-visual-number">{String(i+1).padStart(2,'0')}</span></div><div className="campaign-top"><MapPin size={16}/>{c.location}<span>{c.is_closed?'ĐÃ KẾT THÚC':'THU CHI CÔNG KHAI'}</span></div><h3>{c.title}</h3><p>{c.description}</p><div className="raised"><b>{money(c.raised)}</b><span>/ {money(c.target)}</span></div><progress value={Math.min(c.raised,c.target)} max={c.target}/><div className="card-meta"><span>{c.contribution_count} đóng góp xác nhận</span><span>{Math.round(c.raised/c.target*100)}%</span></div><button className="btn light full" onClick={()=>inspect(c)}>Xem chi tiết chiến dịch <ArrowUpRight size={16}/></button></motion.article>)}</div>}</>}</section>{page==='overview'&&<>{data!==null&&data.campaigns.length>0&&<TechnologyShowcase data={data} onTransparency={()=>navigate('transparency')}/>}<HumanStory onTransparency={()=>navigate('transparency')}/><section className="trust"><div><ShieldCheck size={22}/><h3>Minh bạch là trách nhiệm, không chỉ là lời hứa.</h3><p>Số liệu tổng hợp từ các khoản đóng góp đã đối soát và khoản chi đã được phê duyệt.</p></div><div className="integration"><span className="badge pending">AI · {data?.integrations.ai==='configured'?'Đã cấu hình':'Chưa cấu hình'}</span><span className="badge pending">Blockchain · {data?.integrations.blockchain==='configured'?'Đã cấu hình':'Chưa cấu hình'}</span><small>Xem trạng thái xác nhận trên từng quyết định và báo cáo.</small></div></section></>}</>}
 {page==='transparency'&&<><TransparencyHub data={data} onExplore={()=>navigate('campaigns')}/><ActivityInsights/></>}
 {page==='detail'&&detail&&<section className="campaign-detail">
  <button className="back detail-back" onClick={()=>navigate('campaigns')}>← Quay lại danh sách chiến dịch</button>
  <div className="detail-hero">
    <div className="detail-hero-copy">
      <span className="eyebrow"><MapPin size={14}/> CHIẾN DỊCH CỨU TRỢ · {detail.campaign.location}</span>
      <h1>{detail.campaign.title}</h1>
      <p>{detail.campaign.description}</p>
      <span className="detail-owner"><ShieldCheck size={16}/> Phụ trách: {detail.campaign.manager_name}</span>
    </div>
    <div className="detail-funding">
      <span className="eyebrow">TIẾN ĐỘ ĐÓNG GÓP ĐÃ ĐỐI SOÁT</span>
      <strong>{money(detail.campaign.raised)}</strong>
      <small>Mục tiêu: {money(detail.campaign.target)}</small>
      <progress value={Math.min(detail.campaign.raised,detail.campaign.target)} max={detail.campaign.target}/>
      <div><span>{detail.campaign.contribution_count} lượt đóng góp xác nhận</span><b>{Math.round(detail.campaign.raised/detail.campaign.target*100)}%</b></div>
    </div>
  </div>
  {detail.campaign.cover_url&&<img className="detail-campaign-cover" src={detail.campaign.cover_url} alt={"Ảnh bìa chiến dịch "+detail.campaign.title}/>}
  {user?.role==='manager'&&user.id===detail.campaign.owner_id&&<CampaignCoverEditor id={detail.campaign.id} coverUrl={detail.campaign.cover_url} onSaved={()=>refresh()}/>}
  <div className="metrics three detail-metrics">
    <Metric label="Đóng góp đã đối soát" value={money(detail.campaign.raised)}/>
    <Metric label="Khoản chi đã duyệt" value={money(detail.campaign.spent)}/>
    <Metric label="Số dư tính toán" value={money(detail.campaign.raised-detail.campaign.spent)}/>
  </div>
  <div className="actions detail-actions">
    {!user&&<button className="btn primary" onClick={()=>open('login')}>Đăng nhập để ghi nhận đóng góp <ArrowUpRight size={16}/></button>}
    {user?.role==='donor'&&!detail.campaign.is_closed&&(!isDemoDonor||detail.campaign.owner_id==='aureva_demo_manager_v1')&&<button className="btn primary" onClick={()=>open('donation',detail.campaign)}>{isDemoDonor?'Ghi nhận đóng góp DEMO':'Ghi nhận đóng góp'} <HeartHandshake size={16}/></button>}
    {user?.role==='manager'&&user.id===detail.campaign.owner_id&&!detail.campaign.is_closed&&<button className="btn primary" onClick={()=>open('expense',detail.campaign)}>Đề xuất khoản chi <Plus size={16}/></button>}
    {user?.role==='manager'&&user.id===detail.campaign.owner_id&&!detail.campaign.is_closed&&<button className="btn light" disabled={busy} onClick={()=>void closeCampaign(detail.campaign.id)}>Kết thúc chiến dịch</button>}
    {detail.campaign.is_closed&&<span><ShieldCheck size={16}/> Chiến dịch đã kết thúc · báo cáo vẫn được lưu</span>}
    <span><ShieldCheck size={16}/> Thu chi được tổng hợp từ dữ liệu đã lưu</span>
  </div>
  <div className="detail-ledger-grid">
    <section className="detail-ledger"><span className="eyebrow">CÔNG KHAI ĐÓNG GÓP</span><h2>Lịch sử đóng góp công khai</h2><Records items={detail.donations} publicView/></section>
    <section className="detail-ledger"><span className="eyebrow">MINH BẠCH CHI TIÊU</span><h2>Quyết định thu chi</h2><Records items={detail.expenses} publicView/></section>
  </div>
  <ActivityInsights campaignId={detail.campaign.id}/>
  <Reports campaignId={detail.campaign.id} items={reports} editable={!!user&&(user.role==='approver'||(user.role==='manager'&&user.id===detail.campaign.owner_id))} onRefresh={()=>refresh()}/>
  <p className="detail-disclaimer"><ShieldCheck size={17}/> Không công khai email hoặc mã chuyển khoản của người đóng góp. Mã Blockchain chỉ được xác nhận khi giao dịch Sepolia có bằng chứng thực.</p>
 </section>}
 {page==='workspace'&&user&&<WorkspaceConsole user={user} owned={owned} donations={workspace.donations} expenses={workspace.expenses} busy={busy}
   onCreateCampaign={()=>open('campaign')}
   onProposeExpense={c=>open('expense',c)}
   onConfirmDonation={id=>void run(async()=>{await api('/donations/'+id+'/confirm',{});await refresh();setNotice(user?.id==='aureva_demo_manager_v1'?'Đã xác nhận khoản đóng góp mô phỏng. Không phát sinh tiền thật.':'Đã xác nhận số tiền thực nhận và cập nhật số liệu.');})}
    onRejectDonation={(id,reason)=>void run(async()=>{await api('/donations/'+id+'/reject',{reason});await refresh();setNotice('Đã từ chối khai báo chưa đối soát và lưu lý do vào nhật ký.');})}
   onDecision={decision}
   onRefresh={()=>refresh()}
   onOpenCampaign={id=>{const campaign=data?.campaigns.find(c=>c.id===id);if(campaign)void inspect(campaign);else setNotice('Không tìm thấy chiến dịch trong dữ liệu công khai.');}}
 />}
 <footer><b>AUREVA.</b><span>Trao gửi yêu thương, rõ từng đóng góp.</span><span>Đồ án Web Nâng Cao · 2026</span></footer></PageMotion></main></div>
 <AurevaChat/>
 <AnimatePresence>{modal&&<motion.div className="overlay" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} transition={{duration:reducedMotion?0:.2}} onClick={()=>!busy&&setModal('')}><motion.section role="dialog" aria-modal="true" aria-labelledby="modal-title" className="modal" initial={reducedMotion?false:{opacity:0,scale:.94,y:18}} animate={{opacity:1,scale:1,y:0}} exit={reducedMotion?{opacity:1}:{opacity:0,scale:.97,y:12}} transition={{type:'spring',stiffness:300,damping:28}} onClick={e=>e.stopPropagation()}><button className="close icon-btn" aria-label="Đóng" disabled={busy} onClick={()=>setModal('')}><X size={20}/></button><div className="eyebrow">AUREVA</div><h2 id="modal-title">{{login:'Chào mừng trở lại',register:'Tham gia đóng góp',campaign:'Tạo chiến dịch cứu trợ',donation:isDemoDonor?'Ghi nhận đóng góp DEMO':'Ghi nhận đóng góp',expense:'Đề xuất khoản chi'}[modal]}</h2>{error&&<div role="alert" className="alert error">{error}</div>}<form onSubmit={submit}>{modal==='register'&&<Field name="name" label="Họ và tên" minLength={2}/ >}{['login','register'].includes(modal)&&<><Field name="email" label="Email" type="email"/><Field name="password" label="Mật khẩu" type="password" minLength={10}/><p className="muted">{modal==='register'?'Tối thiểu 10 ký tự. Tài khoản mới có quyền người đóng góp.':'Sử dụng tài khoản đã đăng ký hoặc được người quản trị cấp.'}</p></>}{modal==='campaign'&&<><Field name="title" label="Tên chiến dịch" minLength={5}/><Field name="location" label="Địa bàn cứu trợ" minLength={2}/><label>Mô tả<textarea name="description" required minLength={10} maxLength={3000} rows={4}/></label></>}{['campaign','donation','expense'].includes(modal)&&<Field name="amount" label={modal==='campaign'?'Mục tiêu quyên góp (VND)':'Số tiền (VND)'} type="number"/>}{modal==='donation'&&<>{isDemoDonor
 ?<div className="demo-payment-disclaimer" role="note"><ShieldCheck size={19}/><div><strong>Chế độ mô phỏng — không thanh toán</strong><p>Nhập số tiền giả định để thử quy trình. Hệ thống tự tạo mã DEMO; không yêu cầu chuyển khoản, không trừ tiền ngân hàng hoặc ETH.</p></div></div>
 :<><Field name="reference" label="Mã tham chiếu chuyển khoản" minLength={3}/><p className="muted">Chức năng này chỉ lưu thông tin khoản chuyển khoản bên ngoài website. AUREVA không nhận tiền và chưa tự xác minh giao dịch ngân hàng; người phụ trách phải đối soát thủ công.</p></>}</>}{modal==='expense'&&<><Field name="vendor" label="Đơn vị nhận tiền / nhà cung cấp" minLength={2}/><Field name="purpose" label="Nội dung khoản chi" minLength={5}/><p className="muted">Khoản chi sẽ chờ người có thẩm quyền duyệt. Sau khi tạo, hãy tải chứng từ và bấm phân tích AI trong Không gian làm việc.</p></>}<button disabled={busy} className="btn primary full">{busy?'Đang xử lý…':modal==='login'?'Đăng nhập':modal==='register'?'Tạo tài khoản':modal==='donation'&&isDemoDonor?'Lưu đóng góp mô phỏng':'Lưu thông tin'}</button></form>{modal==='login'&&<button className="text-btn" onClick={()=>open('register')}>Chưa có tài khoản? Đăng ký đóng góp</button>}{modal==='register'&&<button className="text-btn" onClick={()=>open('login')}>Đã có tài khoản? Đăng nhập</button>}</motion.section></motion.div>}</AnimatePresence></div>
}
function Field({name,label,type='text',minLength}:{name:string;label:string;type?:string;minLength?:number}){return <label>{label}<input name={name} type={type} required minLength={minLength} maxLength={type==='password'?128:200} min={type==='number'?1:undefined} max={type==='number'?1000000000000:undefined} step={type==='number'?1:undefined} autoComplete={type==='password'?'current-password':name==='email'?'email':undefined}/></label>}
function Metric({label,value,icon}:{label:string;value:string;icon?:React.ReactNode}){
 const reducedMotion=useReducedMotion();
 return <motion.div className="metric"
   initial={reducedMotion?false:{opacity:0,y:20}}
   whileInView={{opacity:1,y:0}}
   viewport={{once:true,amount:.15}}
   transition={{duration:.48,ease:'easeOut'}}>
   <div><span>{label}</span>{icon}</div><strong><StatValue value={value}/></strong><small>Từ dữ liệu đã xác nhận</small>
 </motion.div>;
}
function Records({items,action,publicView=false}:{items:RecordItem[];action?:(r:RecordItem)=>React.ReactNode;publicView?:boolean}){return !items.length?<div className="empty compact">Chưa có giao dịch phù hợp.</div>:<div className="records">{items.map(r=><article key={r.id}><div className="record-line"><div><b>{r.purpose||r.campaign_title||'Đóng góp cứu trợ'}</b><small>{new Date(r.created).toLocaleString('vi-VN')}{!publicView&&r.reference?' · Mã: '+r.reference:''}{!publicView&&r.vendor?' · '+r.vendor:''}</small></div><strong>{money(r.amount)}</strong><span className={'badge '+(r.status||'confirmed')}>{statuses[r.status]||'Đã đối soát'}</span></div>{r.reason&&<p className="reason">Lý do: {r.reason}</p>}{action?.(r)}</article>)}</div>}
// The ?demo=1 sandbox NEVER mounts the production API-driven application.
const publicDemo = new URLSearchParams(window.location.search).get('demo') === '1';
createRoot(document.getElementById('root')!).render(publicDemo ? <PublicDemo/> : <App/>);
