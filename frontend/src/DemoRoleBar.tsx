import {HeartHandshake,LayoutDashboard,ShieldCheck,Sparkles} from 'lucide-react';
import './DemoRoleBar.css';

export type DemoRole='donor'|'manager'|'approver';
type CurrentUser={role:DemoRole;id:string}|null;

const roles=[
 {role:'donor' as const,label:'Đóng góp',icon:HeartHandshake,detail:'Người đóng góp'},
 {role:'manager' as const,label:'Quản lý',icon:LayoutDashboard,detail:'Người phụ trách'},
 {role:'approver' as const,label:'Phê duyệt',icon:ShieldCheck,detail:'Người phê duyệt'},
];

export function DemoRoleBar({enabled,user,busy,onSwitch}:{
 enabled:boolean;user:CurrentUser;busy:boolean;onSwitch:(role:DemoRole)=>void
}){
 if(!enabled)return null;
 return <aside className="aureva-demo-bar" aria-label="Chuyển tài khoản thuyết trình">
  <div className="aureva-demo-label">
   <span className="aureva-demo-label-badge"><Sparkles size={13}/> DEMO</span>
   <span>Đổi tài khoản một chạm <small>Chỉ dữ liệu thử nghiệm</small></span>
  </div>
  <div className="aureva-demo-roles" role="group" aria-label="Chọn vai trò demo">
   {roles.map(({role,label,icon:Icon,detail})=>{
    const active=user?.id==='aureva_demo_'+role+'_v1';
    return <button key={role} type="button" className={'aureva-demo-role'+(active?' active':'')}
     aria-label={'Đổi sang tài khoản demo '+detail}
     aria-pressed={active}
     disabled={busy||active}
     onClick={()=>onSwitch(role)}>
     <Icon size={16} strokeWidth={1.85}/><span>{label}</span>
    </button>;
   })}
  </div>
 </aside>;
}
