import {useState,type CSSProperties} from 'react';
import {ArrowDownRight, Blocks, BrainCircuit, CheckCircle2, FileCheck2, HeartHandshake, ShieldCheck, Sparkles} from 'lucide-react';
import {motion,useReducedMotion} from 'framer-motion';

const nodes=[
 {className:'v5-orbit-node v5-node-donor', icon:<HeartHandshake size={18}/>, title:'Đóng góp',note:'Đối soát tiền thực nhận'},
 {className:'v5-orbit-node v5-node-ai',icon:<BrainCircuit size={18}/>,title:'AI chứng từ',note:'Phát hiện điểm cần kiểm tra'},
 {className:'v5-orbit-node v5-node-chain',icon:<Blocks size={18}/>,title:'Blockchain',note:'Dấu xác thực khi thành công'}
];

export function ProofOrbit({aiEnabled,chainEnabled}:{aiEnabled:boolean;chainEnabled:boolean}){
 const reduce=useReducedMotion();
 const [tilt,setTilt]=useState({x:0,y:0});
 const style={'--orbit-rotate-x':tilt.x+'deg','--orbit-rotate-y':tilt.y+'deg'} as CSSProperties;
 function pointerMove(e:React.PointerEvent<HTMLDivElement>){
  if(reduce||e.pointerType==='touch')return;
  const rect=e.currentTarget.getBoundingClientRect();
  const x=(e.clientX-rect.left)/rect.width-.5, y=(e.clientY-rect.top)/rect.height-.5;
  setTilt({x:-y*7,y:x*9});
 }
 return <motion.div className="v5-proof-visual" style={style}
   onPointerMove={pointerMove} onPointerLeave={()=>setTilt({x:0,y:0})}
   initial={reduce?false:{opacity:0,scale:.94,y:15}} animate={{opacity:1,scale:1,y:0}}
   transition={{duration:.8,delay:.16,ease:'easeOut'}} aria-label="Mô hình 3D minh họa quá trình từ đóng góp, AI tới Blockchain">
   <div className="v5-proof-glow" aria-hidden="true"/>
   <div className="v5-proof-plane">
    <svg className="v5-orbit-paths" viewBox="0 0 500 500" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
      <defs><linearGradient id="v5-line" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#9FE8FF"/><stop offset=".5" stopColor="#3389F9"/><stop offset="1" stopColor="#DBF6FF"/></linearGradient></defs>
      <circle cx="250" cy="250" r="164" stroke="#B9E1FF" strokeWidth="1" strokeDasharray="2 10" fill="none"/>
      <ellipse cx="250" cy="250" rx="231" ry="100" stroke="url(#v5-line)" strokeWidth="1.7" fill="none" transform="rotate(-27 250 250)" opacity=".85"/>
      <ellipse cx="250" cy="250" rx="231" ry="100" stroke="#74CFFB" strokeWidth="1" strokeDasharray="8 11" fill="none" transform="rotate(49 250 250)" opacity=".7"/>
    </svg>
    <div className="v5-proof-core">
      <div className="v5-core-inner"><span className="v5-core-spark"><Sparkles size={26}/></span><strong>MINH BẠCH</strong><small>TỪ TẤM LÒNG ĐẾN BẰNG CHỨNG</small></div>
    </div>
    {nodes.map(n=><div key={n.title} className={n.className}><span>{n.icon}</span><div><strong>{n.title}</strong><small>{n.note}</small></div></div>)}
    <div className="v5-orbit-flare v5-flare-1" aria-hidden="true"/><div className="v5-orbit-flare v5-flare-2" aria-hidden="true"/>
   </div>
   <div className="v5-proof-caption"><ArrowDownRight size={16}/> Mô hình minh họa quy trình, không phải giao dịch giả.</div>
   <div className="v5-proof-status"><CheckCircle2 size={15}/> <span>AI: {aiEnabled?'Có cấu hình':'Chưa cấu hình'} · Sepolia: {chainEnabled?'Có cấu hình':'Chưa cấu hình'}</span></div>
 </motion.div>;
}
