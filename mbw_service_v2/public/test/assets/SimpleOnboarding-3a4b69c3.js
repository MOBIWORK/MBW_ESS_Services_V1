import{q as C,s as h,u as m,o as c,b as A,a as e,t as u,v as V,x as f,j as g,y as i,i as x,z as S,A as J,F as R,d as L,f as Z,w as $,T as M,p as Q,B as G,C as B,I as w,E as W,G as U,c as k,H as D,h as b,l as F,J as j,K as O,L as T,M as N,_ as Y}from"./index-aea319af.js";import{I as q}from"./alert-circle-3f3ed3a1.js";import{u as P}from"./error-bdedfa48.js";import{F as H}from"./FileUploader-68858d98.js";const z={class:"flex flex-col gap-2 text-gray-800"},X=C({__name:"OnboardingIntro",setup(p){const n="We're excited to have you join us and explore the world of efficient customer support. 	We are here to revolutionize the way you handle customer inquiries, streamline ticket 	management, and deliver outstanding service.",t="Once again, welcome to Frappe Helpdesk! Let's hope for a long and smooth journey!";return h(()=>m("onboarding_started")),(a,s)=>(c(),A("div",z,[e("div",{class:"text-base text-gray-900"},u(n)),e("div",{class:"text-base text-gray-900"},u(t))]))}}),y=V("onboarding",()=>{const p=f(0),n=f("");function t(){p.value++}return{next:t,service:n,step:p}}),K={class:"flex flex-col gap-4"},ee=C({__name:"EmailIntro",setup(p){const{next:n}=y(),t="Did you know that our Helpdesk becomes even more powerful when 	integrated with email? With this integration, you can send and 	receive emails directly from your Helpdesk inbox. It streamlines 	communication and enhances productivity. Would you like assistance 	in setting up your email integration now?";return(a,s)=>(c(),A("div",K,[e("div",{class:"text-gray-700"},u(t)),g(i(x),{label:"Let's go!",variant:"outline",class:"w-max",onClick:i(n)},null,8,["onClick"])]))}}),te="/assets/mbw_service_v2/test/assets/gmail-6497f877.png",se="/assets/mbw_service_v2/test/assets/outlook-e028ee9b.png",oe="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAwMAAALUBAMAAAClQPMzAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAAlwSFlzAAAuIwAALiMBeKU/dgAAACRQTFRFR3BMNqzpdMXvXb3tr+f3o+P1AJ/ZGoPjALPjmeH1dc3uBqfjM5e/jQAAAAZ0Uk5TAPVwwVLTgnc47wAABIBJREFUeNrt1rEJwlAYhdEHNpZa2UpwAxewcAXtbdJYpQo4gATsBVdwAOcTd/DyknC+9zY4XPhLkSRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJkiRJGmGL/cTazo5gOWR69KFWCBAgQIAAAQIECBAgmArBHYEVIECAAAECBC4iBFaAAAECBAgQuIgQWAECBAgQIEDgIkJgBQgQIECAAIGLCIEVIECAAAECBC4iBFaAAAECBAgQuIgQWAECBAgQIEDgIkJgBQgQIECAAIGLCIEVIECAAAECBC4iBFaAAAECBAgQuIgQWAECBAgQIEDgIkJgBQgQIECAAIGLCIEVIECAAAECBC4iBFaAAAECBAgQuIgQWAECBAgQIEDgIkJgBQgQIECAAIGLCIEVIECAAAECBC4iBFaAAAECBAgQuIgQWAECBAgQIEDgIkJgBQgQIECAAIGLCIEVIECAAAECBC4iBFaAAAECBAgQuIgQWAECBAgQIEDgIkJgBQgQIECAAIGLCIEVIECAAAECBC4iBFaAAAECBAgQuIgQWAECBAgQIEDgIkJgBQgQIECAAMHfO4U6X9tP4reb9aX77/v9rqtH8Ar1bEOl1oWgNsGAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAjqEfShbu9QTajD/AhS8yqzCwECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIECAAAECBAgQIKheE2p3DFUkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZIkSZLG2Bet4fvU2eVggAAAAABJRU5ErkJggg==",ne="/assets/mbw_service_v2/test/assets/sparkpost-3d6653ba.webp",ae="/assets/mbw_service_v2/test/assets/yahoo-bf2216d3.png",ie="/assets/mbw_service_v2/test/assets/yandex-5e1e6be8.png",le={class:"flex flex-col gap-4"},re={class:"grid grid-cols-4 gap-4"},ce=["onClick"],Ae=["src"],ue={key:0,class:"flex items-center gap-2 rounded-xl p-2 ring-1 ring-gray-200"},de={class:"text-xs text-gray-700"},ge=C({__name:"SelectService",setup(p){const n=y(),{next:t}=n,{service:a}=S(n),s="Which service do you want to add?",o=[{name:"GMail",icon:te,info:"Setting up GMail requires you to enable two factor authentication 		and app specific passwords. Read more at https://support.google.com/accounts/answer/185833"},{name:"Outlook",icon:se},{name:"Sendgrid",icon:oe},{name:"SparkPost",icon:ne},{name:"Yahoo",icon:ae},{name:"Yandex",icon:ie}],r=J(()=>o.find(d=>d.name===a.value)?.info);return h(()=>m("onboarding_email_select_service_reached")),(d,E)=>(c(),A("div",le,[e("div",{class:"text-gray-700"},u(s)),e("div",re,[(c(),A(R,null,L(o,l=>e("div",{key:l.name,class:Z(["flex h-20 w-20 cursor-pointer items-center justify-center place-self-center rounded-xl bg-gray-100 hover:bg-gray-200",{"ring-2":l.name===i(a),"ring-gray-300":l.name===i(a)}]),onClick:I=>a.value=l.name},[g(i(M),{text:l.name},{default:$(()=>[e("img",{src:l.icon,class:"h-12 w-12"},null,8,Ae)]),_:2},1032,["text"])],10,ce)),64))]),i(r)?(c(),A("div",ue,[g(i(q),{class:"h-12 w-12 text-blue-500"}),e("div",de,u(i(r)),1)])):Q("",!0),g(i(x),{label:"Continue",disabled:i(G.isEmpty)(i(a)),class:"w-max",variant:"outline",onClick:i(t)},null,8,["disabled","onClick"])]))}}),me={class:"flex flex-col gap-4"},pe=C({__name:"EmailCredentials",setup(p){const n=y(),{next:t}=n,{service:a}=S(n),s=f(""),o=f(""),r=f(""),d={GMail:{email_server:"imap.gmail.com",use_ssl:1,smtp_server:"smtp.gmail.com"},outlook:{email_server:"imap-mail.outlook.com",use_ssl:1,smtp_server:"smtp-mail.outlook.com"},Sendgrid:{smtp_server:"smtp.sendgrid.net",smtp_port:587},SparkPost:{smtp_server:"smtp.sparkpostmail.com"},Yahoo:{email_server:"imap.mail.yahoo.com",use_ssl:1,smtp_server:"smtp.mail.yahoo.com",smtp_port:587},Yandex:{email_server:"imap.yandex.com",use_ssl:1,smtp_server:"smtp.yandex.com",smtp_port:587}},E=B({url:"frappe.client.insert",onSuccess:()=>{m("onboarding_email_credentials_success"),t()},onError:I=>{P()(I),m("onboarding_email_credentials_fail")}}),l=U(()=>{E.submit({doc:{doctype:"Email Account",email_account_name:s.value,email_id:o.value,password:r.value,enable_incoming:!0,enable_outgoing:!0,default_incoming:!0,default_outgoing:!0,email_sync_option:"ALL",initial_sync_count:100,imap_folder:[{append_to:"HD Ticket",folder_name:"INBOX"}],create_contact:!0,track_email_status:!0,service:a.value,use_tls:1,use_imap:1,smtp_port:587,...d[a.value]}})},500);return h(()=>m("onboarding_email_credentials_reached")),(I,v)=>(c(),A("div",me,[e("form",{class:"space-y-4",onSubmit:v[3]||(v[3]=W((..._)=>i(l)&&i(l)(..._),["prevent"]))},[g(i(w),{modelValue:s.value,"onUpdate:modelValue":v[0]||(v[0]=_=>s.value=_),label:"Account name",placeholder:"John Doe (Example.com)",type:"text",required:""},null,8,["modelValue"]),g(i(w),{modelValue:o.value,"onUpdate:modelValue":v[1]||(v[1]=_=>o.value=_),label:"Email",placeholder:"john.doe@example.com",type:"email",required:""},null,8,["modelValue"]),g(i(w),{modelValue:r.value,"onUpdate:modelValue":v[2]||(v[2]=_=>r.value=_),label:"Password",placeholder:"••••••••",type:"password",required:""},null,8,["modelValue"])],32),g(i(x),{label:"Finish!",disabled:!s.value||!o.value||!r.value,loading:i(E).loading,class:"w-max",variant:"outline",onClick:i(l)},null,8,["disabled","loading","onClick"])]))}}),_e={class:"flex flex-col items-center justify-center gap-4"},Ce=C({__name:"SuccessMessage",setup(p){const n="✔️",t="Fantastic! Your email is now active. You are ready unleash true 	potential of Frappe Helpdesk!";return h(()=>m("onboarding_email_finished")),(a,s)=>(c(),A("div",_e,[e("div",{class:"text-7xl"},u(n)),e("div",{class:"text-center text-base italic text-gray-900"},u(t))]))}}),Ee={class:"flex flex-col gap-4"},ve=C({__name:"SetupEmail",setup(p){const n=y(),{step:t}=S(n),a=[ee,ge,pe,Ce];return h(()=>m("onboarding_email_reached")),(s,o)=>(c(),A("div",Ee,[(c(),k(D(a[i(t)])))]))}}),fe={class:"flex flex-col gap-4"},he=["src"],Ie=C({__name:"SetupFavicon",setup(p){const n="A favicon enhances your website by providing a small, recognizable icon that 	appears in browser tabs. It improves brand recognition, adds professionalism, 	aids navigation, establishes trust, and maintains brand consistency",t=f(null),a=B({url:"frappe.client.set_value",debounce:1e3,onSuccess(o){t.value=o.brand_favicon,m("onboarding_favicon_changed")}});function s(o){a.submit({doctype:"HD Settings",name:"HD Settings",fieldname:"brand_favicon",value:o.file_url})}return h(()=>m("onboarding_favicon_reached")),(o,r)=>{const d=b("Button"),E=b("ErrorMessage");return c(),A("div",fe,[e("div",{class:"text-gray-700"},u(n)),t.value?(c(),A("img",{key:0,class:"m-auto h-8 w-8",src:t.value},null,8,he)):Q("",!0),g(i(H),{onSuccess:r[0]||(r[0]=l=>s(l))},{default:$(({error:l,openFileSelector:I})=>[e("span",null,[g(d,{label:"Upload Favicon",loading:i(a).loading,class:"w-max",variant:"outline",onClick:I},null,8,["loading","onClick"]),g(E,{class:"mt-2",message:l},null,8,["message"])])]),_:1})])}}}),be={class:"flex flex-col gap-4"},Be=["src"],ke=C({__name:"SetupLogo",setup(p){const n="this will be used in many places, including login and loading screens. 	An image with transparent background and a resolution of 160 x 32 is preferred",t=f(null),a=B({url:"frappe.client.set_value",debounce:1e3,onSuccess(o){t.value=o.brand_logo,m("onboarding_logo_changed")}});function s(o){a.submit({doctype:"HD Settings",name:"HD Settings",fieldname:"brand_logo",value:o.file_url})}return h(()=>m("onboarding_logo_reached")),(o,r)=>{const d=b("Button"),E=b("ErrorMessage");return c(),A("div",be,[e("div",{class:"text-gray-700"},u(n)),t.value?(c(),A("img",{key:0,class:"m-auto h-8",src:t.value},null,8,Be)):Q("",!0),g(i(H),{onSuccess:r[0]||(r[0]=l=>s(l))},{default:$(({error:l,openFileSelector:I})=>[e("span",null,[g(d,{label:"Upload Logo",loading:i(a).loading,class:"w-max",variant:"outline",onClick:I},null,8,["loading","onClick"]),g(E,{class:"mt-2",message:l},null,8,["message"])])]),_:1})])}}}),xe={viewBox:"0 0 256 256",width:"1.2em",height:"1.2em"},Qe=e("path",{fill:"currentColor",d:"m232.49 80.49l-128 128a12 12 0 0 1-17 0l-56-56a12 12 0 1 1 17-17L96 183L215.51 63.51a12 12 0 0 1 17 17Z"},null,-1),ye=[Qe];function we(p,n){return c(),A("svg",xe,ye)}const Se={name:"ph-check-bold",render:we},$e={class:"flex flex-col gap-4 text-gray-800"},Je={class:"relative flex items-center justify-end"},Re=C({__name:"SetupName",setup(p){const n="Now, let's set a name for your Helpdesk that reflects your organization's 	identity and values. So, what would you like to name your Helpdesk?",t="Choose a name that resonates with your brand and instills 	trust in your customers",a="My Helpdesk",s=f(!1),o=B({url:"frappe.client.set_value",debounce:1e3,onSuccess(){s.value=!0,m("onboarding_name_changed")}});function r(d){s.value=!1,o.submit({doctype:"HD Settings",name:"HD Settings",fieldname:"helpdesk_name",value:d})}return h(()=>m("onboarding_name_reached")),(d,E)=>{const l=b("Input");return c(),A("div",$e,[F(u(n)+" "),e("div",Je,[g(l,{type:"text",class:"w-full",placeholder:a,onInput:r}),s.value?(c(),k(i(Se),{key:0,class:"absolute mr-2 w-6 text-green-500"})):Q("",!0)]),e("div",{class:"italic text-gray-800"},u(t))])}}}),Le={class:"flex flex-col gap-4 text-gray-800"},De=C({__name:"SetupSkipEmail",setup(p){const n="Did you know that our Helpdesk is designed to function independently, 	without relying on email? Our customer portal is finely tuned to be a 	standalone solution, eliminating the hassle of email setup. Would you 	like me to disable the email workflow for you?",t=f(!1),a=B({url:"frappe.client.set_value",debounce:1e3,onSuccess(o){t.value=o.skip_email_workflow;const d="onboarding_skip_email_"+(t.value?"yes":"no");m(d)}});function s(o){a.submit({doctype:"HD Settings",name:"HD Settings",fieldname:"skip_email_workflow",value:o})}return h(()=>m("onboarding_skip_email_reached")),(o,r)=>(c(),A("div",Le,[F(u(n)+" "),g(i(x),{label:t.value?"No":"Yes",class:"w-max",variant:"outline",onClick:r[0]||(r[0]=d=>s(!t.value))},null,8,["label"])]))}}),Fe={class:"flex flex-col gap-4"},He=e("div",{class:"font-medium"},"Don't forget to star our GitHub repo",-1),Ve=e("div",{class:"font-medium"}," If you find any bugs, report them at the issue tracker ",-1),Ze=e("div",{class:"font-medium"}," For any queries or support, reach out to our support portal ",-1),Me=e("div",{class:"font-medium"},"Or via our e-mail",-1),Ge=["href"],We=C({__name:"SuccessMessage",setup(p){const n="https://github.com/frappe/helpdesk",t="https://github.com/frappe/helpdesk/issues",a="https://frappedesk.com/helpdesk",s="hello@frappe.io";return h(()=>m("onboarding_finished")),(o,r)=>(c(),A("div",Fe,[e("div",null,[He,e("a",{class:"text-sm text-gray-800",href:n,target:"_blank"},u(n))]),e("div",null,[Ve,e("a",{class:"text-sm text-gray-800",href:t,target:"_blank"},u(t))]),e("div",null,[Ze,e("a",{class:"text-sm text-gray-800",href:a,target:"_blank"},u(a))]),e("div",null,[Me,e("a",{class:"text-sm text-gray-800",href:"mailto:"+s},u(s),8,Ge)])]))}}),Ue={class:"flex h-screen w-screen items-center justify-center bg-gray-100"},je={class:"container-box w-1/3 rounded-xl text-base text-gray-900"},Oe={class:"rounded-t-xl bg-white px-8 py-6"},Te={class:"mb-4 text-xl font-semibold"},Ne={class:"flex justify-end rounded-b-xl bg-gray-200 px-8 py-3"},Ye=C({__name:"SimpleOnboarding",setup(p){const n=N(),t=j(),a=O(),s=f(0),o=[{title:"Welcome to Frappe Helpdesk! 🎉",component:X},{title:"Begin with a name! 🖋️",component:Re},{title:"Let's set a logo 💫",component:ke},{title:"How about a Favicon? 🌏",component:Ie},{title:"Did you know? 💡",component:De},{title:"Let's setup an email 📬",component:ve},{title:"That's it for now! 🙏",component:We}],r=J(()=>[{label:"← Previous",appearance:"minimal",variant:"ghost",onClick(){s.value--},condition:s.value+1>1&&s.value+1<=o.length},{label:"Next →",appearance:"primary",variant:"solid",onClick(){s.value++},condition:s.value+1<o.length},{label:"Finish ✓",variant:"solid",onClick(){d()},condition:s.value+1===o.length}].filter(l=>l.condition));function d(){B({url:"frappe.client.set_value"}).submit({doctype:"HD Settings",name:"HD Settings",fieldname:"setup_complete",value:!0}).then(E)}function E(){n.replace({path:"/"})}return T(()=>{(!t.hasDeskAccess||a.isSetupComplete)&&E()}),(l,I)=>{const v=b("Button");return c(),A("div",Ue,[e("div",je,[e("div",Oe,[e("div",Te,u(o[s.value].title),1),(c(),k(D(o[s.value].component)))]),e("div",Ne,[(c(!0),A(R,null,L(i(r),_=>(c(),k(v,{key:_.label,label:_.label,variant:_.variant,onClick:_.onClick},null,8,["label","variant","onClick"]))),128))])])])}}});const Ke=Y(Ye,[["__scopeId","data-v-b15bbb30"]]);export{Ke as default};
