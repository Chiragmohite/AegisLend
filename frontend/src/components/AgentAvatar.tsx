import { useState } from 'react';
/** This component is used exclusively inside ChatPanel. Original photos are never served. */
export function AgentAvatar({busy=false}:{busy?:boolean}) {
 const [failed,setFailed]=useState(false);
 return <div className={`agent-avatar ${busy?'agent-working':''}`}>
  {failed?<span className="agent-fallback">AI</span>:<img width="62" height="66" src="/agents/chatbot-3d.png" alt="Illustrated AegisLend banking assistant in a navy blazer" onError={()=>setFailed(true)}/>}
 </div>;
}
