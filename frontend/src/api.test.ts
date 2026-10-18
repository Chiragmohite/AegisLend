import { afterEach, expect, test } from 'vitest';
import MockAdapter from 'axios-mock-adapter';
import { api, getHealth, getReadiness } from './api';
const mock = new MockAdapter(api);
afterEach(() => mock.reset());
test('uses the versioned health endpoint', async () => {
  mock.onGet('/health/live').reply(200, { status: 'ok', service: 'aegislend-api' });
  expect((await getHealth()).status).toBe('ok');
  expect(mock.history.get[0].baseURL).toBe('/api/v1');
});
test('rejects malformed responses', async () => {
  mock.onGet('/health/live').reply(200, '<html>wrong server</html>');
  await expect(getHealth()).rejects.toThrow('Invalid API response');
});
test('propagates unavailable database', async () => {
  mock.onGet('/health/ready').reply(503, { status: 'unavailable' });
  await expect(getReadiness()).rejects.toThrow();
});
