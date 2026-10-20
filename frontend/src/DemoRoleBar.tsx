import {useState} from 'react';
import {HeartHandshake,LayoutDashboard,ShieldCheck,Sparkles,BookOpen,ChevronDown,X} from 'lucide-react';
import './DemoRoleBar.css';

export type DemoRole='donor'|'manager'|'approver';
type CurrentUser={role:DemoRole;id:string}|null;

const roles=[
 {role:'donor' as const,label:'Đóng góp',icon:HeartHandshake,detail:'Người đóng góp'},
 {role:'manager' as const,label:'Quản lý',icon:LayoutDashboard,detail:'Người phụ trách'},
 {role:'approver' as const,label:'Phê duyệt',icon:ShieldCheck,detail:'Người phê duyệt'},
];

const steps=[
 {role:'manager' as const,title:'Tạo chiến dịch thử',detail:'Chọn Quản lý → Tạo chiến dịch; tên sẽ tự có nhãn [DEMO].'},
 {role:'donor' as const,title:'Ghi nhận đóng góp mô phỏng',detail:'Chọn Đóng góp → mở chiến dịch DEMO → nhập số tiền. Không có chuyển khoản hay ETH.'},
 {role:'manager' as const,title:'Đối soát và đề xuất chi',detail:'Trở lại Quản lý → xác nhận khoản giả định → đề xuất khoản chi → tải chứng từ mẫu.'},
 {role:'manager' as const,title:'Phân tích chứng từ bằng AI',detail:'Bấm phân tích. OpenAI cần API key thật; lỗi API không được thay bằng kết quả giả.'},
 {role:'approver' as const,title:'Phê duyệt hoặc từ chối',detail:'Chọn Phê duyệt → đọc cảnh báo AI → ghi lý do và quyết định.'},
 {role:'approver' as const,title:'Kiểm chứng Blockchain và PDF',detail:'Dùng ví chủ hợp đồng MetaMask ký Sepolia (nếu đã cấu hình), xem TX/Etherscan và hash PDF.'},
];

export function DemoRoleBar({enabled,user,busy,onSwitch}:{
 enabled:boolean;user:CurrentUser;busy:boolean;onSwitch:(role:DemoRole)=>void
}){
 const[showGuide,setShowGuide]=useState(false);
 if(!enabled)return null;
 return <div className="aureva-demo-bar" role="region" aria-label="Chuyển tài khoản thuyết trình">
  <div className="aureva-demo-label">
   <span className="aureva-demo-label-badge"><Sparkles size={13}/> DEMO</span>
   <span>Đổi tài khoản một chạm <small>Không giao dịch tiền thật</small></span>
  </div>
  <div className="aureva-demo-roles" role="group" aria-label="Chọn vai trò demo">
   {roles.map(({role,label,icon:Icon,detail})=>{
    const active=user?.id==='aureva_demo_'+role+'_v1';
    return <button key={role} type="button" className={'aureva-demo-role'+(active?' active':'')}
     aria-label={'Đổi sang tài khoản demo '+detail} aria-pressed={active}
     disabled={busy||active} onClick={()=>onSwitch(role)}>
     <Icon size={16} strokeWidth={1.85}/><span>{label}</span>
    </button>;
   })}
  </div>
  <button type="button" className="aureva-demo-help" aria-expanded={showGuide}
   aria-controls="aureva-demo-guide" onClick={()=>setShowGuide(value=>!value)}>
   <BookOpen size={16}/><span>Luồng demo</span>{showGuide?<X size={14}/>:<ChevronDown size={14}/>}
  </button>
  {showGuide&&<div className="aureva-demo-guide" id="aureva-demo-guide" role="region" aria-label="Hướng dẫn thử các chức năng của AUREVA">
   <strong>Thử AUREVA theo 6 bước</strong>
   <p>Toàn bộ khoản đóng góp trong Preview là mô phỏng. AI và Blockchain chỉ hiện xác nhận khi các dịch vụ thật hoạt động.</p>
   <ol>{steps.map((step,index)=><li key={index}><span className="aureva-demo-step-number">{index+1}</span><div><b>{step.title}</b><small>{step.detail}</small></div><button type="button" disabled={busy||user?.id==='aureva_demo_'+step.role+'_v1'}
    onClick={()=>onSwitch(step.role)}>Đổi vai trò</button></li>)}</ol>
  </div>}
 </div>;
}
