import {type ReactNode} from 'react';
import {ArrowRight, CheckCircle2, FileCheck2, HeartHandshake, ShieldCheck, Wallet} from 'lucide-react';
import {motion, useReducedMotion} from 'framer-motion';

const stages: {number:string; title:string; detail:string; icon:ReactNode; tone:string}[] = [
  {number:'01',title:'Ghi nhận đóng góp',detail:'Người ủng hộ gửi thông tin và mã tham chiếu để người phụ trách kiểm tra.',icon:<HeartHandshake size={22}/>,tone:'ocean'},
  {number:'02',title:'Đối soát thực nhận',detail:'Khoản đóng góp chỉ được tính vào tổng tiền sau khi xác nhận đã nhận.',icon:<Wallet size={22}/>,tone:'sky'},
  {number:'03',title:'Kiểm tra & phê duyệt',detail:'Người phụ trách gửi khoản chi, chứng từ; người có thẩm quyền xem xét.',icon:<ShieldCheck size={22}/>,tone:'coral'},
  {number:'04',title:'Công khai báo cáo',detail:'Tổng hợp số liệu, quyết định và báo cáo để cộng đồng cùng đối chiếu.',icon:<FileCheck2 size={22}/>,tone:'teal'}
];

export function ImpactJourney(){
  const reduce=useReducedMotion();
  return <section className="impact-journey" aria-labelledby="journey-heading">
    <div className="journey-heading">
      <div>
        <span className="eyebrow journey-kicker"><span className="journey-kicker-dot"/> QUY TRÌNH MINH BẠCH</span>
        <h2 id="journey-heading">Mỗi đóng góp đều có <em>một hành trình rõ ràng.</em></h2>
        <p>Không chỉ nhìn thấy số tiền, bạn có thể hiểu cách khoản đóng góp được ghi nhận, kiểm tra và công khai.</p>
      </div>
      <div className="journey-seal"><CheckCircle2 size={18}/><span>Rõ ràng từng bước</span></div>
    </div>
    <div className="journey-path" role="list">
      {stages.map((stage,index)=><motion.article role="listitem" className={'journey-step tone-'+stage.tone} key={stage.number}
        initial={reduce?false:{opacity:0,y:24}}
        whileInView={{opacity:1,y:0}}
        viewport={{once:true,amount:.2}}
        transition={{delay:reduce?0:index*.09,duration:.48,ease:'easeOut'}}
        whileHover={reduce?undefined:{y:-6}}>
        <div className="journey-step-top">
          <div className="journey-icon">{stage.icon}</div>
          <span className="journey-step-number">{stage.number}</span>
        </div>
        <h3>{stage.title}</h3>
        <p>{stage.detail}</p>
        {index<stages.length-1&&<span className="journey-next" aria-hidden="true"><ArrowRight size={18}/></span>}
      </motion.article>)}
    </div>
    <div className="journey-footnote"><ShieldCheck size={16}/><span>Minh họa quy trình vận hành. Trạng thái thực tế của mỗi khoản chi và tích hợp AI/Blockchain được hiển thị riêng trong hệ thống.</span></div>
  </section>;
}
