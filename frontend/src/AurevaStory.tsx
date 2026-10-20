import {ArrowRight, ArrowUpRight, BrainCircuit, CheckCircle2, ClipboardCheck, FileCheck2, Fingerprint, HandHeart, HeartHandshake, ShieldCheck, Sparkles, Waves, Wallet, Zap} from 'lucide-react';
import {motion,useReducedMotion} from 'framer-motion';
import {ProofOrbit} from './ProofOrbit';

type Metrics={raised:number;spent:number;contribution_count:number;campaigns:{id:string}[];integrations?:{ai:string;blockchain:string}};
const fmt=(n:number)=>new Intl.NumberFormat('vi-VN',{maximumFractionDigits:0}).format(n);
const vietnamRelief='https://images.pexels.com/photos/32799179/pexels-photo-32799179.jpeg?auto=compress&cs=tinysrgb&w=1400&h=1600&fit=crop';
const vietnamFlood='https://images.pexels.com/photos/34959205/pexels-photo-34959205.jpeg?auto=compress&cs=tinysrgb&w=1400';
const vietnamYouth='https://images.pexels.com/photos/33670808/pexels-photo-33670808.jpeg?auto=compress&cs=tinysrgb&w=900';

export function AurevaMark({size=35}:{size?:number}){
 return <svg width={size} height={size} viewBox="0 0 48 48" fill="none" aria-hidden="true">
  <path d="M7 26.5c7-1.2 9.5-13 17-13 7.3 0 10 11.8 17 13" stroke="currentColor" strokeWidth="4.2" strokeLinecap="round"/>
  <path d="M8 34c6.6-1.6 10-9.1 16-9.1 6.1 0 9.4 7.5 16 9.1" stroke="currentColor" strokeWidth="4.2" strokeLinecap="round" opacity=".53"/>
  <circle cx="24" cy="9" r="3.5" fill="#3A98FF"/>
  <circle cx="8.5" cy="26.5" r="2.3" fill="currentColor"/>
  <circle cx="39.5" cy="26.5" r="2.3" fill="currentColor"/>
 </svg>;
}
export function PublicIntro({data,onExplore,onTransparency}:{data:Metrics|null;onExplore:()=>void;onTransparency:()=>void}){
 const reduced=useReducedMotion();
 return <>
  <section className="hero v5-hero" aria-labelledby="v5-hero-title">
   <div className="v5-hero-copy">
    <motion.div className="v5-overline" initial={reduced?false:{opacity:0,y:10}} animate={{opacity:1,y:0}} transition={{duration:.45}}>
     <span className="v5-live-dot"/> CÔNG NGHỆ VÌ CỘNG ĐỒNG VIỆT NAM
    </motion.div>
    <motion.h1 id="v5-hero-title" initial={reduced?false:{opacity:0,y:22}} animate={{opacity:1,y:0}} transition={{duration:.6,delay:.1}}>
     Trao đi yêu thương.<br/><em>Rõ từng đóng góp.</em>
    </motion.h1>
    <motion.p initial={reduced?false:{opacity:0,y:16}} animate={{opacity:1,y:0}} transition={{duration:.6,delay:.18}}>Một nền tảng để mọi sự sẻ chia có dấu vết rõ ràng — từ tiền đóng góp đã đối soát, chứng từ được AI kiểm tra, quyết định phê duyệt đến báo cáo có thể xác minh.</motion.p>
    <div className="v5-hero-actions">
     <button className="btn primary" onClick={onExplore}>Khám phá chiến dịch <ArrowUpRight size={18}/></button>
     <button className="btn v5-button-outline" onClick={onTransparency}>Xem minh bạch thu chi <ArrowRight size={17}/></button>
    </div>
    <div className="v5-hero-checks"><span><CheckCircle2 size={16}/> Số liệu từ hệ thống</span><span><ShieldCheck size={16}/> Phân quyền và đối soát</span></div>
   </div>
   <div className="v5-hero-photo">
     <img src={vietnamRelief} alt="Tình nguyện viên giúp người cao tuổi mang nhu yếu phẩm tại Bình Phước, Việt Nam" loading="eager" fetchPriority="high"/>
     <div className="v5-photo-shimmer" aria-hidden="true"/>
     <div className="v5-photo-country"><span>VIETNAM · HUMAN STORIES</span><strong>Lan tỏa điều tử tế.</strong></div>
     <div className="v5-photo-glass">
       <div><span className="v5-glass-icon"><HeartHandshake size={18}/></span><span>Trao gửi yêu thương<small>Niềm tin được xây từ minh bạch</small></span></div>
       <span className="v5-glass-mark"><CheckCircle2 size={20}/></span>
     </div>
     <small className="v5-photo-credit">Ảnh thực tế tại Bình Phước · Duy Nguyen / Pexels · ảnh minh họa, không phải chiến dịch AUREVA</small>
   </div>
   <div className="v5-hero-decor v5-decor-a" aria-hidden="true"/><div className="v5-hero-decor v5-decor-b" aria-hidden="true"/>
  </section>
  <div className="v5-statband" aria-label="Các chỉ số công khai">
    <div className="v5-stat-lead"><span className="v5-stat-lead-icon"><Waves size={25}/></span><div><strong>Niềm tin đến từ những con số thật.</strong><small>Dữ liệu được đối soát và phê duyệt</small></div></div>
    <div className="v5-stat"><span>Tổng thu xác nhận</span><strong>{data?fmt(data.raised)+' ₫':'Đang tải…'}</strong></div>
    <div className="v5-stat"><span>Khoản chi đã duyệt</span><strong>{data?fmt(data.spent)+' ₫':'Đang tải…'}</strong></div>
    <div className="v5-stat"><span>Chiến dịch</span><strong>{data?fmt(data.campaigns.length):'…'}</strong></div>
  </div>
 </>;
}

export function TechnologyShowcase({data,onTransparency}:{data:Metrics|null;onTransparency:()=>void}){
 const reduced=useReducedMotion();
 return <section className="v5-tech-section" aria-labelledby="v5-tech-heading">
   <div className="v5-tech-bg" aria-hidden="true"/>
   <div className="v5-tech-copy">
     <div className="v5-tech-overline"><Zap size={17}/> TÍNH NĂNG CÔNG NGHỆ CỐT LÕI</div>
     <h2 id="v5-tech-heading">Một luồng cứu trợ.<br/><em>Hai lớp kiểm chứng.</em></h2>
     <p>AI giúp tìm chênh lệch từ chứng từ thực. Con người có trách nhiệm phê duyệt. Blockchain lưu dấu để đối chiếu lịch sử khi giao dịch được xác nhận.</p>
     <div className="v5-tech-features">
      <motion.article initial={reduced?false:{opacity:0,y:18}} whileInView={{opacity:1,y:0}} viewport={{once:true}}><span><BrainCircuit size={21}/></span><div><strong>AI kiểm tra hóa đơn</strong><small>Đọc ảnh/PDF, đối chiếu số tiền và cảnh báo các điểm cần kiểm tra</small></div></motion.article>
      <motion.article initial={reduced?false:{opacity:0,y:18}} whileInView={{opacity:1,y:0}} viewport={{once:true}} transition={{delay:.1}}><span><Fingerprint size={21}/></span><div><strong>Blockchain lưu dấu</strong><small>SHA-256, lịch sử quyết định, giao dịch thật trên Sepolia khi tích hợp</small></div></motion.article>
      <motion.article initial={reduced?false:{opacity:0,y:18}} whileInView={{opacity:1,y:0}} viewport={{once:true}} transition={{delay:.2}}><span><FileCheck2 size={21}/></span><div><strong>Báo cáo công khai</strong><small>Xuất PDF từ dữ liệu thực và cho phép đối chiếu toàn vẹn</small></div></motion.article>
     </div>
     <button className="v5-tech-link" onClick={onTransparency}>Khám phá hệ thống minh bạch <ArrowUpRight size={18}/></button>
   </div>
   <ProofOrbit aiEnabled={data?.integrations?.ai==='configured'} chainEnabled={data?.integrations?.blockchain==='configured'}/>
 </section>;
}

export function HumanStory({onTransparency}:{onTransparency:()=>void}){
 const steps=[
  {n:'01',name:'Ghi nhận và đối soát',desc:'Người đóng góp khai báo, người phụ trách xác nhận đúng số tiền thực nhận.',icon:<HandHeart size={23}/>},
  {n:'02',name:'AI phân tích — con người duyệt',desc:'Hóa đơn được AI đọc qua API. Quyết định cuối cùng thuộc người phê duyệt.',icon:<ClipboardCheck size={23}/>},
  {n:'03',name:'Lưu dấu và công khai báo cáo',desc:'PDF, mã băm và chứng nhận Sepolia (nếu được xác nhận) có thể được đối chiếu.',icon:<Fingerprint size={23}/>}
 ];
 return <section className="v5-human-section" aria-labelledby="v5-human-title">
  <div className="v5-human-media">
    <img src={vietnamFlood} loading="lazy" alt="Nhân viên cứu hộ tại Phú Yên vượt qua vùng ngập lụt vào ban đêm"/>
    <div className="v5-human-photo-caption"><span>CHUYỆN TỪ VIỆT NAM</span><strong>Giữa những ngày khó khăn, sự sẻ chia vẫn tiếp tục.</strong><small>Ảnh cứu hộ tại Phú Yên · Long Bà Mùi / Pexels. Chỉ minh họa hoạt động cứu trợ tại Việt Nam.</small></div>
  </div>
  <div className="v5-human-content">
   <div className="v5-small-label"><span/> VÌ SAO MINH BẠCH QUAN TRỌNG?</div>
   <h2 id="v5-human-title">Lòng tốt xứng đáng<br/>được <em>đặt đúng niềm tin.</em></h2>
   <p>Mỗi sự giúp đỡ đều quan trọng. AUREVA đặt chứng từ, số liệu và quyết định trong một luồng dễ theo dõi, thay vì để thông tin rải rác.</p>
   <div className="v5-human-steps">{steps.map(step=><div className="v5-human-step" key={step.n}><span className="v5-human-num">{step.n}</span><span className="v5-human-icon">{step.icon}</span><div><strong>{step.name}</strong><small>{step.desc}</small></div></div>)}</div>
   <button className="v5-human-link" onClick={onTransparency}>Tìm hiểu cách AUREVA bảo vệ niềm tin <ArrowRight size={17}/></button>
  </div>
 </section>;
}

export function TransparencyHub({data,onExplore}:{data:Metrics|null;onExplore:()=>void}){
 const percent=data&&data.raised>0?Math.min(100,Math.max(0,data.spent/data.raised*100)):0;
 return <section className="transparency-hub v5-transparency">
  <div className="detail-head transparency-heading">
    <div className="eyebrow"><Sparkles size={16}/> CÔNG KHAI · CÓ BẰNG CHỨNG · DỄ ĐỐI CHIẾU</div>
    <h1>Minh bạch từ<br/><em>mỗi quyết định.</em></h1>
    <p>Tất cả số liệu được tổng hợp từ database: tiền đã đối soát, khoản chi được phê duyệt và số dư của các chiến dịch. Không sử dụng thống kê dựng sẵn.</p>
  </div>
  <div className="transparency-board">
   <div className="transparency-chart">
    <div className="panel-top"><span>01 / TÀI CHÍNH CÔNG KHAI</span><span className="panel-chip"><span/> DỮ LIỆU THỰC</span></div>
    <h2>Tiền đã được ghi nhận và phân bổ thế nào?</h2>
    <div className="money-balance"><div><span>Đóng góp đã đối soát</span><b>{data?fmt(data.raised)+' ₫':'Đang tải…'}</b></div><div><span>Khoản chi đã được duyệt</span><b>{data?fmt(data.spent)+' ₫':'Đang tải…'}</b></div><div><span>Số dư tính toán</span><b>{data?fmt(data.raised-data.spent)+' ₫':'Đang tải…'}</b></div></div>
    <div className="proportion-bar" role="img" aria-label={data?'Khoản chi được duyệt chiếm '+percent.toFixed(1)+'% tổng thu đã đối soát':'Chưa có dữ liệu'}><span style={{width:percent+'%'}}/></div>
    <div className="proportion-legend"><span><i/> Đã đối soát</span><span><i/> Đã phê duyệt</span></div>
    <p className="small-disclosure">Khoản chi đã duyệt thể hiện quyết định sử dụng kinh phí, chưa chứng minh giao dịch ngân hàng đã hoàn tất.</p>
   </div>
   <div className="transparency-ethos"><span className="ethos-icon"><Wallet size={33}/></span><div className="eyebrow">02 / QUY TRÌNH KIỂM CHỨNG</div><h2>Chứng từ rõ ràng.<br/><em>Trách nhiệm minh bạch.</em></h2><p>AI hỗ trợ đọc hóa đơn, người phê duyệt xác minh. Bằng chứng Blockchain và báo cáo PDF có thể được đối chiếu khi giao dịch Sepolia đã được xác nhận.</p><button className="btn story-outline" onClick={onExplore}>Xem lịch sử chiến dịch <ArrowUpRight size={16}/></button></div>
  </div>
  <div className="transparency-disclaimer"><ShieldCheck size={17}/><p>AI chỉ hỗ trợ cảnh báo, không tự động kết luận gian lận. Trạng thái Blockchain chỉ được coi là xác nhận khi có giao dịch thật thành công.</p></div>
 </section>;
}
