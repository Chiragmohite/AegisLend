import axios from 'axios';
import { createContext, useContext, useState, type ReactNode } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { api } from './api';
import { get, post, type User } from './client';
type Session={user:User|null;login:(email:string,password:string,otp?:string)=>Promise<void>;logout:()=>Promise<void>};
const Context=createContext<Session|null>(null);
export function SessionProvider({children}:{children:ReactNode}) {
  const [user,setUser]=useState<User|null>(null);
  async function login(email:string,password:string,otp?:string) {
    const result=await post<{access_token:string}>('/auth/login',{email,password,...(otp?{otp}:{})});
    api.defaults.headers.common.Authorization=`Bearer ${result.access_token}`;
    try{setUser(await get<User>('/auth/me'))}catch(e){delete api.defaults.headers.common.Authorization;throw e}
  }
  async function logout(){try{await post('/auth/logout')}catch(e){if(!axios.isAxiosError(e)||e.response?.status!==401)throw e}delete api.defaults.headers.common.Authorization;setUser(null)}
  return <Context.Provider value={{user,login,logout}}>{children}</Context.Provider>;
}
export function useSession(){const value=useContext(Context);if(!value)throw Error('SessionProvider missing');return value}
export function Protected({admin=false}:{admin?:boolean}) {const {user}=useSession();if(!user)return <Navigate to="/login" replace/>;if(admin&&user.role!=='administrator')return <Navigate to="/dashboard" replace/>;return <Outlet/>}
