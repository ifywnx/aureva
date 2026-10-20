import {ArrowRight, ArrowUpRight, Check, CheckCircle2, ClipboardCheck, FileText, Fingerprint, Heart, ShieldCheck, Sparkles, Wallet, Waves} from 'lucide-react';
import {motion, useReducedMotion} from 'framer-motion';

type Metrics={raised:number;spent:number;contribution_count:number;campaigns:{id:string}[]};
const fmt=(n:number)=>new Intl.NumberFormat('vi-VN',{maximumFractionDigits:0}).format(n);

export function AurevaMark({size=35}:{size?:number}){
 return <svg width={size} height={size} viewBox="0 0 48 48" fill="none" aria-hidden="true">
  <path d="M7 26.5c7-1.2 9.5-13 17-13 7.3 0 10 11.8 17 13" stroke="currentColor" strokeWidth="4.2" strokeLinecap="round"/>
  <path d="M8 34c6.6-1.6 10-9.1 16-9.1 6.1 0 9.4 7.5 16 9.1" stroke="currentColor" strokeWidth="4.2" strokeLinecap="round" opacity=".53"/>
  <circle cx="24" cy="9" r="3.5" fill="#F4A68C"/>
  <circle cx="8.5" cy="26.5" r="2.3" fill="currentColor"/>
  <circle cx="39.5" cy="26.5" r="2.3" fill="currentColor"/>
 </svg>;
}

function ProofVisual(){
 const reduced=useReducedMotion();
 const stages=[
  {name:'Khoản đóng góp',caption:'Được đối soát với tiền nhận',icon:<Wallet size={18}/>},
  {name:'Chứng từ & cảnh báo AI',caption:'Chờ người có thẩm quyền kiểm tra',icon:<FileText size={18}/>},
  {name:'Dấu xác thực',caption:'Xác minh trạng thái trên Sepolia',icon:<Fingerprint size={18}/>}
 ];
 return <motion.div className="proof-visual" aria-label="Minh họa quy trình kiểm tra, không phải dữ liệu giao dịch" initial={reduced?false:{opacity:0,y:18}} animate={{opacity:1,y:0}} transition={{duration:.7,delay:.15}}>
  <div className="proof-halo proof-halo-one"/><div className="proof-halo proof-halo-two"/>
  <div className="proof-visual-index">AUREVA / SYSTEM OVERVIEW <span>01 — 03</span></div>
  <div className="proof-visual-sheet">
   <div className="proof-sheet-heading"><span className="sheet-round-icon"><AurevaMark size={24}/></span><div><span>QUY TRÌNH KIỂM CHỨNG</span><strong>Từng bước đều có dấu vết.</strong></div><CheckCircle2 size={20} color="#407D70"/></div>
   <div className="proof-stages">{stages.map((step,i)=><div className="proof-stage" key={i}>
    <div className="proof-stage-symbol">{step.icon}</div>
    <div><b>{step.name}</b><small>{step.caption}</small></div>
    <span>{String(i+1).padStart(2,'0')}</span>
   </div>)}</div>
   <div className="proof-sheet-bottom"><ShieldCheck size={15}/><span>Minh họa quy trình · không thay thế bằng chứng giao dịch thật</span></div>
  </div>
  <div className="proof-seal"><Heart size={15} fill="currentColor"/> LAN TỎA ĐIỀU TỐT</div>
 </motion.div>;
}
export function PublicIntro({data,onExplore,onTransparency}:{data:Metrics|null;onExplore:()=>void;onTransparency:()=>void}){
 const reduced=useReducedMotion();
 return <>
  <section className="hero hero-v3" aria-labelledby="hero-v3-title">
   <div className="hero-copy">
    <motion.div className="hero-topline" initial={reduced?false:{opacity:0,y:8}} animate={{opacity:1,y:0}} transition={{duration:.5}}>
      <span className="hero-spark"><Waves size={15}/></span> CỨU TRỢ MINH BẠCH · CÔNG NGHỆ VÌ CỘNG ĐỒNG
    </motion.div>
    <motion.h1 id="hero-v3-title" initial={reduced?false:{opacity:0,y:16}} animate={{opacity:1,y:0}} transition={{duration:.58,delay:.05}}>
      Trao gửi yêu thương,<br/><em>rõ từng đóng góp.</em>
    </motion.h1>
    <motion.p initial={reduced?false:{opacity:0,y:10}} animate={{opacity:1,y:0}} transition={{duration:.5,delay:.12}}>AUREVA giúp kết nối những tấm lòng với các chiến dịch cứu trợ — nơi việc tiếp nhận, phê duyệt và công khai thu chi được đặt trong một quy trình có thể kiểm tra.</motion.p>
    <div className="hero-actions">
     <button className="btn primary" onClick={onExplore}>Khám phá chiến dịch <ArrowUpRight size={17}/></button>
     <button className="btn story-outline" onClick={onTransparency}>Khám phá sự minh bạch <ArrowRight size={17}/></button>
    </div>
    <div className="hero-assurances"><span><Check size={14}/> Số liệu từ database</span><span><Check size={14}/> Quyết định có dấu vết</span></div>
   </div>
   <ProofVisual/>
  </section>
  <div className="story-ribbon" aria-label="Tóm tắt dữ liệu công khai">
   <div className="ribbon-lead"><span className="ribbon-asterisk"><Heart size={21}/></span><div><b>Minh bạch tạo dựng niềm tin</b><small>Cập nhật từ dữ liệu thật của hệ thống</small></div></div>
   <div className="ribbon-item"><small>Đóng góp đã đối soát</small><strong>{data?fmt(data.raised)+' ₫':'Đang tải…'}</strong></div>
   <div className="ribbon-item"><small>Chi được phê duyệt</small><strong>{data?fmt(data.spent)+' ₫':'Đang tải…'}</strong></div>
   <div className="ribbon-item"><small>Chiến dịch cứu trợ</small><strong>{data?fmt(data.campaigns.length):'…'}</strong></div>
  </div>
 </>;
}
export function TransparencyHub({data,onExplore}:{data:Metrics|null;onExplore:()=>void}){
 const percent=data&&data.raised>0?Math.min(100,Math.max(0,data.spent/data.raised*100)):0;
 return <section className="transparency-hub">
  <div className="detail-head transparency-heading"><div className="eyebrow"><Sparkles size={16}/> MINH BẠCH LÀ NỀN TẢNG CỦA LÒNG TIN</div><h1>Dữ liệu công khai.<br/><em>Trách nhiệm rõ ràng.</em></h1><p>Thu chi được tổng hợp từ database, tách riêng tiền đã đối soát và các khoản chi đã được phê duyệt. Mỗi chiến dịch có lịch sử để mọi người cùng kiểm tra.</p></div>
  <div className="transparency-board">
   <div className="transparency-chart">
    <div className="panel-top"><span>01 / TÀI CHÍNH CÔNG KHAI</span><span className="panel-chip"><span/> DỮ LIỆU THỰC</span></div>
    <h2>Toàn cảnh dòng tiền cứu trợ</h2>
    <div className="money-balance">
     <div><span>Tổng thu đã đối soát</span><b>{data?fmt(data.raised)+' ₫':'…'}</b></div>
     <div><span>Khoản chi đã duyệt</span><b>{data?fmt(data.spent)+' ₫':'…'}</b></div>
     <div><span>Số dư tính toán</span><b>{data?fmt(data.raised-data.spent)+' ₫':'…'}</b></div>
    </div>
    <div className="proportion-bar" role="img" aria-label={data?'Khoản chi được duyệt chiếm '+percent.toFixed(1)+'% số tiền đã đối soát':'Chưa tải dữ liệu'}><span style={{width:percent+'%'}}/></div>
    <div className="proportion-legend"><span><i/> Số tiền đã đối soát</span><span><i/> Khoản chi được duyệt</span></div>
    <p className="small-disclosure">Lưu ý: “Chi đã duyệt” là quyết định phân bổ kinh phí, không phải bằng chứng xác nhận đã chuyển khoản ngân hàng.</p>
   </div>
   <div className="transparency-ethos">
    <span className="ethos-icon"><ClipboardCheck size={32}/></span>
    <div className="eyebrow">02 / CHỨNG CỨ & TRÁCH NHIỆM</div>
    <h2>Không chỉ là<br/><em>những con số.</em></h2>
    <p>Chứng từ được lưu riêng tư để người phê duyệt kiểm tra cảnh báo AI. Quyết định và báo cáo có dấu băm; trạng thái Blockchain chỉ được xác nhận khi giao dịch thực sự thành công trên Sepolia.</p>
    <button className="btn story-outline" onClick={onExplore}>Xem chiến dịch & lịch sử <ArrowRight size={16}/></button>
   </div>
  </div>
  <div className="transparency-disclaimer"><ShieldCheck size={17}/><p>AI hỗ trợ phân tích và phát hiện dữ liệu cần kiểm tra, không tự kết luận gian lận. Phê duyệt cuối cùng luôn thuộc về người có thẩm quyền.</p></div>
 </section>;
}
