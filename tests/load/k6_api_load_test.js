/**
 * GER2 CMMS — k6 Load Test
 * Target: 200 concurrent users, p95 < 200ms
 * Run: k6 run k6_api_load_test.js
 */
import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Trend } from "k6/metrics";

const errorRate   = new Rate("errors");
const assetTrend  = new Trend("asset_list_duration");
const woDashTrend = new Trend("wo_dashboard_duration");

export const options = {
  stages: [
    { duration: "1m",  target: 50  },   // ramp-up
    { duration: "3m",  target: 200 },   // steady state
    { duration: "1m",  target: 0   },   // ramp-down
  ],
  thresholds: {
    http_req_duration:    ["p(95)<200"],   // p95 < 200ms
    http_req_failed:      ["rate<0.01"],   // <1% errors
    asset_list_duration:  ["p(95)<150"],
  },
};

const BASE = __ENV.API_BASE_URL || "http://localhost:8000/api/v1";
let TOKEN = "";

export function setup() {
  const res = http.post(`${BASE}/auth/login`, JSON.stringify({
    email: __ENV.TEST_USER_EMAIL || "loadtest@ger2.tn",
    password: __ENV.TEST_USER_PASSWORD || "LoadTest@2024!",
  }), { headers: { "Content-Type": "application/json" } });
  return { token: res.json("access_token") };
}

export default function (data) {
  const headers = {
    Authorization: `Bearer ${data.token}`,
    "Content-Type": "application/json",
  };

  // Asset list
  const r1 = http.get(`${BASE}/assets?limit=50`, { headers });
  check(r1, { "assets 200": (r) => r.status === 200 });
  errorRate.add(r1.status !== 200);
  assetTrend.add(r1.timings.duration);

  sleep(0.5);

  // WO dashboard
  const r2 = http.get(`${BASE}/workorders?limit=50`, { headers });
  check(r2, { "workorders 200": (r) => r.status === 200 });
  errorRate.add(r2.status !== 200);
  woDashTrend.add(r2.timings.duration);

  sleep(0.5);

  // AI agents
  const r3 = http.get(`${BASE}/ai/agents`, { headers });
  check(r3, { "agents 200": (r) => r.status === 200 });

  sleep(1);
}
