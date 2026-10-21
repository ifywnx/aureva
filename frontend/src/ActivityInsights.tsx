import {useEffect,useState} from 'react';
import {CalendarDays,BarChart3,CheckCircle2,ClipboardCheck,HeartHandshake,ShieldCheck} from 'lucide-react';

type Point={day:string;confirmed:number;approved:number};
type Event={id:number;action:string;occurred_at:string;campaign_id:string;campaign_title:string;amount:number};
type Activity={events:Event[];trend:Point[];description:string;scope:string};
const money=(n:number)=>new Intl.NumberFormat('vi-VN',{maximumFractionDigits:0}).format(n)+' ₫';
const labels:Record<string,string>={
 'donation.confirmed':'Đã đối soát khoản đóng góp',
 'expense.approved':'Đã phê duyệt khoản chi',
 'expense.rejected':'Đã từ chối khoản chi'
};
const icons:Record<string,typeof HeartHandshake>={
 'donation.confirmed':HeartHandshake,'expense.approved':ClipboardCheck,'expense.rejected':ShieldCheck
};
export function ActivityInsights({campaignId}:{campaignId?:string}){
 const [data,setData]=useState<Activity|null>(null),[error,setError]=useState(''),[loading,setLoading]=useState(true);
 useEffect(()=>{
  const controller=new AbortController();
  setLoading(true);setError('');setData(null);
  fetch('/api/public/activity'+(campaignId?'?campaign_id='+encodeURIComponent(campaignId):''),{signal:controller.signal,credentials:'same-origin'})
   .then(async r=>{if(!r.ok)throw new Error('Chưa tải được dữ liệu dòng tiền. Vui lòng thử lại.');return r.json() as Promise<Activity>})
   .then(d=>{if(!controller.signal.aborted)setData(d)})
   .catch(e=>{if(!controller.signal.aborted)setError(e instanceof Error?e.message:'Không tải được dữ liệu.')})
   .finally(()=>{if(!controller.signal.aborted)setLoading(false)});
  return ()=>controller.abort();
 },[campaignId]);
 const max=Math.max(1,...(data?.trend??[]).flatMap(r=>[r.confirmed,r.approved]));
 return <section className="activity-insights" aria-label="Biểu đồ và lịch sử giao dịch đã được xác nhận">
   <div className="activity-insights-head"><div><span className="eyebrow"><BarChart3 size={16}/> DỮ LIỆU THỜI GIAN THỰC TỪ NHẬT KÝ</span><h2>Hành trình minh bạch, nhìn thấy được.</h2><p>Biểu đồ chỉ sử dụng các khoản đã đối soát và khoản chi đã được duyệt.</p></div></div>
   {loading?<div className="activity-placeholder" role="status">Đang tải diễn biến thu chi…</div>:
    error?<div className="activity-placeholder" role="alert">{error}</div>:
    !data||!data.events.length?<div className="activity-placeholder"><CalendarDays size={24}/><span>Chưa có quyết định thu–chi nào được ghi vào nhật ký. Biểu đồ sẽ xuất hiện khi có dữ liệu thực.</span></div>:
    <div className="activity-layout">
      <div className="activity-graph">
        <div className="activity-panel-heading"><b>Thu–chi theo ngày có hoạt động</b><small>{data.trend.length} ngày ghi nhận gần nhất</small></div>
        <div className="activity-legend"><span><i className="in"/> Đã đối soát</span><span><i className="out"/> Chi được duyệt</span></div>
        <div className="activity-bars" role="group" aria-label="Biểu đồ thu chi theo ngày">
          {data.trend.map(p=><div className="activity-bar-column" key={p.day} title={p.day+' · Thu '+money(p.confirmed)+' · Chi '+money(p.approved)}>
            <div className="activity-bar-pair">
              <span className="activity-bar-in" style={{height:100*p.confirmed/max+'%'}}/>
              <span className="activity-bar-out" style={{height:100*p.approved/max+'%'}}/>
            </div>
            <small>{p.day.slice(5)}</small>
          </div>)}
        </div>
        <p className="activity-footnote">Các cột phản ánh ngày hệ thống ghi nhận việc đối soát và phê duyệt, không phải ngày ngân hàng chuyển tiền.</p>
      </div>
      <div className="activity-timeline">
        <div className="activity-panel-heading"><b>Lịch sử quyết định gần đây</b><small>{data.events.length} sự kiện</small></div>
        <div className="activity-events">{data.events.slice(0,7).map(e=>{
          const Icon=icons[e.action]??CheckCircle2;
          return <article className="activity-event" key={e.id}>
            <span className={'activity-event-icon '+(e.action==='expense.rejected'?'rejected':e.action==='expense.approved'?'approved':'donation')}><Icon size={16}/></span>
            <div><b>{labels[e.action]??'Cập nhật hoạt động'}</b><small>{e.campaign_title}</small><time dateTime={e.occurred_at}>{new Date(e.occurred_at).toLocaleString('vi-VN')}</time></div>
            <strong>{money(e.amount)}</strong>
          </article>;
        })}</div>
      </div>
    </div>}
 </section>;
}
