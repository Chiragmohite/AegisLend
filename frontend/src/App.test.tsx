import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, expect, test, vi } from 'vitest';
import App from './App';
import { getHealth, getReadiness } from './api';
vi.mock('./api', () => ({ getHealth: vi.fn(), getReadiness: vi.fn() }));
beforeEach(() => vi.resetAllMocks());
test('shows live connection and database readiness', async () => {
  vi.mocked(getHealth).mockResolvedValue({ status: 'ok', service: 'aegislend-api' });
  vi.mocked(getReadiness).mockResolvedValue({ status: 'ready', service: 'aegislend-api', database: 'ready' });
  render(<MemoryRouter initialEntries={['/status']}><App /></MemoryRouter>);
  expect(await screen.findByText('Connected')).toBeInTheDocument();
  expect(await screen.findByText('Ready')).toBeInTheDocument();
});
test('shows failure and allows retry without a page reload', async () => {
  vi.mocked(getHealth).mockRejectedValueOnce(new Error('offline')).mockResolvedValue({ status: 'ok', service: 'aegislend-api' });
  vi.mocked(getReadiness).mockRejectedValue(new Error('offline'));
  render(<MemoryRouter initialEntries={['/status']}><App /></MemoryRouter>);
  await waitFor(() => expect(screen.getAllByText('Unavailable')).toHaveLength(2));
  fireEvent.click(screen.getByRole('button', { name: 'Check again' }));
  expect(await screen.findByText('Connected')).toBeInTheDocument();
});
test('handles unknown routes', () => {
  render(<MemoryRouter initialEntries={['/missing']}><App /></MemoryRouter>);
  expect(screen.getByText('Page not found')).toBeInTheDocument();
});

test('landing has no Foundation panel or reference portraits',()=>{render(<MemoryRouter><App/></MemoryRouter>);expect(screen.queryByText('Backend API')).not.toBeInTheDocument();expect(screen.queryByRole('img')).not.toBeInTheDocument();expect(screen.getByRole('link',{name:'Connection status'})).toHaveAttribute('href','/status')});
