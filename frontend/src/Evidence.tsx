import {type FormEvent,useEffect,useState} from 'react';
import {AlertTriangle,ArrowDownToLine,ArrowUpRight,CheckCircle2,ClipboardCheck,CloudUpload,ExternalLink,FileCheck2,FileImage,FileText,Fingerprint,LockKeyhole,ScanText,ShieldCheck,ShieldAlert,X} from 'lucide-react';

export type DocumentInfo={id:string;sha256:string;filename:string;mime:string;ai_status:string;ai_error:string|null;model:string|null;invoice:{vendor:string|null;invoice_number:string|null;total:number|null;currency:string|null;notes:string}|null;warnings:string[]};
export type Attestation={digest:string;status:string;tx_hash:string|null};
export type ReportInfo={id:string;created:string;pdf_hash:string;digest:string;status:string;tx_hash:string|null};
const money=(v:number)=>new Intl.NumberFormat('vi-VN',{style:'currency',currency:'VND',maximumFractionDigits:0}).format(v);
async function request(path:string,body:unknown={}){
 const response=await fetch('/api'+path,{method:'POST',credentials:'same-origin',headers:{'X-Aureva-Request':'1',...(!(body instanceof FormData)?{'Content-Type':'application/json'}:{})},body:body instanceof FormData?body:JSON.stringify(body)});
 const data=await response.json().catch(()=>null);
 if(!response.ok)throw new Error(typeof data?.detail==='string'?data.detail:response.status>=500?'Máy chủ chưa xử lý được yêu cầu. Vui lòng thử lại sau.':'Yêu cầu không hợp lệ.');
 if(data===null)throw new Error('Máy chủ trả về dữ liệu không hợp lệ.');
 return data;
}
const chainStates:Record<string,string>={pending:'Chưa ghi chuỗi',signed:'Đã ký, chờ gửi',submitted:'Chờ xác nhận trên Sepolia',confirmed:'Đã xác nhận trên Sepolia',failed:'Giao dịch thất bại'};
export function ChainActions({id,state,onRefresh,editable}:{id:string;state:Attestation|ReportInfo;onRefresh:()=>Promise<void>;editable:boolean}){
 const[busy,setBusy]=useState(false),[error,setError]=useState('');
 async function act(action:string){setBusy(true);setError('');try{await request('/attestations/'+id+'/'+action);await onRefresh()}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 const confirmed=state.status==='confirmed';
 return <div className="chain-panel chain-v3">
  <div className="chain-v3-header"><div className="chain-v3-emblem"><Fingerprint size={20}/></div><div><strong>Minh chứng Blockchain</strong><small>Chỉ xác nhận khi có bằng chứng giao dịch thực</small></div><span className={'badge '+(confirmed?'confirmed':'pending')}>{confirmed?<CheckCircle2 size={13}/>:<ShieldCheck size={13}/>} {chainStates[state.status]??state.status}</span></div>
  <div className="chain-v3-content">
   <div><small>Mã băm dữ liệu (SHA-256)</small><code className="hash">{state.digest}</code></div>
   {state.tx_hash&&<div><small>Giao dịch Sepolia</small><code className="hash">{state.tx_hash}</code></div>}
  </div>
  <div className="chain-v3-actions">
   <a href={'/api/public/attestations/'+id} target="_blank" rel="noreferrer">Xem dữ liệu xác thực <ArrowUpRight size={14}/></a>
   {state.tx_hash&&<a href={'https://sepolia.etherscan.io/tx/'+state.tx_hash} target="_blank" rel="noreferrer">Kiểm tra trên Etherscan <ExternalLink size={14}/></a>}
   {editable&&state.status!=='confirmed'&&state.status!=='failed'&&<button disabled={busy} className="btn light" onClick={()=>act(state.status==='submitted'?'refresh':'anchor')}>{busy?'Đang kết nối…':state.status==='submitted'?'Kiểm tra xác nhận':'Ghi dấu lên Sepolia'}</button>}
  </div>
  {error&&<p role="alert" className="alert error">{error}</p>}
 </div>;
}
function DocumentPreview({expenseId,filename,mime}:{expenseId:string;filename:string;mime:string}){
 const [url,setUrl]=useState<string|null>(null),[error,setError]=useState(''),[loading,setLoading]=useState(false);
 useEffect(()=>()=>{if(url)URL.revokeObjectURL(url)},[url]);
 async function open(){setLoading(true);setError('');try{
  const response=await fetch('/api/expenses/'+expenseId+'/document',{credentials:'same-origin',headers:{'X-Aureva-Request':'1'}});
  if(!response.ok)throw new Error('Không tải được chứng từ. Kiểm tra quyền truy cập.');
  const data=await response.blob();if(data.size>2_100_000)throw new Error('Kích thước file không hợp lệ.');
  setUrl(URL.createObjectURL(new Blob([data],{type:mime})));
 }catch(e){setError((e as Error).message)}finally{setLoading(false)}}
 return <div className="doc-preview"><div className="doc-preview-heading"><FileImage size={18}/><div><strong>{filename}</strong><small>Chứng từ riêng tư · chỉ người có quyền mới xem được</small></div>{url?<button className="icon-btn" aria-label="Đóng xem trước chứng từ" onClick={()=>setUrl(null)}><X size={17}/></button>:<button className="btn light" disabled={loading} onClick={open}>{loading?'Đang tải…':'Xem chứng từ'}</button>}</div>
  {url&&<div className="doc-preview-frame">{mime==='application/pdf'?<iframe title={'Xem chứng từ '+filename} src={url}/>:<img src={url} alt={'Chứng từ '+filename}/>}</div>}
  {error&&<p role="alert" className="alert error">{error}</p>}
 </div>;
}
export function EvidencePanel({id,status,document,manager,onRefresh,attestation,amount,vendor}:{id:string;status:string;document?:DocumentInfo|null;manager:boolean;onRefresh:()=>Promise<void>;attestation?:Attestation|null;amount?:number;vendor?:string}){
 const[busy,setBusy]=useState(false),[error,setError]=useState('');
 async function execute(fn:()=>Promise<unknown>){setBusy(true);setError('');try{await fn();await onRefresh()}catch(e){setError((e as Error).message);await onRefresh().catch(()=>{})}finally{setBusy(false)}}
 async function upload(e:FormEvent<HTMLFormElement>){e.preventDefault();await execute(()=>request('/expenses/'+id+'/document',new FormData(e.currentTarget)))}
 const analyzed=document?.ai_status==='completed';
 const total=document?.invoice?.total;
 const discrepancy=analyzed&&typeof amount==='number'&&typeof total==='number'&&document.invoice?.currency==='VND'&&amount!==total;
 return <section className="evidence-panel evidence-v3">
  <div className="evidence-panel-heading"><span className="evidence-heading-icon"><ScanText size={20}/></span><div><span className="eyebrow">HỒ SƠ CHỨNG TỪ</span><h4>AI hỗ trợ kiểm tra hóa đơn</h4><p>Hệ thống kiểm tra thông tin trích xuất; người có thẩm quyền quyết định cuối cùng.</p></div><span className={'badge '+(analyzed?'confirmed':'pending')}>{analyzed?'Đã phân tích':document?'Chưa hoàn tất':'Chưa có file'}</span></div>
  {!document?<div className="doc-upload-section"><div className="upload-illustration"><CloudUpload size={35}/><strong>Thêm hóa đơn hoặc chứng từ</strong><small>Ảnh JPG, PNG hoặc PDF · Tối đa 2 MB · PDF tối đa 5 trang</small></div>{manager&&status==='pending'?<form className="upload" onSubmit={upload}><label>Chọn chứng từ từ thiết bị<input required type="file" name="file" accept="image/jpeg,image/png,application/pdf"/></label><button disabled={busy} className="btn primary"><CloudUpload size={16}/> {busy?'Đang tải…':'Tải chứng từ'}</button></form>:<p className="muted"><LockKeyhole size={15}/> Chỉ người phụ trách được tải chứng từ khi khoản chi đang chờ xử lý.</p>}</div>:<>
   <DocumentPreview key={document.id} expenseId={id} filename={document.filename} mime={document.mime}/>
   <div className="evidence-status-line"><span className="badge">{({pending:'Chưa phân tích',processing:'Đang phân tích',completed:'Đã phân tích',failed:'Phân tích lỗi'} as Record<string,string>)[document.ai_status]??document.ai_status}</span><span className="hash">SHA-256: {document.sha256}</span></div>
   {document.invoice&&<div className="ai-result"><div className="ai-result-top"><span><ScanText size={17}/> KẾT QUẢ TRÍCH XUẤT QUA API</span><small>Model: {document.model??'Không xác định'}</small></div><div className="ai-compare">
     <div><small>Số tiền khai báo</small><strong>{typeof amount==='number'?money(amount):'Không có dữ liệu'}</strong><span>Thông tin trên hồ sơ khoản chi</span></div>
     <div><small>AI đọc từ hóa đơn</small><strong>{typeof total==='number'?money(total):'Không đọc được'}</strong><span>{document.invoice.currency??'Chưa xác định loại tiền'}</span></div>
    </div>
    {discrepancy&&<div className="ai-delta"><AlertTriangle size={17}/> Chênh lệch {money(Math.abs((amount??0)-(total??0)))} — cần đối chiếu thủ công</div>}
    <div className="ai-fields"><span>Nhà cung cấp <b>{document.invoice.vendor??'Không đọc được'}</b></span><span>Số hóa đơn <b>{document.invoice.invoice_number??'Không đọc được'}</b></span><span>Đơn vị khai báo <b>{vendor??'Chưa khai báo'}</b></span></div>
    {document.invoice.notes&&<p className="muted">Ghi chú AI: {document.invoice.notes}</p>}
   </div>}
   {document.warnings.length>0?<div className="warnings warnings-v3"><div><ShieldAlert size={18}/><b>{document.warnings.length} điểm cần người có thẩm quyền xác minh</b></div><ul>{document.warnings.map((w,i)=><li key={i}>{w}</li>)}</ul></div>:analyzed&&<div className="ai-safe"><CheckCircle2 size={17}/> Chưa phát hiện chênh lệch theo quy tắc hiện tại. Điều này không chứng minh hóa đơn là thật.</div>}
   {document.ai_error&&<p role="alert" className="alert error">{document.ai_error}</p>}
   {status==='pending'&&!analyzed&&<div className="ai-action"><p className="muted"><LockKeyhole size={15}/> Nội dung chứng từ sẽ được gửi tới OpenAI API khi bạn bấm phân tích. Hãy che thông tin cá nhân không cần thiết.</p><button disabled={busy||document.ai_status==='processing'} className="btn primary" onClick={()=>execute(()=>request('/expenses/'+id+'/analyze'))}><ScanText size={16}/>{busy?'Đang phân tích…':document.ai_status==='processing'?'Đang xử lý':'Phân tích bằng OpenAI'}</button></div>}
  </>}
  {error&&<p role="alert" className="alert error">{error}</p>}
  {attestation&&<ChainActions id={id} state={attestation} onRefresh={onRefresh} editable/>}
 </section>;
}
export function Reports({campaignId,items,editable,onRefresh}:{campaignId:string;items:ReportInfo[];editable:boolean;onRefresh:()=>Promise<void>}){
 const[busy,setBusy]=useState(false),[error,setError]=useState('');
 async function create(){setBusy(true);setError('');try{await request('/campaigns/'+campaignId+'/reports');await onRefresh()}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 return <section className="reports reports-v3">
  <div className="section-head"><div><div className="eyebrow">CHỨNG CỨ CÔNG KHAI</div><h2>Báo cáo & xác minh</h2><p className="muted">Mỗi báo cáo là một bản chốt cố định; các thay đổi sau đó chỉ xuất hiện trong báo cáo mới.</p></div>{editable&&<button className="btn primary" disabled={busy} onClick={create}><FileCheck2 size={17}/>{busy?'Đang chốt báo cáo…':'Tạo báo cáo PDF'}</button>}</div>
  {error&&<p role="alert" className="alert error">{error}</p>}
  {!items.length?<div className="empty compact"><FileText size={24}/> Chưa có báo cáo được chốt.</div>:<div className="report-grid">{items.map(r=><article className="report-card" key={r.id}>
   <div className="report-cover"><span className="report-icon"><FileCheck2 size={26}/></span><span>TRANSPARENCY REPORT</span><small>AUREVA / {r.id.slice(0,8).toUpperCase()}</small></div>
   <div className="report-content"><strong>Báo cáo {new Date(r.created).toLocaleString('vi-VN')}</strong><p>Mã bản chốt: {r.id}</p><a className="btn light" href={'/api/public/reports/'+r.id+'/pdf'}><ArrowDownToLine size={16}/> Tải báo cáo PDF</a>
    <ChainActions id={r.id} state={r} onRefresh={onRefresh} editable={editable}/>
    <div className="report-hash"><small>SHA-256 file PDF</small><code className="hash">{r.pdf_hash}</code></div>
    <VerifyPdf expected={r.pdf_hash}/>
   </div>
  </article>)}</div>}
 </section>;
}
function VerifyPdf({expected}:{expected:string}){
 const[result,setResult]=useState('');
 return <label className="verify-file"><span><ClipboardCheck size={17}/> Tự kiểm tra file PDF bạn đang giữ</span><input type="file" accept="application/pdf" onChange={async e=>{const file=e.target.files?.[0];if(!file)return;try{if(file.size>15_000_000)throw Error('File quá lớn');const digest=await crypto.subtle.digest('SHA-256',await file.arrayBuffer());const hash=Array.from(new Uint8Array(digest),b=>b.toString(16).padStart(2,'0')).join('');setResult(hash===expected?'✓ File PDF khớp với bản được lưu.':'✕ File PDF khác với bản đã được lưu.')}catch{setResult('Không thể kiểm tra file.')}}}/><span role="status">{result}</span><small>Kiểm tra trên thiết bị của bạn, file không được gửi lại máy chủ.</small></label>;
}
