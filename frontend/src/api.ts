import axios from 'axios';
export const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1', timeout: 6000 });
export interface Health { status: 'ok' | 'ready' | 'unavailable'; service: string; database?: 'ready' | 'unavailable' }
export async function getHealth(signal?: AbortSignal): Promise<Health> {
  const { data } = await api.get<Health>('/health/live', { signal });
  if (data.status !== 'ok' || data.service !== 'aegislend-api') throw new Error('Invalid API response');
  return data;
}
export async function getReadiness(signal?: AbortSignal): Promise<Health> {
  const { data } = await api.get<Health>('/health/ready', { signal });
  if (data.status !== 'ready' || data.database !== 'ready') throw new Error('Database unavailable');
  return data;
}
