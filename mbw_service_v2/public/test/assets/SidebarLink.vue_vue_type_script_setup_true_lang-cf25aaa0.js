import{q as m,o as t,b as x,a as o,c as n,y as s,H as y,f as i,l,t as h,r as k,j as g,w as c,ai as w,p as b,T as v,M as B}from"./index-aea319af.js";import{I as C}from"./iconify-d47d89f2.js";const A=m({__name:"SidebarLink",props:{icon:null,label:null,isExpanded:{type:Boolean},isActive:{type:Boolean,default:!1},isBeta:{type:Boolean,default:!1},onClick:{type:Function,default:()=>()=>!0},to:{default:""}},setup(e){const a=e,r=B(),d="This feature is a work in progress. Use with caution";function u(){a.onClick(),a.to&&r.push({name:a.to})}return(f,E)=>(t(),x("div",{class:i(["-all flex h-7 cursor-pointer items-center rounded pl-2 pr-1 text-gray-800 duration-300 ease-in-out",{"w-full":e.isExpanded,"w-8":!e.isExpanded,"shadow-sm":e.isActive,"bg-white":e.isActive,"hover:bg-gray-100":!e.isActive}]),onClick:u},[o("span",{class:i(["shrink-0 text-gray-700",{"text-gray-900":!e.isExpanded}])},[typeof e.icon=="string"?(t(),n(s(C),{key:0,icon:e.icon,class:"h-4 w-4"},null,8,["icon"])):(t(),n(y(e.icon),{key:1,class:"h-4 w-4"}))],2),o("div",{class:i(["-all ml-2 flex shrink-0 grow items-center justify-between text-sm duration-300 ease-in-out",{"opacity-100":e.isExpanded,"opacity-0":!e.isExpanded,"-z-50":!e.isExpanded}])},[l(h(e.label)+" ",1),k(f.$slots,"right",{},()=>[g(s(v),{text:d},{default:c(()=>[e.isBeta?(t(),n(s(w),{key:0,theme:"orange",variant:"subtle"},{default:c(()=>[l("beta")]),_:1})):b("",!0)]),_:1})])],2)],2))}});export{A as _};