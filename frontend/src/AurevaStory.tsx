import {ArrowRight,ArrowUpRight,CheckCircle2,ClipboardCheck,FileCheck2,Fingerprint,HandHeart,Heart,HeartHandshake,ShieldCheck,Sparkles,Wallet} from 'lucide-react';
import {motion,useReducedMotion} from 'framer-motion';

type Metrics={raised:number;spent:number;contribution_count:number;campaigns:{id:string}[]};
const fmt=(n:number)=>new Intl.NumberFormat('vi-VN',{maximumFractionDigits:0}).format(n);
const heroImage='https://images.pexels.com/photos/7156189/pexels-photo-7156189.jpeg?auto=compress&cs=tinysrgb&w=1400';
const storyImage='https://images.pexels.com/photos/6590929/pexels-photo-6590929.jpeg?auto=compress&cs=tinysrgb&w=1000';
export function AurevaMark({size=35}:{size?:number}){
 return <svg width={size} height={size} viewBox="0 0 48 48" fill="none" aria-hidden="true">
  <path d="M7 26.5c7-1.2 9.5-13 17-13 7.3 0 10 11.8 17 13" stroke="currentColor" strokeWidth="4.2" strokeLinecap="round"/>
  <path d="M8 34c6.6-1.6 10-9.1 16-9.1 6.1 0 9.4 7.5 16 9.1" stroke="currentColor" strokeWidth="4.2" strokeLinecap="round" opacity=".53"/>
  <circle cx="24" cy="9" r="3.5" fill="#F5A483"/>
  <circle cx="8.5" cy="26.5" r="2.3" fill="currentColor"/>
  <circle cx="39.5" cy="26.5" r="2.3" fill="currentColor"/>
 </svg>;
}
export function PublicIntro({data,onExplore,onTransparency}:{data:Metrics|null;onExplore:()=>void;onTransparency:()=>void}){
 const reduced=useReducedMotion();
 return <>
 <section className="hero heart-hero" aria-label="AUREVA - nền tảng cứu trợ minh bạch">
  <div className="heart-hero-copy">
   <motion.div className="heart-hero-eyebrow" initial={reduced?false:{opacity:0,y:9}} animate={{opacity:1,y:0}}><span className="heart-eyebrow-line"/> AUREVA · NỀN TẢNG CỨU TRỢ MINH BẠCH</motion.div>
   <motion.h1 initial={reduced?false:{opacity:0,y:22}} animate={{opacity:1,y:0}} transition={{duration:.62,delay:.07}}>Cho đi bằng<br/><em>cả tấm lòng.</em><br/>Minh bạch bằng<br/>sự thật.</motion.h1>
   <motion.p initial={reduced?false:{opacity:0,y:17}} animate={{opacity:1,y:0}} transition={{duration:.6,delay:.15}}>Trao gửi yêu thương, rõ từng đóng góp. AUREVA giúp mỗi chiến dịch cứu trợ công khai tiền thực nhận, khoản chi được duyệt và hành trình kiểm chứng.</motion.p>
   <div className="heart-hero-actions"><button className="btn primary" onClick={onExplore}>Khám phá chiến dịch <ArrowUpRight size={18}/></button><button className="btn ghost" onClick={onTransparency}>Xem sự minh bạch <ArrowRight size={17}/></button></div>
   <div className="heart-hero-bottom"><span><CheckCircle2 size={15}/> Dữ liệu đối soát thực tế</span><span><ShieldCheck size={15}/> Có người phê duyệt</span></div>
  </div>
  <div className="heart-hero-visual">
   <img src={heroImage} alt="Nhóm tình nguyện viên sắp xếp các thùng đồ quyên góp" loading="eager" fetchPriority="high"/>
   <div className="heart-photo-shade"/>
   <span className="heart-photo-corner">KẾT NỐI <Heart fill="currentColor" size={15}/> TỬ TẾ</span>
   <div className="heart-photo-quote"><span className="heart-quote-star">✳</span><strong>Trao đi niềm tin.<br/>Giữ lại bằng chứng.</strong><span>Mọi chiến dịch xứng đáng được kiểm chứng.</span></div>
   <small className="heart-photo-credit">Ảnh minh họa hoạt động tình nguyện · Gustavo Fring / Pexels</small>
  </div>
 </section>
 <div className="story-ribbon heart-facts">
  <div className="ribbon-lead"><span className="ribbon-asterisk"><HeartHandshake size={22}/></span><div><b>Lòng tốt cần được nhìn thấy.</b><small>Số liệu được đọc từ hệ thống, không phải con số quảng cáo.</small></div></div>
  <div className="ribbon-item"><small>Đã đối soát</small><strong>{data?fmt(data.raised)+' ₫':'Đang tải…'}</strong></div>
  <div className="ribbon-item"><small>Chi đã phê duyệt</small><strong>{data?fmt(data.spent)+' ₫':'Đang tải…'}</strong></div>
  <div className="ribbon-item"><small>Chiến dịch</small><strong>{data?fmt(data.campaigns.length):'…'}</strong></div>
 </div>
 </>;
}
export function HumanStory({onTransparency}:{onTransparency:()=>void}){
 const steps=[
  {n:'01',name:'Bạn gửi đi sự sẻ chia',desc:'Ghi nhận khoản đóng góp; chỉ cập nhật vào tổng quỹ khi người phụ trách xác nhận tiền thực nhận.',icon:<HandHeart size={21}/>},
  {n:'02',name:'Khoản chi có chứng từ',desc:'Người phụ trách tải hóa đơn, AI phân tích các điểm đáng chú ý, người phê duyệt trực tiếp ra quyết định.',icon:<ClipboardCheck size={21}/>},
  {n:'03',name:'Cộng đồng có thể kiểm chứng',desc:'Báo cáo PDF, dấu SHA-256 và chứng nhận Sepolia (nếu đã ghi chuỗi thành công) được công khai.',icon:<Fingerprint size={21}/>}
 ];
 return <section className="human-story" aria-label="Hành trình của một khoản quyên góp">
  <div className="human-story-photo">
   <img src={storyImage} alt="Tình nguyện viên chuẩn bị những hộp quà cứu trợ" loading="lazy"/>
   <div className="human-story-photo-caption"><span>ĐÂU ĐÓ, MỘT SỰ GIÚP ĐỠ ĐANG ĐƯỢC CHUẨN BỊ.</span><small>Ảnh minh họa · cottonbro studio / Pexels. Không phải hoạt động của một chiến dịch AUREVA cụ thể.</small></div>
  </div>
  <div className="human-story-copy">
   <div className="human-story-kicker"><span/> MINH BẠCH KHÔNG CÓ NGHĨA LÀ KHÔ KHAN</div>
   <h2>Điều đẹp nhất là<br/>lòng tốt được <em>đi đúng nơi.</em></h2>
   <p className="human-story-intro">Một khoản ủng hộ không nên biến mất sau nút gửi. Mọi người cần biết hành trình tiếp theo đã diễn ra như thế nào.</p>
   <div className="human-story-steps">{steps.map(s=><div className="human-story-step" key={s.n}><span className="human-step-count">{s.n}</span><div className="human-step-icon">{s.icon}</div><div><h3>{s.name}</h3><p>{s.desc}</p></div></div>)}</div>
   <button className="human-story-link" onClick={onTransparency}>Khám phá cách AUREVA hoạt động <ArrowUpRight size={18}/></button>
  </div>
 </section>;
}
export function TransparencyHub({data,onExplore}:{data:Metrics|null;onExplore:()=>void}){
 const percent=data&&data.raised>0?Math.min(100,Math.max(0,data.spent/data.raised*100)):0;
 return <section className="transparency-hub">
  <div className="detail-head transparency-heading"><div className="eyebrow"><Sparkles size={16}/> HIỂU RÕ TỪNG QUYẾT ĐỊNH</div><h1>Minh bạch không<br/><em>chỉ là một lời hứa.</em></h1><p>AUREVA tổng hợp đóng góp đã đối soát và khoản chi đã được duyệt từ database. Mỗi chiến dịch có thông tin và báo cáo để cộng đồng đối chiếu.</p></div>
  <div className="transparency-board">
   <div className="transparency-chart">
    <div className="panel-top"><span>GÓC NHÌN TÀI CHÍNH</span><span className="panel-chip"><span/> DỮ LIỆU TỪ HỆ THỐNG</span></div>
    <h2>Điều gì đang diễn ra với nguồn quỹ?</h2>
    <div className="money-balance"><div><span>Tổng thu đã đối soát</span><b>{data?fmt(data.raised)+' ₫':'Đang tải…'}</b></div><div><span>Khoản chi đã duyệt</span><b>{data?fmt(data.spent)+' ₫':'Đang tải…'}</b></div><div><span>Số dư tính toán</span><b>{data?fmt(data.raised-data.spent)+' ₫':'Đang tải…'}</b></div></div>
    <div className="proportion-bar" role="img" aria-label={data?'Khoản chi được duyệt chiếm '+percent.toFixed(1)+'% tổng thu đã đối soát':'Chưa tải dữ liệu'}><span style={{width:percent+'%'}}/></div>
    <div className="proportion-legend"><span><i/> Số tiền đã đối soát</span><span><i/> Khoản chi được duyệt</span></div>
    <p className="small-disclosure">Khoản chi được duyệt là quyết định sử dụng kinh phí, không tự động chứng minh ngân hàng đã chuyển tiền.</p>
   </div>
   <div className="transparency-ethos"><span className="ethos-icon"><FileCheck2 size={32}/></span><div className="eyebrow">BẰNG CHỨNG TẠO NÊN NIỀM TIN</div><h2>Có chứng từ.<br/><em>Có trách nhiệm.</em></h2><p>AI đọc hóa đơn và nêu các điểm cần xem xét. Người phê duyệt đưa ra quyết định. Blockchain lưu dấu kiểm chứng khi đã có giao dịch thật trên Sepolia.</p><button className="btn story-outline" onClick={onExplore}>Xem hồ sơ chiến dịch <ArrowUpRight size={16}/></button></div>
  </div>
  <div className="transparency-disclaimer"><ShieldCheck size={17}/><p>AI chỉ hỗ trợ kiểm tra, không tự kết luận gian lận. Trạng thái xác nhận Blockchain chỉ hiển thị khi giao dịch thực sự thành công.</p></div>
 </section>;
}
