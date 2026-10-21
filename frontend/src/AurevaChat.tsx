import {useEffect,useRef,useState,type FormEvent} from 'react';
import {AnimatePresence,motion,useReducedMotion} from 'framer-motion';
import {ArrowUpRight,Bot,ChevronDown,HeartHandshake,MessageCircle,RotateCcw,Send,ShieldCheck,Sparkles,X} from 'lucide-react';
import './AurevaChat.css';

type Turn={role:'assistant'|'user';content:string;status?:'error'};
type ChatResponse={reply:string;model:string;data_status:string;campaign_count:number};
const HELLO:Turn={role:'assistant',content:'Xin chào! Mình là AUREVA AI. Bạn có thể hỏi về quy trình đóng góp, minh bạch thu chi hoặc các chiến dịch đang có trên hệ thống.'};
const suggestions=[
 'AUREVA minh bạch quyên góp thế nào?',
 'Hiện có chiến dịch cứu trợ nào?',
 'Tôi muốn đóng góp thì làm sao?',
 'AI và Blockchain dùng để làm gì?'
];

export function AurevaChat(){
 const[open,setOpen]=useState(false);
 const[messages,setMessages]=useState<Turn[]>([HELLO]);
 const[draft,setDraft]=useState('');
 const[busy,setBusy]=useState(false);
 const[error,setError]=useState('');
 const[connected,setConnected]=useState(false);
 const inputRef=useRef<HTMLTextAreaElement|null>(null);
 const endRef=useRef<HTMLDivElement|null>(null);
 const abortRef=useRef<AbortController|null>(null);
 const reduced=useReducedMotion();
 useEffect(()=>{
   if(open){const id=window.setTimeout(()=>inputRef.current?.focus(),160);return()=>window.clearTimeout(id)}
 },[open]);
 useEffect(()=>{if(open)endRef.current?.scrollIntoView({block:'end',behavior:reduced?'instant':'smooth'})},[messages,busy,error,open,reduced]);
 useEffect(()=>{
   if(!open)return;
   const onKey=(e:KeyboardEvent)=>{if(e.key==='Escape'){setOpen(false)}};
   window.addEventListener('keydown',onKey);
   return()=>window.removeEventListener('keydown',onKey);
 },[open]);
 useEffect(()=>()=>abortRef.current?.abort(),[]);

 async function send(text=draft){
  const question=text.trim();
  if(busy||question.length<2||question.length>750)return;
  const previous=messages.filter(m=>m.status!=='error').slice(-8).map(({role,content})=>({role,content}));
  const controller=new AbortController();
  abortRef.current=controller;
  setDraft('');setError('');setBusy(true);
  setMessages(items=>[...items,{role:'user',content:question}]);
  try{
   const response=await fetch('/api/public/assistant/chat',{
    method:'POST',
    credentials:'same-origin',
    headers:{'Content-Type':'application/json','X-Aureva-Request':'1'},
    signal:controller.signal,
    body:JSON.stringify({message:question,history:previous}),
   });
   const data=await response.json().catch(()=>null) as (ChatResponse&{detail?:string})|null;
   if(!response.ok)throw new Error(typeof data?.detail==='string'?data.detail:'Trợ lý tạm thời không trả lời được. Vui lòng thử lại.');
   if(!data||typeof data.reply!=='string'||!data.reply.trim())throw new Error('Dữ liệu trả lời chưa hợp lệ.');
   setConnected(data.data_status==='connected');
   setMessages(items=>[...items,{role:'assistant',content:data.reply}]);
  }catch(e){
   if(controller.signal.aborted)return;
   setError(e instanceof Error?e.message:'Trợ lý tạm thời chưa kết nối được.');
   setConnected(false);
  }finally{
   if(abortRef.current===controller)abortRef.current=null;
   setBusy(false);
  }
 }
 function reset(){abortRef.current?.abort();setBusy(false);setError('');setConnected(false);setMessages([HELLO]);setDraft('')}

 return <div className="aureva-chat-root">
  <AnimatePresence>
   {open&&<motion.section
     key="chat-panel" id="aureva-chat-panel" className="aureva-chat-panel"
     initial={reduced?false:{opacity:0,y:17,scale:.96}}
     animate={{opacity:1,y:0,scale:1}}
     exit={reduced?{opacity:0}:{opacity:0,y:15,scale:.97}}
     transition={{type:'spring',stiffness:310,damping:30}}
     role="dialog" aria-modal="false" aria-label="Trợ lý AI AUREVA">
     <div className="aureva-chat-hero">
       <div className="aureva-chat-hero-glow" aria-hidden="true"/>
       <div className="aureva-chat-hero-top">
        <span className="aureva-chat-avatar"><Bot size={23} strokeWidth={1.8}/></span>
        <div className="aureva-chat-heading">
         <span className="aureva-chat-brow">CÔNG NGHỆ VÌ CỘNG ĐỒNG</span>
         <h2>AUREVA <em>AI</em></h2>
         <span className="aureva-chat-desc"><span className="aureva-chat-dot"/> Trợ lý minh bạch cứu trợ</span>
        </div>
        <button type="button" className="aureva-chat-icon" onClick={()=>setOpen(false)} aria-label="Thu nhỏ trợ lý"><ChevronDown size={19}/></button>
       </div>
       <div className="aureva-chat-trust"><ShieldCheck size={13}/> Số liệu từ hệ thống · Không suy đoán</div>
     </div>
     <div className="aureva-chat-conversation" role="log" aria-live="polite" aria-label="Nội dung hội thoại AUREVA">
      <div className="aureva-chat-date"><Sparkles size={13}/> ĐỒNG HÀNH CÙNG BẠN</div>
      {messages.map((m,i)=><div key={i} className={'aureva-chat-turn '+(m.role==='user'?'aureva-chat-user':'aureva-chat-assistant')}>
       {m.role==='assistant'&&<span className="aureva-chat-mini-avatar" aria-hidden="true"><Sparkles size={13}/></span>}
       <div className="aureva-chat-bubble">{m.content}</div>
      </div>)}
      {messages.length===1&&!busy&&<div className="aureva-chat-starters">
       <span>BẠN CÓ THỂ HỎI</span>
       {suggestions.map(s=><button key={s} type="button" onClick={()=>void send(s)}>{s}<ArrowUpRight size={13}/></button>)}
      </div>}
      {busy&&<div className="aureva-chat-turn aureva-chat-assistant" aria-label="Trợ lý đang trả lời"><span className="aureva-chat-mini-avatar"><Sparkles size={13}/></span><span className="aureva-chat-typing"><i/><i/><i/></span></div>}
      {error&&<div className="aureva-chat-error" role="alert">{error}<button type="button" onClick={()=>{const last=[...messages].reverse().find(m=>m.role==='user');if(last)void send(last.content)}} disabled={busy}><RotateCcw size={13}/> Thử lại</button></div>}
      <div ref={endRef}/>
     </div>
     <div className="aureva-chat-bottom">
       <form className="aureva-chat-compose" onSubmit={(e:FormEvent<HTMLFormElement>)=>{e.preventDefault();void send()}}>
        <textarea ref={inputRef} placeholder="Hỏi AUREVA AI điều gì đó…" value={draft} rows={1} maxLength={750}
          aria-label="Nội dung câu hỏi" onChange={e=>setDraft(e.target.value)}
          onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();void send()}}}/>
        <button type="submit" disabled={busy||draft.trim().length<2} aria-label="Gửi câu hỏi"><Send size={17}/></button>
       </form>
       <div className="aureva-chat-footnote">
        <span><ShieldCheck size={12}/>{connected?'Đã đọc dữ liệu công khai':'Không chia sẻ dữ liệu nhạy cảm'}</span>
        <button type="button" onClick={reset} title="Xóa cuộc trò chuyện"><RotateCcw size={12}/> Làm mới</button>
       </div>
       <p>AI có thể sai. Vui lòng kiểm chứng số liệu và giao dịch trước khi quyết định.</p>
     </div>
   </motion.section>}
  </AnimatePresence>
  <motion.button type="button" className={'aureva-chat-toggle '+(open?'aureva-chat-open':'')} onClick={()=>setOpen(x=>!x)}
   whileHover={reduced?undefined:{y:-3,scale:1.025}} whileTap={reduced?undefined:{scale:.96}}
   aria-expanded={open} aria-controls="aureva-chat-panel" aria-label={open?'Đóng AUREVA AI':'Mở trợ lý AI AUREVA'}>
   <span className="aureva-chat-toggle-symbol">{open?<X size={21}/>:<MessageCircle size={22}/>}</span>
   {!open&&<span className="aureva-chat-toggle-copy"><strong>Hỏi AUREVA AI</strong><small><HeartHandshake size={12}/> Luôn sẵn sàng hỗ trợ</small></span>}
   {!open&&<span className="aureva-chat-toggle-spark" aria-hidden="true"><Sparkles size={15}/></span>}
  </motion.button>
 </div>
}
