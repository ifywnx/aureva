import {useState} from 'react';
import {ArrowRight,ArrowUpRight,BrainCircuit,CheckCircle2,ClipboardCheck,FileCheck2,HeartHandshake,ReceiptText,ShieldCheck,Waypoints} from 'lucide-react';

const stages=[
  {number:'01',title:'Tạo chiến dịch',short:'Chiến dịch',role:'Người phụ trách',icon:HeartHandshake,
   detail:'Đặt tên, mục tiêu và khu vực cứu trợ. Mỗi chiến dịch có trang công khai để cộng đồng theo dõi.',
   evidence:'Mục tiêu · địa phương · người phụ trách',tag:'Điểm khởi đầu'},
  {number:'02',title:'Đóng góp & đối soát',short:'Đối soát',role:'Người ủng hộ + phụ trách',icon:CheckCircle2,
   detail:'Khoản đóng góp được ghi nhận trước, sau đó người phụ trách kiểm tra tiền thực nhận. Chỉ tiền đã đối soát được cộng vào tổng thu.',
   evidence:'Thông tin đóng góp · trạng thái xác nhận',tag:'Dữ liệu có kiểm chứng'},
  {number:'03',title:'Tạo khoản chi',short:'Chứng từ',role:'Người phụ trách',icon:ReceiptText,
   detail:'Mỗi khoản chi ghi số tiền, đơn vị nhận và có ảnh hóa đơn hoặc PDF làm căn cứ kiểm tra.',
   evidence:'Hồ sơ khoản chi · SHA-256 chứng từ',tag:'Có chứng cứ'},
  {number:'04',title:'AI kiểm tra',short:'OpenAI',role:'AI hỗ trợ phân tích',icon:BrainCircuit,
   detail:'OpenAI đọc nội dung chứng từ thực, so sánh số tiền và cảnh báo trùng lặp. Cảnh báo là gợi ý cần xem lại, không phải kết luận gian lận.',
   evidence:'Kết quả trích xuất · cảnh báo chênh lệch',tag:'AI không tự phê duyệt'},
  {number:'05',title:'Duyệt hoặc từ chối',short:'Phê duyệt',role:'Người phê duyệt',icon:ClipboardCheck,
   detail:'Người có thẩm quyền tự đối chiếu chứng từ và ghi quyết định kèm lý do. Người tạo khoản chi không được tự phê duyệt.',
   evidence:'Quyết định · lý do · lịch sử',tag:'Con người chịu trách nhiệm'},
  {number:'06',title:'Công khai & xác thực',short:'Blockchain',role:'Hệ thống / cộng đồng',icon:FileCheck2,
   detail:'Báo cáo PDF có mã SHA-256. Quyết định có dấu xác thực Blockchain chỉ khi giao dịch Sepolia thực tế được xác nhận.',
   evidence:'Báo cáo PDF · mã băm · TX nếu có',tag:'Cộng đồng tự kiểm tra'}
];

export function JourneyFlow({onTransparency}:{onTransparency:()=>void}){
 const [active,setActive]=useState(0);
 const item=stages[active];
 const Icon=item.icon;
 return <section className="journey-flow" aria-labelledby="journey-flow-title">
   <div className="journey-flow-heading">
     <div>
       <span className="journey-kicker"><Waypoints size={16}/> AUREVA FLOW / 06 CHẶNG MINH BẠCH</span>
       <h2 id="journey-flow-title">Một hành động tử tế.<br/><em>Một hành trình rõ ràng.</em></h2>
       <p>Từ đóng góp tới báo cáo, các bước trong AUREVA kết nối thành một quy trình có trách nhiệm — không chỉ là các tính năng đứng riêng lẻ.</p>
     </div>
     <button className="journey-summary-action" onClick={onTransparency}>Xem dữ liệu minh bạch <ArrowUpRight size={17}/></button>
   </div>
   <div className="journey-line" aria-label="Chọn một bước trong quy trình minh bạch">
     {stages.map((s,index)=>{
       const StageIcon=s.icon;
       return <button key={s.number} className={'journey-step '+(active===index?'is-active':'')} onClick={()=>setActive(index)}
          aria-pressed={active===index} aria-label={'Bước '+s.number+': '+s.title}>
          <span className="journey-step-disc"><StageIcon size={20}/></span>
          <span className="journey-step-number">BƯỚC {s.number}</span>
          <strong>{s.short}</strong>
       </button>;
     })}
   </div>
   <div className="journey-focus" key={item.number}>
     <div className="journey-focus-copy">
       <div className="journey-focus-intro"><span className="journey-focus-index">{item.number} / 06</span><span className="journey-focus-pill">{item.tag}</span></div>
       <h3>{item.title}</h3>
       <p>{item.detail}</p>
       <span className="journey-focus-role"><ShieldCheck size={17}/> {item.role}</span>
       <div className="journey-focus-actions"><button onClick={()=>setActive((active+1)%stages.length)} className="journey-next">Bước tiếp theo <ArrowRight size={17}/></button></div>
     </div>
     <div className="journey-proof" aria-label="Loại chứng cứ được lưu tại bước đang chọn">
       <div className="journey-proof-top"><span>MINH CHỨNG TRONG HỆ THỐNG</span><span className="journey-proof-dots"><i/><i/><i/></span></div>
       <div className="journey-proof-symbol"><Icon size={48} strokeWidth={1.35}/></div>
       <div className="journey-proof-content"><small>{'AUREVA / PROCESS '+item.number}</small><strong>{item.evidence}</strong><span><CheckCircle2 size={15}/> Mô tả nghiệp vụ · không phải bản ghi giao dịch</span></div>
     </div>
   </div>
 </section>;
}
