import {useEffect,useState,type FormEvent,type ReactNode} from 'react';
import {ArrowLeft, ArrowRight, KeyRound, LockKeyhole, ShieldCheck, Sparkles} from 'lucide-react';
import './PresentationGate.css';

/**
 * Public visitors automatically enter the real FastAPI/React flow against a separate
 * PostgreSQL schema. It does not log in as a real manager or simulate AI.
 * The server issues a short-lived, signed, HttpOnly presentation cookie.
 * A protected PIN fallback remains available when the public toggle is off.
 */
export function PresentationGate({children}:{children:ReactNode}){
 const [ready,setReady]=useState(false);
 const [unlocked,setUnlocked]=useState(false);
 const [code,setCode]=useState('');
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState('');

 useEffect(()=>{
   let alive=true;
   async function initialize(){
    try{
     const statusResponse=await fetch('/api/demo/status',{credentials:'same-origin',cache:'no-store'});
     const status=statusResponse.ok?await statusResponse.json():null;
     if(status?.enabled===true){
      if(alive)setUnlocked(true);
      return;
     }
     const configResponse=await fetch('/api/demo/config',{credentials:'same-origin',cache:'no-store'});
     const config=configResponse.ok?await configResponse.json():null;
     if(config?.public_demo===true){
      const entry=await fetch('/api/demo/enter',{
       method:'POST',credentials:'same-origin',
       headers:{'Content-Type':'application/json','X-Aureva-Request':'1'},
       body:JSON.stringify({})
      });
      if(!entry.ok){
       const detail=await entry.json().catch(()=>null);
       throw new Error(typeof detail?.detail==='string'?detail.detail:'Không thể mở DEMO công khai.');
      }
      const result=await entry.json();
      if(result?.mode!=='presentation')throw new Error('Không thể xác thực phiên DEMO.');
      if(alive)setUnlocked(true);
     }
    }catch(e){
     if(alive)setError(e instanceof Error?e.message:'Chưa kết nối được chế độ DEMO.');
    }finally{if(alive)setReady(true)}
   }
   void initialize();
   return()=>{alive=false};
 },[]);

 async function unlock(event:FormEvent<HTMLFormElement>){
  event.preventDefault();
  if(busy||!code.trim())return;
  setBusy(true);setError('');
  try{
   const response=await fetch('/api/demo/unlock',{
    method:'POST',credentials:'same-origin',
    headers:{'Content-Type':'application/json','X-Aureva-Request':'1'},
    body:JSON.stringify({code:code.trim()})
   });
   const data=await response.json().catch(()=>null);
   if(!response.ok||data?.mode!=='presentation'){
    throw new Error(typeof data?.detail==='string'?data.detail:'Không mở được chế độ thuyết trình.');
   }
   setCode('');
   setUnlocked(true);
  }catch(e){setError(e instanceof Error?e.message:'Không mở được chế độ thuyết trình.')}
  finally{setBusy(false)}
 }

 if(!ready)return <div className="pg-loading" role="status">Đang mở AUREVA DEMO và chuẩn bị 3 tài khoản…</div>;
 if(unlocked)return <>{children}</>;
 return <main className="pg-page">
  <div className="pg-shell">
   <a className="pg-back" href="/"><ArrowLeft size={17}/> Trở về website AUREVA</a>
   <section className="pg-card" aria-label="Mở chế độ thuyết trình AUREVA">
    <span className="pg-icon"><LockKeyhole size={28}/></span>
    <span className="pg-kicker"><Sparkles size={14}/> AUREVA · PRESENTATION MODE</span>
    <h1>Trải nghiệm đầy đủ.<br/><em>Ba vai trò trong một website.</em></h1>
    <p>Nhập mã của nhóm để thử các thao tác qua backend thật: tạo chiến dịch, đối soát, tải chứng từ, AI phân tích và xác minh giao dịch Ethereum Sepolia.</p>
    <form onSubmit={unlock}>
     <label htmlFor="pg-code">Mã truy cập thuyết trình</label>
     <div className="pg-input-row"><KeyRound size={20}/><input id="pg-code" type="password" autoComplete="off" autoFocus value={code} onChange={e=>setCode(e.target.value)} maxLength={128} placeholder="Nhập mã do trưởng nhóm cung cấp" required/></div>
     <button type="submit" disabled={busy||!code.trim()}>{busy?'Đang xác thực…':'Mở chế độ 3 tài khoản'}<ArrowRight size={17}/></button>
    </form>
    {error&&<div className="pg-error" role="alert">{error}</div>}
    <div className="pg-security"><ShieldCheck size={18}/><span>Chỉ dữ liệu thuyết trình được ghi vào database riêng. Không chuyển tiền thật. AI cần API hoạt động, ký Sepolia cần ví chủ hợp đồng và test ETH.</span></div>
   </section>
  </div>
 </main>;
}
