import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 10,
  iterations: 30,
};

export default function () {
  const url = `${__ENV.BASE_URL || 'http://localhost:5000'}/auth/token`;
  const payload = JSON.stringify({ email: 'u@example.com', password: 'wrong' });
  const params = { headers: { 'Content-Type': 'application/json' } };
  const res = http.post(url, payload, params);
  check(res, {
    'status is 401 or 429': (r) => r.status === 401 || r.status === 429,
  });
}
