import {useEffect, useRef, useState, type ReactNode} from 'react';
import {AnimatePresence, animate, motion, useInView, useReducedMotion, useScroll, useSpring} from 'framer-motion';

export function ScrollProgress(){
  const reducedMotion = useReducedMotion();
  const {scrollYProgress} = useScroll();
  const smoothProgress = useSpring(scrollYProgress, {stiffness: 110, damping: 30, restDelta: .001});
  return <motion.div className="scroll-progress" style={{scaleX: reducedMotion ? scrollYProgress : smoothProgress}} aria-hidden="true"/>;
}

export function PageMotion({page, children}:{page:string;children:ReactNode}){
  const reducedMotion = useReducedMotion();
  return <AnimatePresence mode="wait" initial={false}>
    <motion.div key={page} className="page-view"
      initial={reducedMotion ? false : {opacity: 0, y: 14}}
      animate={{opacity: 1, y: 0}}
      exit={reducedMotion ? {opacity: 1} : {opacity: 0, y: -9}}
      transition={{duration: reducedMotion ? 0 : .26, ease: 'easeOut'}}>
      {children}
    </motion.div>
  </AnimatePresence>;
}

const formatter = new Intl.NumberFormat('vi-VN', {maximumFractionDigits: 0});
/** Animate only confirmed, real values, never invent a financial number. */
export function StatValue({value}:{value:string}){
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, {once: true, amount: .5});
  const reducedMotion = useReducedMotion();
  const [display, setDisplay] = useState(value);
  const lastValue = useRef(0);

  useEffect(()=>{
    const digits = value.replace(/[^\d]/g, '');
    if(!inView || !digits || reducedMotion){
      setDisplay(value);
      return;
    }
    const target = Number(digits);
    if(!Number.isSafeInteger(target)){setDisplay(value);return;}
    const currency = value.includes('₫');
    const format = (n:number)=> currency ? formatter.format(Math.round(n)) + ' ₫' : formatter.format(Math.round(n));
    const animation = animate(lastValue.current, target, {
      duration: 1.15,
      ease: 'easeOut',
      onUpdate: v=>setDisplay(format(v))
    });
    lastValue.current = target;
    return ()=>animation.stop();
  }, [value, inView, reducedMotion]);

  return <span ref={ref} className="animated-value">{display}</span>;
}
