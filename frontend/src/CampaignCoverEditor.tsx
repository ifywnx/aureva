import {useEffect,useState,type ChangeEvent} from 'react';
import {Camera,CheckCircle2,ImagePlus,RefreshCw} from 'lucide-react';

export function CampaignCoverEditor({id,coverUrl,onSaved}:{id:string;coverUrl:string|null;onSaved:()=>Promise<void>}){
 const [file,setFile]=useState<File|null>(null),[preview,setPreview]=useState<string|null>(null),
       [saving,setSaving]=useState(false),[error,setError]=useState(''),[done,setDone]=useState(false);
 useEffect(()=>{
  if(!file){setPreview(null);return}
  const objectUrl=URL.createObjectURL(file);
  setPreview(objectUrl);
  return ()=>URL.revokeObjectURL(objectUrl);
 },[file]);
 function choose(e:ChangeEvent<HTMLInputElement>){
  setError('');setDone(false);
  const candidate=e.target.files?.[0]??null;
  if(candidate && (!['image/jpeg','image/png','image/webp'].includes(candidate.type)||candidate.size>2_000_000)){
   setError('Chọn ảnh JPG/PNG/WebP không quá 2 MB.');
   setFile(null);
   e.target.value='';
   return;
  }
  setFile(candidate);
 }
 async function save(){
  if(!file)return;
  setSaving(true);setError('');setDone(false);
  try{
   const form=new FormData();form.append('file',file);
   const response=await fetch('/api/campaigns/'+encodeURIComponent(id)+'/cover',{
      method:'POST',credentials:'same-origin',headers:{'X-Aureva-Request':'1'},body:form
   });
   const data=await response.json().catch(()=>null);
   if(!response.ok)throw new Error(typeof data?.detail==='string'?data.detail:'Không thể lưu ảnh bìa.');
   await onSaved();
   setFile(null);setDone(true);
  }catch(e){setError(e instanceof Error?e.message:'Không lưu được ảnh bìa.')}finally{setSaving(false)}
 }
 return <div className="campaign-cover-editor">
   <div className="cover-editor-heading"><span><Camera size={16}/> Ảnh bìa chiến dịch</span><small>Lưu bền vững trong database</small></div>
   <div className="cover-editor-body">
     <div className="cover-editor-thumb">
       {preview||coverUrl?<img src={preview||coverUrl||''} alt="Xem trước ảnh bìa chiến dịch"/>:<ImagePlus size={24}/>}
     </div>
     <div className="cover-editor-controls">
       <label className="cover-upload-select">Chọn ảnh thực tế (JPG, PNG, WebP)
         <input type="file" accept="image/jpeg,image/png,image/webp" onChange={choose} aria-label="Chọn ảnh bìa chiến dịch"/>
       </label>
       <small>Chỉ người phụ trách chiến dịch có quyền cập nhật. Không dùng ảnh người khác khi chưa được phép.</small>
       {file&&<button className="btn primary" disabled={saving} onClick={save}><RefreshCw size={15}/>{saving?'Đang lưu ảnh…':'Lưu ảnh bìa'}</button>}
       {done&&<span className="cover-editor-success" role="status"><CheckCircle2 size={15}/> Đã lưu ảnh vào hệ thống.</span>}
       {error&&<span className="alert error" role="alert">{error}</span>}
     </div>
   </div>
 </div>;
}
