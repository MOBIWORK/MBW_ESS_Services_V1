import{_ as p}from"./plus-d3fdba1e.js";import{q as l,at as u,ad as T,o as f,b as y,j as t,w as r,y as s,au as d,h as a}from"./index-aea319af.js";import{c as k}from"./notification-c4068361.js";import{_ as h}from"./PageTitle.vue_vue_type_script_setup_true_lang-98ef5881.js";import{_ as E}from"./LV.vue_vue_type_script_setup_true_lang-2ffe76d5.js";import"./iconify-d47d89f2.js";import"./error-bdedfa48.js";import"./EmptyMessage.vue_vue_type_script_setup_true_lang-fbb9efd4.js";import"./label-bdf4c41a.js";import"./use-tree-walker-388abf0b.js";import"./use-controllable-f6b0426f.js";const w={class:"flex flex-col"},I=l({__name:"TicketTypeList",setup(L){const n=[{label:"Name",key:"name",width:"w-80"},{label:"Priority",key:"priority",width:"w-80"}],i=k({doctype:"HD Ticket Type",fields:["name","priority"],auto:!0,transform:e=>{for(const o of e)o.onClick={name:u,params:{id:o.name}};return e}});return T(()=>({title:"Ticket types"})),(e,o)=>{const c=p,m=a("Button"),_=a("RouterLink");return f(),y("div",w,[t(h,{title:"Ticket Types"},{right:r(()=>[t(_,{to:{name:s(d)}},{default:r(()=>[t(m,{label:"New ticket type",theme:"gray",variant:"solid"},{prefix:r(()=>[t(c,{class:"h-4 w-4"})]),_:1})]),_:1},8,["to"])]),_:1}),t(s(E),{columns:n,resource:s(i),class:"mt-2.5",doctype:"HD Ticket Type"},null,8,["resource"])])}}});export{I as default};
