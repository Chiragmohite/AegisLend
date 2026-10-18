import { useEffect, useState } from 'react';
import { getHealth, getReadiness } from './api';

export function StatusPage() {
  const [attempt, setAttempt] = useState(0);
  const [apiStatus, setApiStatus] = useState('Checking');
  const [dbStatus, setDbStatus] = useState('Checking');
  useEffect(() => {
    const controller = new AbortController();
    setApiStatus('Checking'); setDbStatus('Checking');
    getHealth(controller.signal).then(() => {
      if (!controller.signal.aborted) setApiStatus('Connected');
    }).catch(() => { if (!controller.signal.aborted) setApiStatus('Unavailable'); });
    getReadiness(controller.signal).then(() => {
      if (!controller.signal.aborted) setDbStatus('Ready');
    }).catch(() => { if (!controller.signal.aborted) setDbStatus('Unavailable'); });
    return () => controller.abort();
  }, [attempt]);
  return <main id="main-content" className="mx-auto max-w-5xl px-6 py-16">
    <p className="text-xs font-bold uppercase tracking-widest text-teal-700">Application / Connection status</p>
    <h1 className="mt-4 text-4xl font-semibold tracking-tight">Service connection status.</h1>
    <p className="mt-5 max-w-2xl text-lg text-slate-600">Check the API connection and database readiness. This diagnostic page does not test every application workflow.</p>
    <div className="mt-10 grid gap-5 sm:grid-cols-2" aria-live="polite">
      <StatusCard label="Backend API" value={apiStatus} />
      <StatusCard label="MySQL database" value={dbStatus} />
    </div>
    <button className="mt-6 rounded-lg bg-teal-800 px-5 py-3 font-medium text-white focus-visible:outline-2 focus-visible:outline-offset-4" onClick={() => setAttempt(n => n + 1)}>Check again</button>
    <p className="mt-10 rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-600">Academic demonstration only. Use synthetic information. Estimates are not approvals; application decisions require authorized human review.</p>
  </main>;
}
function StatusCard({ label, value }: { label: string; value: string }) {
  return <section className="rounded-xl border border-slate-200 bg-white p-7 shadow-sm">
    <h2 className="text-sm text-slate-500">{label}</h2><p className="mt-3 text-2xl font-semibold">{value}</p>
  </section>;
}
