import { api } from './api';
import axios from 'axios';
export interface User { id:string; email:string; role:'customer'|'administrator' }
export interface Product { id:string; name:string; description:string; product_type:string; min_amount:string; max_amount:string; min_months:number; max_months:number; annual_rate:string; min_income:string; max_dti:string; active:boolean }
export interface Estimate { indicative_eligible:boolean; monthly_installment:string; estimated_repayment:string; debt_to_income:string; reasons:string[]; assumptions:string[]; disclaimer:string }
export interface Assessment { id:string; inputs:Record<string,string|number>; result:Estimate; created_at:string }
export interface Application { id:string; user_id:string; product_id:string; assessment_id:string; amount:string; months:number; status:string; version:number; created_at:string; history:{status:string;note:string;created_at:string}[] }
export interface Appointment {id:string; user_id:string; starts_at:string; status:string; purpose:string}
export interface Profile {user_id:string;display_name:string;employment:string}
export interface Document {id:string;title:string;status:string;error:string|null;created_at:string}
export interface Answer {answer:string;sources:{document_id:string;title:string;chunk:number;page:number|null;excerpt:string}[];mode:string;retrieval:string;warning:string|null;stages:string[]}
export interface SecurityEvent {id:string;category:string;severity:string;correlation_id:string;features:Record<string,number>;rules:string[];created_at:string}
export interface Risk {id:string;event_id:string;score:number;severity:string;anomaly_score:number|null;anomaly_class:number|null;model_version:string|null;explanation:string;created_at:string}
export interface Audit {id:string;actor_id:string|null;event_type:string;target_type:string;target_id:string|null;correlation_id:string;details:Record<string,unknown>;created_at:string}
export interface Summary {active_restrictions:number;open_incidents:number;active_challenges:number;total:number;severity:Record<string,number>;failed_login_trend:{date:string;count:number}[];anomalies:number;telemetry:{degraded:boolean;persisted_this_process:number;failed_writes:number};model:{status:string;metadata:Record<string,unknown>|null};rate_limiter:{mode:string;degraded:boolean};assistant:{provider:string;chroma_configured:boolean}}
export const get = async <T,>(path:string):Promise<T> => (await api.get<T>(path)).data;
export const post = async <T,>(path:string,body:unknown={}):Promise<T> => (await api.post<T>(path,body,{timeout:30000})).data;
export const put = async <T,>(path:string,body:unknown):Promise<T> => (await api.put<T>(path,body)).data;
export const remove = async <T,>(path:string):Promise<T> => (await api.delete<T>(path)).data;
export function message(error:unknown):string {
  if(axios.isAxiosError(error)) {
    const detail=error.response?.data?.detail;
    if(typeof detail==='string')return detail;
    if(error.response?.status===401)return 'Your session expired. Sign out and sign in again.';
    return error.response ? `Request failed (${error.response.status}). No success was confirmed.` : 'Unable to reach the API. Check the backend connection.';
  }
  return error instanceof Error ? error.message : 'An unexpected error occurred.';
}
