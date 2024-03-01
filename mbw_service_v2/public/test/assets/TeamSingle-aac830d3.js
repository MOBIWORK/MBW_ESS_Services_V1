import{q as O,x as y,ak as U,U as x,A as k,o as i,b as d,a as l,j as a,w as r,y as e,F as E,d as C,t as D,ao as I,M as L,i as u,B as P,c as q,af as G,D as V,C as H,as as j}from"./index-aea319af.js";import{_ as z}from"./Avatar.vue_vue_type_script_setup_true_lang-827ced2f.js";import{D as F}from"./Dropdown-2ffa90e9.js";import{u as X,_ as J}from"./agent-532e565f.js";import{u as h}from"./error-bdedfa48.js";import"./notification-c4068361.js";import{_ as K,I as Q}from"./more-horizontal-fc7b02da.js";import{_ as W}from"./plus-d3fdba1e.js";import{I as Y}from"./x-98362857.js";import{_ as Z}from"./PageTitle.vue_vue_type_script_setup_true_lang-98ef5881.js";import"./iconify-d47d89f2.js";import"./use-tracked-pointer-f136af1c.js";import"./use-tree-walker-388abf0b.js";import"./label-bdf4c41a.js";import"./use-controllable-f6b0426f.js";const ee={class:"flex flex-col"},te={class:"flex items-center gap-2"},se={class:"my-6"},ae={class:"container"},oe={class:"space-y-4"},le=l("div",{class:"text-lg font-medium"},"Members",-1),ne={key:0,class:"flex flex-wrap gap-2"},re={key:1,class:"text-base text-gray-900"},ie={class:"space-y-2"},me={class:"space-y-2"},de={class:"flex items-center gap-2"},ue={class:"text-base"},De=O({__name:"TeamSingle",props:{teamId:{type:String,required:!0}},setup(c){const b=c,w=L(),T=X(),p=y(!1),_=y(!1),f=y(!1),o=U({doctype:"HD Team",name:b.teamId,auto:!0,setValue:{onError:h({title:"Error updating team"})},delete:{onSuccess(){w.replace({name:x})},onError:h({title:"Error deleting team"})}}),m=k({get(){return o.doc?.name},set(n){o.doc.name=n}}),v=k({get(){return!!o.doc?.ignore_restrictions},set(n){o.doc&&o.setValue.submit({ignore_restrictions:n})}}),A=[{label:"Rename",icon:"edit-3",onClick:()=>p.value=!p.value},{label:"Delete",icon:"trash-2",onClick:()=>_.value=!_.value}],M={title:"Rename team"},R={title:"Add member"},$={title:"Delete team",message:`Are you sure you want to delete ${b.teamId}? This action cannot be reversed!`,actions:[{label:"Confirm",theme:"red",variant:"solid",onClick:()=>o.delete.submit()}]};function S(){H({url:"frappe.client.rename_doc",makeParams(){return{doctype:"HD Team",old_name:b.teamId,new_name:m.value}},validate(s){if(!s.new_name)return"New title is required";if(s.new_name===s.old_name)return"New and old title cannot be same"},onSuccess(){w.replace({name:j,params:{teamId:m.value}})},onError:h({title:"Error renaming team"})}).submit()}function N(n){const s=o.doc.users.concat([{user:n}]);o.setValue.submit({users:s})}function B(n){const s=o.doc.users.filter(t=>t.user!==n);o.setValue.submit({users:s})}return(n,s)=>(i(),d("span",null,[l("div",ee,[a(e(Z),{class:"border-b"},{title:r(()=>[a(e(K),{items:[{label:"Teams",route:{name:e(x)}},{label:c.teamId}]},null,8,["items"])]),right:r(()=>[l("div",te,[a(e(u),{label:"Add member",theme:"gray",variant:"solid",onClick:s[0]||(s[0]=t=>f.value=!f.value)},{prefix:r(()=>[a(e(W),{class:"h-4 w-4"})]),_:1}),a(e(F),{options:A},{default:r(()=>[a(e(u),{variant:"ghost"},{icon:r(()=>[a(e(Q),{class:"h-4 w-4"})]),_:1})]),_:1})])]),_:1}),l("div",se,[l("div",ae,[l("div",oe,[le,e(P.isEmpty)(e(o).doc?.users)?(i(),d("div",re," No members found in team: "+D(c.teamId),1)):(i(),d("div",ne,[(i(!0),d(E,null,C(e(o).doc?.users,t=>(i(),q(e(u),{key:t.name,label:t.user,disabled:e(o).loading,theme:"gray",variant:"outline",onClick:g=>B(t.user)},{suffix:r(()=>[a(e(Y),{class:"h-3 w-3"})]),_:2},1032,["label","disabled","onClick"]))),128))])),a(e(J),{modelValue:e(v),"onUpdate:modelValue":s[1]||(s[1]=t=>I(v)?v.value=t:null),size:"md",label:"Bypass restrictions",description:"Members of this team will be able to bypass any team-wise restriction",class:"rounded border p-4"},null,8,["modelValue"])])])])]),a(e(V),{modelValue:p.value,"onUpdate:modelValue":s[3]||(s[3]=t=>p.value=t),options:M},{"body-content":r(()=>[l("div",ie,[a(e(G),{modelValue:e(m),"onUpdate:modelValue":s[2]||(s[2]=t=>I(m)?m.value=t:null),label:"Title",placeholder:"Product Experts"},null,8,["modelValue"]),a(e(u),{label:"Confirm",theme:"gray",variant:"solid",class:"w-full",disabled:e(m)===c.teamId,onClick:S},null,8,["disabled"])])]),_:1},8,["modelValue"]),a(e(V),{modelValue:_.value,"onUpdate:modelValue":s[4]||(s[4]=t=>_.value=t),options:$},null,8,["modelValue"]),a(e(V),{modelValue:f.value,"onUpdate:modelValue":s[5]||(s[5]=t=>f.value=t),options:R},{"body-content":r(()=>[l("div",me,[(i(!0),d(E,null,C(e(T).options,t=>(i(),d("div",{key:t.name,class:"flex items-center justify-between"},[l("div",de,[a(e(z),{label:t.agent_name,image:t.user_image},null,8,["label","image"]),l("div",ue,D(t.agent_name),1)]),a(e(u),{disabled:!!e(o).doc?.users.find(g=>g.user===t.user),label:"Add",theme:"gray",variant:"outline",onClick:g=>N(t.user)},null,8,["disabled","onClick"])]))),128))])]),_:1},8,["modelValue"])]))}});export{De as default};