import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    search: {
      executor: 'constant-vus',
      vus: 10,
      duration: '30s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<1500'],
  },
};

const baseUrl = __ENV.API_URL || 'http://localhost:8000/api/v1';
const token = __ENV.ACCESS_TOKEN;

export default function () {
  const response = http.post(
    `${baseUrl}/search`,
    JSON.stringify({ query: 'computer science scholarship in Germany' }),
    {
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    },
  );
  check(response, { 'search responds': (res) => [200, 401, 429].includes(res.status) });
  sleep(1);
}
