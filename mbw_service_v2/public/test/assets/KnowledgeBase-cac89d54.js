import{q as y,ae as C,x as f,C as $,o as i,c as _,w as v,a0 as b,y as s,a,j as l,af as w,i as h,E as V,D as k,A,ag as D,b as g,F as N,d as R,M as B,a1 as E,ah as S,ad as K,h as I,H as P}from"./index-aea319af.js";import{_ as L}from"./PageTitle.vue_vue_type_script_setup_true_lang-98ef5881.js";import{_ as T}from"./EmptyMessage.vue_vue_type_script_setup_true_lang-fbb9efd4.js";import{I as U}from"./iconify-d47d89f2.js";import{_ as q}from"./SidebarLink.vue_vue_type_script_setup_true_lang-cf25aaa0.js";import{_ as F}from"./KnowledgeBaseIconSelector.vue_vue_type_script_setup_true_lang-7c105983.js";import{g as G}from"./util-fd56a68f.js";const H={class:"space-y-4"},M={class:"space-y-2"},O=a("div",{class:"text-xs text-gray-700"},"Title",-1),j={class:"flex items-center gap-2"},W={class:"space-y-2"},Y=a("div",{class:"text-xs text-gray-700"},"Description",-1),z=y({__name:"KnowledgeBaseCategoryNew",emits:["success"],setup(x,{emit:d}){const p=C(),c=f(""),o=f(""),n=f(""),m=$({url:"frappe.client.insert",makeParams(){return{doc:{doctype:"HD Article Category",category_name:c.value,description:o.value,icon:n.value}}},validate(u){const e=["category_name","description","icon"];for(const t of e)return u.doc[t]?void 0:`${t.replace("_"," ").toUpperCase()} is required`},onSuccess(u){d("success",u.name)}});return(u,e)=>(i(),_(s(k),b(s(p),{options:{title:"New category"}}),{"body-content":v(()=>[a("form",{onSubmit:e[3]||(e[3]=V((...t)=>s(m).submit&&s(m).submit(...t),["prevent"]))},[a("div",H,[a("div",M,[O,a("div",j,[l(F,{icon:n.value,onSelect:e[0]||(e[0]=t=>n.value=t)},null,8,["icon"]),l(s(w),{modelValue:c.value,"onUpdate:modelValue":e[1]||(e[1]=t=>c.value=t),placeholder:"A brief guide",type:"text"},null,8,["modelValue"])])]),a("div",W,[Y,l(s(w),{modelValue:o.value,"onUpdate:modelValue":e[2]||(e[2]=t=>o.value=t),placeholder:"A short description",type:"textarea"},null,8,["modelValue"])]),l(s(h),{class:"w-full",label:"Create",theme:"gray",variant:"solid"})])],32)]),_:1},16))}}),J={class:"h-full space-y-2 border-r px-3.5 py-2.5",style:{"min-width":"242px","max-width":"242px"}},Q={class:"flex items-center justify-between"},X=a("div",{class:"text-sm font-medium text-gray-600"},"Categories",-1),Z={class:"flex flex-col gap-1"},ee=y({__name:"KnowledgeBaseSidebar",setup(x){const d=B(),p=E(),c=A(()=>p.params.categoryId),o=D({doctype:"HD Article Category",auto:!0,fields:["name","category_name","icon"],filters:{parent_category:""}}),n=f(!1);function m(e){d.push({name:S,params:{categoryId:e}})}function u(e){o.reload().then(()=>{n.value=!1,m(e)})}return(e,t)=>(i(),g("div",J,[a("div",Q,[X,l(s(h),{theme:"gray",variant:"ghost",onClick:t[0]||(t[0]=r=>n.value=!n.value)},{icon:v(()=>[l(s(U),{icon:"lucide:plus",class:"h-4 w-4"})]),_:1})]),a("div",Z,[(i(!0),g(N,null,R(s(o).data,r=>(i(),_(q,{key:r.label,icon:s(G)(r.icon,!0),"is-active":s(c)===r.name,"is-expanded":!0,label:r.category_name,"on-click":()=>m(r.name)},null,8,["icon","is-active","label","on-click"]))),128))]),l(z,{modelValue:n.value,"onUpdate:modelValue":t[1]||(t[1]=r=>n.value=r),onSuccess:u},null,8,["modelValue"])]))}}),te={class:"flex flex-col"},se={class:"flex grow border-t"},ue=y({__name:"KnowledgeBase",setup(x){return K(()=>({title:"Knowledge base"})),(d,p)=>{const c=I("RouterView");return i(),g("div",te,[l(L,{title:"Knowledge base"}),a("div",se,[l(ee),(i(),_(c,{key:d.$route.fullPath},{default:v(({Component:o})=>[o?(i(),_(P(o),{key:0})):(i(),_(T,{key:1,message:"Select a category"}))]),_:1}))])])}}});export{ue as default};
