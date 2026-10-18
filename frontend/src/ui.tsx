import { useEffect, useState, type ReactNode } from 'react';
import { get, message } from './client';
export const money=(value:string|number)=>new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:2}).format(Number(value));
export const date=(value:string)=>new Date(value).toLocaleString();
export function Card({children,className=''}:{children:ReactNode;className?:string}) {return <section className={`card ${className}`}>{children}</section>}
export function Page({title,subtitle,children}:{title:string;subtitle?:string;children:ReactNode}) {return <main id="main-content" className="page"><div className="page-heading"><p className="eyebrow">AEGISLEND / ACADEMIC DEMO</p><h1>{title}</h1>{subtitle&&<p>{subtitle}</p>}</div>{children}</main>}
export function Badge({children}:{children:ReactNode}) {return <span className={`badge badge-${typeof children==='string'?children.toLowerCase().split(' ')[0]:'neutral'}`}>{children}</span>}
export function Notice({error,text}:{error?:string|null;text?:string|null}) {return error?<p role="alert" className="notice error">{error}</p>:text?<p role="status" className="notice success">{text}</p>:null}
export function Empty({text='No records yet.'}:{text?:string}) {return <p className="empty">{text}</p>}
export function useRemote<T>(path:string) {
  const [data,setData]=useState<T|null>(null),[error,setError]=useState(''),[loading,setLoading]=useState(true),[version,setVersion]=useState(0);
  useEffect(()=>{let active=true;setLoading(true);setError('');setData(null);get<T>(path).then(value=>{if(active)setData(value)}).catch(e=>{if(active)setError(message(e))}).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[path,version]);
  return {data,error,loading,reload:()=>setVersion(v=>v+1)};
}
export function useAction() {
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[success,setSuccess]=useState('');
  async function run(fn:()=>Promise<void>,done='Saved successfully.') {if(busy)return;setBusy(true);setError('');setSuccess('');try{await fn();setSuccess(done)}catch(e){setError(message(e))}finally{setBusy(false)}}
  return {busy,error,success,run};
}
export function Pager({offset,count,step=25,onChange}:{offset:number;count:number;step?:number;onChange:(n:number)=>void}) {return <div className="actions"><button className="secondary" disabled={offset===0} onClick={()=>onChange(Math.max(0,offset-step))}>Previous</button><span>Page {Math.floor(offset/step)+1}</span><button className="secondary" disabled={count<step} onClick={()=>onChange(offset+step)}>Next</button></div>}
export function LoadState({loading,error}:{loading:boolean;error:string}) {return <>{loading&&<p role="status">Loading…</p>}<Notice error={error}/></>}
