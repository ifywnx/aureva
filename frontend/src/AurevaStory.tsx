import {ArrowDownRight, ArrowRight, CheckCircle2, CircleDollarSign, Fingerprint, Heart, Leaf, ShieldCheck, Sparkles, Waves} from 'lucide-react';
import {motion, useReducedMotion} from 'framer-motion';

type Metrics = {raised:number;spent:number;contribution_count:number;campaigns:{id:string}[]};
const fmt=(amount:number)=>new Intl.NumberFormat('vi-VN',{maximumFractionDigits:0}).format(amount);
export function AurevaMark({size=35}:{size?:number}){
  return <svg width={size} height={size} viewBox="0 0 48 48" fill="none" aria-hidden="true">
    <path d="M7 26.5c7-1.2 9.5-13 17-13 7.3 0 10 11.8 17 13" stroke="currentColor" strokeWidth="4.2" strokeLinecap="round"/>
    <path d="M8 34c6.6-1.6 10-9.1 16-9.1 6.1 0 9.4 7.5 16 9.1" stroke="currentColor" strokeWidth="4.2" strokeLinecap="round" opacity=".53"/>
    <circle cx="24" cy="9" r="3.5" fill="#FFAE91"/>
    <circle cx="8.5" cy="26.5" r="2.3" fill="currentColor"/>
    <circle cx="39.5" cy="26.5" r="2.3" fill="currentColor"/>
  </svg>;
}

function ReliefNetwork(){
  const reduced = useReducedMotion();
  return <div className="relief-network" aria-hidden="true">
    <div className="network-field"/>
    <svg className="network-lines" viewBox="0 0 560 470" preserveAspectRatio="xMidYMid meet" fill="none">
      <path className="network-contour" d="M35 179c93-112 155-135 259-88 105 48 153 18 236-68M-8 310c122-107 200-127 294-50 79 66 159 84 296-23M39 421c87-110 187-124 291-74 104 49 156 14 231-37"/>
      <path className="network-path" d="M72 292Q156 182 255 239T445 137" strokeWidth="2.3" strokeDasharray="7 9"/>
      <path className="network-path faint" d="M91 350Q165 415 286 333T487 308" strokeWidth="1.4" strokeDasharray="5 11"/>
      <circle cx="72" cy="292" r="7" fill="#F3B594"/>
      <circle cx="255" cy="239" r="9" fill="#B8E6DC"/>
      <circle cx="445" cy="137" r="7" fill="#F3B594"/>
      <circle cx="91" cy="350" r="5" fill="#B8E6DC"/>
      <circle cx="286" cy="333" r="5" fill="#B8E6DC"/>
    </svg>
    <motion.div className="network-center" initial={reduced?false:{opacity:0,scale:.9}} animate={{opacity:1,scale:1}} transition={{duration:.8}}>
      <span className="network-center-icon"><Heart size={31} strokeWidth={1.8}/></span>
      <span className="network-center-label">MỖI ĐÓNG GÓP</span>
      <strong>Đều có<br/>giá trị.</strong>
      <span className="network-center-foot"><CheckCircle2 size={14}/> Rõ ràng từng bước</span>
    </motion.div>
    <div className="network-pill network-pill-a"><span className="network-pill-symbol"><CircleDollarSign size={16}/></span><span><b>Đối soát</b><small>Khoản tiền thực nhận</small></span></div>
    <div className="network-pill network-pill-b"><span className="network-pill-symbol warm"><ShieldCheck size={16}/></span><span><b>Phê duyệt</b><small>Quyết định có trách nhiệm</small></span></div>
    <div className="network-pill network-pill-c"><span className="network-pill-symbol"><Fingerprint size={16}/></span><span><b>Đối chiếu</b><small>Báo cáo và mã xác thực</small></span></div>
    <span className="network-point point-a"/><span className="network-point point-b"/>
  </div>;
}

export function PublicIntro({data,onExplore,onTransparency}:{data:Metrics|null;onExplore:()=>void;onTransparency:()=>void}){
  const reduced=useReducedMotion();
  return <>
    <section className="hero" aria-label="Giới thiệu AUREVA">
      <div className="hero-copy">
        <motion.div className="hero-topline" initial={reduced?false:{opacity:0,y:8}} animate={{opacity:1,y:0}} transition={{duration:.6}}>
          <span className="hero-spark"><Waves size={15}/></span>
          NỀN TẢNG MINH BẠCH CỨU TRỢ
        </motion.div>
        <motion.h1 initial={reduced?false:{opacity:0,y:23}} animate={{opacity:1,y:0}} transition={{duration:.7,delay:.06}}>
          Khi sự sẻ chia<br/>có <em>đường đi rõ ràng.</em>
        </motion.h1>
        <motion.p initial={reduced?false:{opacity:0,y:15}} animate={{opacity:1,y:0}} transition={{duration:.7,delay:.14}}>
          AUREVA kết nối những tấm lòng và giúp cộng đồng theo dõi số tiền đã xác nhận, khoản chi được duyệt cùng các báo cáo của từng chiến dịch.
        </motion.p>
        <div className="hero-actions">
          <button className="btn primary" onClick={onExplore}>Khám phá chiến dịch <ArrowRight size={17}/></button>
          <button className="btn story-outline" onClick={onTransparency}>Xem cách minh bạch <ArrowDownRight size={17}/></button>
        </div>
        <div className="hero-assurances">
          <span><CheckCircle2 size={16}/> Không hiển thị thông tin người đóng góp</span>
          <span><Leaf size={16}/> Chỉ cộng số tiền đã đối soát</span>
        </div>
      </div>
      <ReliefNetwork/>
      <div className="hero-corner-index" aria-hidden="true">AUREVA / 01—04</div>
    </section>
    <div className="story-ribbon" aria-label="Tóm tắt dữ liệu công khai">
      <div className="ribbon-lead"><span className="ribbon-asterisk">✳</span><div><b>Sự tin tưởng đến từ dữ liệu.</b><small>Cập nhật theo trạng thái xác nhận thực tế</small></div></div>
      <div className="ribbon-item"><small>Đóng góp đã đối soát</small><strong>{data?fmt(data.raised)+' ₫':'Đang tải…'}</strong></div>
      <div className="ribbon-item"><small>Chi đã được duyệt</small><strong>{data?fmt(data.spent)+' ₫':'Đang tải…'}</strong></div>
      <div className="ribbon-item"><small>Chiến dịch</small><strong>{data?fmt(data.campaigns.length):'…'}</strong></div>
    </div>
  </>;
}

export function TransparencyHub({data,onExplore}:{data:Metrics|null;onExplore:()=>void}){
  const percent=data&&data.raised>0?Math.min(100,Math.max(0,data.spent/data.raised*100)):0;
  return <section className="transparency-hub">
    <div className="detail-head transparency-heading">
      <div className="eyebrow"><Sparkles size={16}/> CÔNG KHAI THAY VÌ CAM KẾT SUÔNG</div>
      <h1>Mọi con số đều cần <em>lời giải thích.</em></h1>
      <p>AUREVA tổng hợp đóng góp đã đối soát và khoản chi đã được phê duyệt. Mỗi chiến dịch có lịch sử thu chi riêng để cộng đồng tự kiểm tra.</p>
    </div>
    <div className="transparency-board">
      <div className="transparency-chart">
        <div className="panel-top"><span>GÓC NHÌN TÀI CHÍNH</span><span className="panel-chip"><span/> DỮ LIỆU THỰC</span></div>
        <h2>Thu – chi được thể hiện tách bạch.</h2>
        <div className="money-balance">
          <div><span>Tổng thu đã đối soát</span><b>{data?fmt(data.raised)+' ₫':'…'}</b></div>
          <div><span>Khoản chi đã duyệt</span><b>{data?fmt(data.spent)+' ₫':'…'}</b></div>
          <div><span>Số dư tính toán</span><b>{data?fmt(data.raised-data.spent)+' ₫':'…'}</b></div>
        </div>
        <div className="proportion-bar" role="img" aria-label={data?'Khoản chi được duyệt chiếm '+percent.toFixed(1)+'% tổng thu đã đối soát':'Chưa tải dữ liệu'}><span style={{width:percent+'%'}}/></div>
        <div className="proportion-legend"><span><i/> Tổng đã đối soát</span><span><i/> Phần chi đã duyệt</span></div>
        <p className="small-disclosure">“Chi đã duyệt” là quyết định phân bổ nguồn tiền, không tự động chứng minh đã chuyển tiền tại ngân hàng.</p>
      </div>
      <div className="transparency-ethos">
        <span className="ethos-icon"><Fingerprint size={35}/></span>
        <div className="eyebrow">KHÔNG CHỈ LÀ MỘT DÒNG SỐ</div>
        <h2>Kiểm tra được.<br/><em>Đối chiếu được.</em></h2>
        <p>Hệ thống lưu chứng từ riêng tư, hỗ trợ người phê duyệt xem cảnh báo AI, tạo báo cáo PDF và theo dõi dấu xác thực trên Sepolia khi đã được cấu hình.</p>
        <button className="btn story-outline" onClick={onExplore}>Xem lịch sử từng chiến dịch <ArrowRight size={16}/></button>
      </div>
    </div>
    <div className="transparency-disclaimer"><ShieldCheck size={17}/><p>AI chỉ hỗ trợ đọc và cảnh báo; người có trách nhiệm luôn là người đưa ra quyết định cuối cùng. Blockchain chỉ được xác nhận khi giao dịch thật có bằng chứng trên chuỗi.</p></div>
  </section>;
}
