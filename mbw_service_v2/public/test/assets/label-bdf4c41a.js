import{x as v,az as g,A as h,q as j,aO as y,s as L,aP as O,y as S,aN as k,ab as x}from"./index-aea319af.js";let i=Symbol("LabelContext");function p(){let t=x(i,null);if(t===null){let a=new Error("You used a <Label /> component, but it is not inside a parent.");throw Error.captureStackTrace&&Error.captureStackTrace(a,p),a}return t}function E({slot:t={},name:a="Label",props:n={}}={}){let e=v([]);function o(r){return e.value.push(r),()=>{let l=e.value.indexOf(r);l!==-1&&e.value.splice(l,1)}}return g(i,{register:o,slot:t,name:a,props:n}),h(()=>e.value.length>0?e.value.join(" "):void 0)}let P=j({name:"Label",props:{as:{type:[Object,String],default:"label"},passive:{type:[Boolean],default:!1},id:{type:String,default:()=>`headlessui-label-${y()}`}},setup(t,{slots:a,attrs:n}){let e=p();return L(()=>O(e.register(t.id))),()=>{let{name:o="Label",slot:r={},props:l={}}=e,{id:d,passive:c,...u}=t,s={...Object.entries(l).reduce((b,[m,f])=>Object.assign(b,{[m]:S(f)}),{}),id:d};return c&&(delete s.onClick,delete s.htmlFor,delete u.onClick),k({ourProps:s,theirProps:u,slot:r,attrs:n,slots:a,name:o})}}});export{E as K,P as T};
