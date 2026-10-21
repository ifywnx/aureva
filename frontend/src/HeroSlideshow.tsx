import {useEffect,useRef,useState,type TouchEvent} from 'react';
import {AnimatePresence,motion,useReducedMotion} from 'framer-motion';
import {CheckCircle2,ChevronLeft,ChevronRight,HeartHandshake,Pause,Play} from 'lucide-react';
import './HeroSlideshow.css';

const slides=[
  {
    src:'https://images.pexels.com/photos/32799179/pexels-photo-32799179.jpeg?auto=compress&cs=tinysrgb&w=1400&h=1600&fit=crop',
    alt:'Tình nguyện viên giúp một cụ bà nhận nhu yếu phẩm tại Bình Phước, Việt Nam',
    eyebrow:'BÌNH PHƯỚC · VIỆT NAM',title:'Trao đi sự tử tế.',
    credit:'Duy Nguyen / Pexels · Bình Phước',
    position:'47% 41%'
  },
  {
    src:'https://images.pexels.com/photos/25584155/pexels-photo-25584155.jpeg?auto=compress&cs=tinysrgb&w=1200&h=1500&fit=crop',
    alt:'Tình nguyện viên hỗ trợ vận chuyển hàng cứu trợ tại Bình Thuận, Việt Nam',
    eyebrow:'BÌNH THUẬN · VIỆT NAM',title:'Gắn kết cộng đồng.',
    credit:'Ninh Tien Dat / Pexels · Bình Thuận',
    position:'52% 45%'
  },
  {
    src:'https://images.pexels.com/photos/33670808/pexels-photo-33670808.jpeg?auto=compress&cs=tinysrgb&w=1200&h=1500&fit=crop',
    alt:'Thanh niên tình nguyện mặc áo xanh tham gia hoạt động cộng đồng tại Hà Nội',
    eyebrow:'HÀ NỘI · VIỆT NAM',title:'Từ những hành động nhỏ.',
    credit:'Thang Nguyen / Pexels · Hà Nội',
    position:'50% 45%'
  },
  {
    src:'https://images.pexels.com/photos/34959191/pexels-photo-34959191.jpeg?auto=compress&cs=tinysrgb&w=1200&h=1500&fit=crop',
    alt:'Khung cảnh một ngôi làng bị ngập lụt ở Phú Yên, Việt Nam',
    eyebrow:'PHÚ YÊN · VIỆT NAM',title:'Để mỗi hỗ trợ đến đúng nơi.',
    credit:'Long Bà Mùi / Pexels · Phú Yên',
    position:'53% 51%'
  }
] as const;

const INTERVAL_MS=7000;

export function HeroSlideshow(){
 const reducedMotion=useReducedMotion();
 const [current,setCurrent]=useState(0);
 const [manualPause,setManualPause]=useState(false);
 const [hovered,setHovered]=useState(false);
 const [focused,setFocused]=useState(false);
 const [visible,setVisible]=useState(true);
 const [viewportVisible,setViewportVisible]=useState(true);
 const root=useRef<HTMLDivElement>(null);
 const touchStartX=useRef<number|null>(null);
 const pointerFocus=useRef(false);
 const slide=slides[current];
 const suspended=Boolean(reducedMotion)||manualPause||hovered||focused||!visible||!viewportVisible;
 useEffect(()=>{
   const update=()=>setVisible(document.visibilityState==='visible');
   document.addEventListener('visibilitychange',update);
   update();
   return()=>document.removeEventListener('visibilitychange',update);
 },[]);
 useEffect(()=>{
   const el=root.current;
   if(!el||!('IntersectionObserver' in window))return;
   const observer=new IntersectionObserver(([entry])=>setViewportVisible(entry.isIntersecting),{threshold:.1});
   observer.observe(el);
   return()=>observer.disconnect();
 },[]);
 useEffect(()=>{
   const preload=new Image();
   preload.src=slides[(current+1)%slides.length].src;
 },[current]);
 useEffect(()=>{
   if(suspended)return;
   const interval=window.setInterval(()=>setCurrent(i=>(i+1)%slides.length),INTERVAL_MS);
   return()=>window.clearInterval(interval);
 },[suspended,current]);
 function change(index:number){setCurrent((index+slides.length)%slides.length)}
 function touchEnd(event:TouchEvent<HTMLDivElement>){
   if(touchStartX.current===null)return;
   const distance=event.changedTouches[0].clientX-touchStartX.current;
   touchStartX.current=null;
   if(Math.abs(distance)>=44)change(current+(distance<0?1:-1));
 }
 return <div className="v5-hero-slideshow" ref={root}
   aria-label="Bộ sưu tập ảnh hoạt động cộng đồng tại Việt Nam"
   onMouseEnter={()=>setHovered(true)} onMouseLeave={()=>setHovered(false)}
   onPointerDownCapture={()=>{pointerFocus.current=true;setFocused(false)}}
   onKeyDownCapture={()=>{pointerFocus.current=false}}
   onFocusCapture={()=>{if(!pointerFocus.current)setFocused(true)}}
   onBlurCapture={event=>{if(!event.currentTarget.contains(event.relatedTarget)){setFocused(false);pointerFocus.current=false}}}
   onTouchStart={event=>{touchStartX.current=event.touches[0].clientX}}
   onTouchEnd={touchEnd}>
   <div className="v5-hero-slide-stack">
    <AnimatePresence initial={false}>
      <motion.img key={slide.src} className="v5-hero-slide" src={slide.src} alt={slide.alt}
        loading={current===0?'eager':'lazy'} fetchPriority={current===0?'high':'auto'}
        style={{objectPosition:slide.position}}
        initial={reducedMotion?false:{opacity:0,scale:1.025}}
        animate={{opacity:1,scale:1}}
        exit={reducedMotion?{opacity:0}:{opacity:0,scale:1.015}}
        transition={{duration:reducedMotion?0:.85,ease:'easeInOut'}}
      />
    </AnimatePresence>
   </div>
   <div className="v5-photo-shimmer" aria-hidden="true"/>
   <div className="v5-photo-country" aria-live="off">
    <span>{slide.eyebrow}</span><strong>{slide.title}</strong>
   </div>
   <div className="v5-photo-glass">
     <div><span className="v5-glass-icon"><HeartHandshake size={18}/></span><span>Trao gửi yêu thương<small>Niềm tin được xây từ minh bạch</small></span></div>
     <span className="v5-glass-mark" aria-hidden="true"><CheckCircle2 size={20}/></span>
   </div>
   <div className="v5-slideshow-toolbar" role="group" aria-label="Điều khiển ảnh">
      <button type="button" className="v5-slide-arrow" onClick={()=>change(current-1)} aria-label="Ảnh trước"><ChevronLeft size={15}/></button>
      <div className="v5-slide-indicators" role="group" aria-label="Chọn ảnh">
      {slides.map((item,index)=><button type="button" key={item.src} onClick={()=>change(index)}
        aria-label={`Chọn ảnh ${index+1}: ${item.title}`} aria-current={current===index?'true':undefined}
        className={current===index?'active':''}><span/></button>)}
      </div>
      <button type="button" className="v5-slide-arrow" onClick={()=>change(current+1)} aria-label="Ảnh tiếp theo"><ChevronRight size={15}/></button>
      <button type="button" className="v5-slide-play" onClick={()=>setManualPause(p=>!p)}
        aria-label={manualPause?'Tiếp tục tự chuyển ảnh':'Tạm dừng tự chuyển ảnh'}
        aria-pressed={manualPause}>{manualPause?<Play size={14}/>:<Pause size={14}/>}</button>
   </div>
   <small className="v5-photo-credit">Ảnh tư liệu minh họa, không thuộc chiến dịch AUREVA · {slide.credit}</small>
 </div>
}
