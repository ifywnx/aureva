import {useState, type FormEvent} from 'react';
import {CircleAlert, ClipboardCheck, ShieldAlert} from 'lucide-react';

type ReviewRecord={
 id:string;
 document?:{ai_status:string;warnings:string[]}|null;
};
export function ApprovalForm({record,busy,onDecision}:{
 record:ReviewRecord;
 busy:boolean;
 onDecision:(event:FormEvent<HTMLFormElement>,id:string)=>void;
}){
 const [decision,setDecision]=useState<'approved'|'rejected'>('approved');
 const warnings=record.document?.warnings??[];
 const ready=record.document?.ai_status==='completed';
 const approving=decision==='approved';
 return <form className="decision work-decision" onSubmit={event=>onDecision(event,record.id)}>
  <label>Lý do phê duyệt hoặc từ chối
   <input name="reason" required minLength={approving&&warnings.length>0?15:5} maxLength={1000}
    placeholder={approving&&warnings.length?'Ghi rõ cách đã đối chiếu chênh lệch/chứng từ…':'Nêu rõ nội dung đã kiểm tra…'}/>
  </label>
  <label>Quyết định
   <select name="status" value={decision} onChange={event=>setDecision(event.target.value as 'approved'|'rejected')}>
    <option value="approved">Phê duyệt</option>
    <option value="rejected">Từ chối</option>
   </select>
  </label>
  {approving&&warnings.length>0&&<label className="review-warning-check">
   <input type="checkbox" name="warnings_acknowledged" value="true" required/>
   <span><ShieldAlert size={17}/> Tôi đã xem và đối chiếu {warnings.length} cảnh báo AI với chứng từ gốc. Tôi chịu trách nhiệm cho quyết định và ghi lý do cụ thể ở trên.</span>
  </label>}
  {approving&&!ready&&<p className="review-warning-note"><CircleAlert size={16}/> Chưa có kết quả phân tích AI. Cần hoàn thành bước này trước khi phê duyệt; vẫn có thể từ chối khoản chi.</p>}
  <button disabled={busy||(approving&&!ready)} className="btn primary"><ClipboardCheck size={16}/> Lưu quyết định</button>
  <small><CircleAlert size={14}/> AI chỉ hỗ trợ cảnh báo. Quyết định và xác nhận cảnh báo được lưu vào lịch sử kiểm toán.</small>
 </form>;
}
