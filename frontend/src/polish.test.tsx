import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import MockAdapter from 'axios-mock-adapter';
import { api } from './api';
import { DraftEditor } from './components/DraftEditor';
import { ChatPanel } from './components/ChatPanel';
import { IncidentCenter } from './components/IncidentCenter';
import type { Application, Assessment } from './client';
const mock=new MockAdapter(api);
beforeEach(()=>mock.reset());afterEach(()=>mock.reset());
const item:Application={id:'synthetic-app',user_id:'synthetic-user',product_id:'p1',assessment_id:'a1',amount:'100000',months:24,status:'draft',version:2,created_at:'2026-01-01T00:00:00Z',history:[]};
const assessment:Assessment={id:'a1',created_at:item.created_at,inputs:{monthly_income:'75000',obligations:'1000',employment:'salaried'},result:{indicative_eligible:true,monthly_installment:'1',estimated_repayment:'1',debt_to_income:'0.1',reasons:[],assumptions:[],disclaimer:'Synthetic estimate'}};
test('draft editor sends versioned edits and preserves form on conflict',async()=>{
 mock.onGet('/products?limit=100').reply(200,[{id:'p1',name:'Synthetic loan'}]);mock.onPut('/applications/synthetic-app').replyOnce(409,{detail:'Draft changed; refresh before editing again'});mock.onPut('/applications/synthetic-app').reply(200,{});
 const saved=vi.fn();render(<DraftEditor item={item} assessment={assessment} onSaved={saved} onCancel={()=>{}}/>);
 await waitFor(()=>expect(screen.getByRole('button',{name:'Save revised draft'})).toBeEnabled());fireEvent.change(screen.getByLabelText('Requested amount'),{target:{value:'120000'}});fireEvent.click(screen.getByRole('button',{name:'Save revised draft'}));expect(await screen.findByRole('alert')).toHaveTextContent('Draft changed');expect(saved).not.toHaveBeenCalled();expect(screen.getByLabelText('Requested amount')).toHaveValue(120000);fireEvent.click(screen.getByRole('button',{name:'Save revised draft'}));await waitFor(()=>expect(saved).toHaveBeenCalledOnce());expect(JSON.parse(mock.history.put[1].data)).toMatchObject({version:2,amount:'120000',months:24});
});
test('assistant renders hostile source text as text, never active HTML',async()=>{
 const hostile='<img src=x onerror="alert(1)"><script>alert(2)</script>';
 mock.onPost('/assistant').reply(200,{answer:hostile,mode:'local_extractive',retrieval:'local_hash512',warning:null,sources:[{title:'Synthetic source',chunk:0,excerpt:hostile}],stages:[]});
 const {container}=render(<MemoryRouter><ChatPanel/></MemoryRouter>);fireEvent.click(screen.getByRole('button',{name:'Ask the assistant'}));expect((await screen.findAllByText(hostile)).length).toBe(2);expect(container.querySelector('script')).toBeNull();expect(container.querySelector('img[src="x"]')).toBeNull();
});
test('incident action rejection is shown and does not claim success',async()=>{
 const incident={id:'i1',state:'detected',actor_id:'u1',version:1,created_at:'2026-01-01T00:00:00Z',recommended_action:'investigate',applied_action:'log',allowed_actions:['note','investigate']};
 mock.onGet('/admin/security/incidents?limit=25&offset=0').reply(200,[incident]);mock.onGet('/admin/security/incidents/i1').reply(200,{...incident,evidence:{category:'resource_access_denied',rules:['resource_access_denied'],features:{},correlation_id:'test-correlation'},risk:null,timeline:[],sessions:[],restrictions:[]});mock.onPost('/admin/security/incidents/i1/actions').reply(409,{detail:'Incident changed; reload it'});
 render(<IncidentCenter/>);fireEvent.click(await screen.findByRole('button',{name:'Investigate i1'}));await screen.findByLabelText('Action');expect(screen.queryByRole('option',{name:'restrict'})).not.toBeInTheDocument();fireEvent.change(screen.getByLabelText('Reason / investigation note'),{target:{value:'Synthetic investigation note'}});fireEvent.click(screen.getByRole('button',{name:'Apply authorized action'}));expect(await screen.findByRole('alert')).toHaveTextContent('Incident changed');expect(screen.queryByText('Action confirmed by the server.')).not.toBeInTheDocument();
});
