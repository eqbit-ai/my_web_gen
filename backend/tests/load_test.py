"""
Load test: 1000 concurrent requests (600 single-page + 400 multi-page).

Usage:
    pip install aiohttp
    python tests/load_test.py --base-url http://localhost:8000

What it tests:
    1. Infrastructure capacity — can the API accept 1000 simultaneous connections?
    2. Job queue — can Redis queue 1000 jobs without dropping any?
    3. Database — can PG handle 1000 concurrent auth lookups + job inserts?
    4. Rate limiter — are limits correctly applied under pressure?

Note: This submits jobs to the queue but does NOT run actual LLM generation
      (that would cost thousands in API tokens). Workers should be stopped
      or pointed at a mock LLM to avoid real API calls.
"""

import argparse
import asyncio
import json
import random
import string
import sys
import time
from dataclasses import dataclass, field

import aiohttp

# ── Config ────────────────────────────────────────────────────────────

SINGLE_PAGE_COUNT = 600
MULTI_PAGE_COUNT = 400
TOTAL = SINGLE_PAGE_COUNT + MULTI_PAGE_COUNT

SINGLE_PAGE_PROMPTS = [
    "Create a modern website for a Dubai real estate agency",
    "Build a landing page for a luxury car rental company",
    "Design a website for an architecture firm in UAE",
    "Create a portfolio site for a photographer in Dubai",
    "Build a website for a restaurant in Meydan",
    "Design a corporate site for a consulting firm",
    "Create a website for a fitness center in Dubai",
    "Build a landing page for a travel agency",
    "Design a website for a tech startup in UAE",
    "Create a website for a beauty salon in Dubai Marina",
]

MULTI_PAGE_PROMPTS = [
    "Create a multi-page website for a law firm with home, about, services, and contact pages",
    "Build a full website for a hotel with home, rooms, dining, and booking pages",
    "Design a multi-page site for a school with home, programs, admissions, and contact",
    "Create a complete website for a clinic with home, services, doctors, and appointments",
    "Build a multi-page site for an event company with home, portfolio, services, and contact",
    "Design a full website for a car dealership with home, inventory, about, and contact pages",
    "Create a multi-page website for a marketing agency with home, work, team, and contact",
    "Build a complete site for a gym with home, classes, trainers, and membership pages",
]

NICHES = [
    "real_estate", "restaurant", "consulting", "fitness", "beauty",
    "technology", "travel", "architecture", "healthcare", "education",
]


# ── Result tracking ───────────────────────────────────────────────────

@dataclass
class LoadTestResults:
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    rate_limited: int = 0
    timeouts: int = 0
    connection_errors: int = 0
    other_errors: int = 0
    response_times: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    status_codes: dict = field(default_factory=dict)

    def record(self, status: int, elapsed: float, error: str = None):
        self.total_requests += 1
        self.response_times.append(elapsed)
        self.status_codes[status] = self.status_codes.get(status, 0) + 1

        if 200 <= status < 300:
            self.successful += 1
        elif status == 429:
            self.rate_limited += 1
        else:
            self.failed += 1
            if error:
                self.errors.append(f"[{status}] {error[:200]}")

    def record_error(self, error_type: str, msg: str):
        self.total_requests += 1
        if error_type == "timeout":
            self.timeouts += 1
        elif error_type == "connection":
            self.connection_errors += 1
        else:
            self.other_errors += 1
        self.errors.append(f"[{error_type}] {msg[:200]}")

    def summary(self) -> str:
        times = sorted(self.response_times) if self.response_times else [0]
        p50 = times[len(times) // 2]
        p95 = times[int(len(times) * 0.95)]
        p99 = times[int(len(times) * 0.99)]
        avg = sum(times) / len(times) if times else 0

        lines = [
            "",
            "=" * 70,
            "  LOAD TEST RESULTS",
            "=" * 70,
            f"  Total requests:       {self.total_requests:,}",
            f"  Successful (2xx):     {self.successful:,}  ({self.successful/max(self.total_requests,1)*100:.1f}%)",
            f"  Rate limited (429):   {self.rate_limited:,}",
            f"  Failed (other):       {self.failed:,}",
            f"  Timeouts:             {self.timeouts:,}",
            f"  Connection errors:    {self.connection_errors:,}",
            f"  Other errors:         {self.other_errors:,}",
            "",
            "  Response times (seconds):",
            f"    Average:  {avg:.3f}s",
            f"    P50:      {p50:.3f}s",
            f"    P95:      {p95:.3f}s",
            f"    P99:      {p99:.3f}s",
            f"    Min:      {times[0]:.3f}s",
            f"    Max:      {times[-1]:.3f}s",
            "",
            "  Status code breakdown:",
        ]
        for code, count in sorted(self.status_codes.items()):
            lines.append(f"    {code}: {count:,}")

        if self.errors:
            lines.append("")
            lines.append("  First 10 errors:")
            for e in self.errors[:10]:
                lines.append(f"    - {e}")

        lines.append("=" * 70)

        # Verdict
        success_rate = self.successful / max(self.total_requests, 1) * 100
        if success_rate >= 95:
            lines.append("  VERDICT: PASS — infrastructure handles 1000+ concurrent requests")
        elif success_rate >= 80:
            lines.append("  VERDICT: PARTIAL — most requests succeeded but some dropped")
        else:
            lines.append("  VERDICT: FAIL — too many failures under load")
        lines.append("=" * 70)

        return "\n".join(lines)


# ── Test user management ──────────────────────────────────────────────

def random_email():
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"loadtest_{suffix}@test.meydan.ae"


async def create_test_user(session: aiohttp.ClientSession, base_url: str) -> dict | None:
    """Create a test user and return {email, token}."""
    email = random_email()
    password = "LoadTest123!"
    payload = {
        "email": email,
        "password": password,
        "full_name": "Load Test User",
    }
    try:
        async with session.post(f"{base_url}/api/auth/signup", json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status == 200:
                data = await resp.json()
                return {"email": email, "token": data.get("token")}
            # User might already exist, try login
            if resp.status == 400:
                async with session.post(f"{base_url}/api/auth/login", json={"email": email, "password": password}, timeout=aiohttp.ClientTimeout(total=15)) as login_resp:
                    if login_resp.status == 200:
                        data = await login_resp.json()
                        return {"email": email, "token": data.get("token")}
    except Exception as e:
        print(f"  Failed to create user: {e}")
    return None


async def create_test_users(base_url: str, count: int) -> list[dict]:
    """Create test users in batches."""
    print(f"\n  Creating {count} test users...")
    users = []
    connector = aiohttp.TCPConnector(limit=50)
    async with aiohttp.ClientSession(connector=connector) as session:
        # Create in batches of 50
        for batch_start in range(0, count, 50):
            batch_size = min(50, count - batch_start)
            tasks = [create_test_user(session, base_url) for _ in range(batch_size)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, dict) and r:
                    users.append(r)
            print(f"    Created {len(users)}/{count} users...", end="\r")

    print(f"    Created {len(users)} test users successfully")
    return users


# ── Load test execution ──────────────────────────────────────────────

async def submit_job(
    session: aiohttp.ClientSession,
    base_url: str,
    token: str,
    prompt: str,
    is_multipage: bool,
    results: LoadTestResults,
    semaphore: asyncio.Semaphore,
):
    """Submit a single generation job."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "prompt": prompt,
        "niche": random.choice(NICHES),
        "designSystem": {},
        "sessionId": None,
    }

    async with semaphore:
        start = time.monotonic()
        try:
            async with session.post(
                f"{base_url}/api/jobs/submit",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                elapsed = time.monotonic() - start
                body = await resp.text()
                error = None
                if resp.status >= 400:
                    try:
                        error = json.loads(body).get("detail", body[:200])
                    except Exception:
                        error = body[:200]
                results.record(resp.status, elapsed, error)

        except TimeoutError:
            elapsed = time.monotonic() - start
            results.record_error("timeout", f"Request timed out after {elapsed:.1f}s")
        except aiohttp.ClientConnectionError as e:
            elapsed = time.monotonic() - start
            results.record_error("connection", str(e))
        except Exception as e:
            elapsed = time.monotonic() - start
            results.record_error("other", str(e))


async def health_check(base_url: str) -> bool:
    """Verify the server is up before testing."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/api/health", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                return resp.status == 200
    except Exception:
        return False


async def check_queue_depth(base_url: str, token: str) -> int | None:
    """Check current queue depth via admin endpoint."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/api/admin/generations/queue", headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("queue_depth", data.get("depth"))
    except Exception:
        pass
    return None


async def run_load_test(base_url: str, use_single_user: str = None):
    """Main load test orchestrator."""
    print("\n" + "=" * 70)
    print("  MEYDAN LOAD TEST — 1000 Concurrent Requests")
    print(f"  Target: {base_url}")
    print(f"  Single-page: {SINGLE_PAGE_COUNT} | Multi-page: {MULTI_PAGE_COUNT}")
    print("=" * 70)

    # Step 1: Health check
    print("\n  [1/4] Health check...")
    if not await health_check(base_url):
        print("  ERROR: Server is not responding. Start the server first.")
        sys.exit(1)
    print("  Server is healthy.")

    # Step 2: Create test users (or use provided token)
    if use_single_user:
        print("\n  [2/4] Using provided token for all requests")
        users = [{"email": "admin", "token": use_single_user}] * TOTAL
    else:
        print("\n  [2/4] Creating test users...")
        users = await create_test_users(base_url, min(TOTAL, 200))
        if len(users) < 10:
            print("  ERROR: Could not create enough test users.")
            sys.exit(1)
        # Spread users across requests (reuse if fewer than 1000)
        while len(users) < TOTAL:
            users.extend(users[:TOTAL - len(users)])
        users = users[:TOTAL]

    # Step 3: Prepare requests
    print(f"\n  [3/4] Preparing {TOTAL} requests...")
    requests = []

    # 600 single-page
    for i in range(SINGLE_PAGE_COUNT):
        requests.append({
            "user": users[i],
            "prompt": random.choice(SINGLE_PAGE_PROMPTS),
            "multipage": False,
        })

    # 400 multi-page
    for i in range(MULTI_PAGE_COUNT):
        requests.append({
            "user": users[SINGLE_PAGE_COUNT + i],
            "prompt": random.choice(MULTI_PAGE_PROMPTS),
            "multipage": True,
        })

    # Shuffle to mix single and multi-page
    random.shuffle(requests)

    # Step 4: Fire all requests
    print(f"\n  [4/4] Firing {TOTAL} concurrent requests...")
    results = LoadTestResults()

    # Allow up to 1000 concurrent connections
    connector = aiohttp.TCPConnector(
        limit=1000,
        limit_per_host=1000,
        ttl_dns_cache=300,
        enable_cleanup_closed=True,
    )
    semaphore = asyncio.Semaphore(1000)

    start_time = time.monotonic()

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            submit_job(
                session=session,
                base_url=base_url,
                token=req["user"]["token"],
                prompt=req["prompt"],
                is_multipage=req["multipage"],
                results=results,
                semaphore=semaphore,
            )
            for req in requests
        ]

        # Progress tracker
        done_count = 0
        total_tasks = len(tasks)

        async def progress_monitor():
            nonlocal done_count
            while done_count < total_tasks:
                await asyncio.sleep(1)
                completed = results.total_requests
                rate = completed / max(time.monotonic() - start_time, 0.1)
                print(f"    Progress: {completed}/{total_tasks} ({rate:.0f} req/s) | "
                      f"OK: {results.successful} | 429: {results.rate_limited} | "
                      f"Err: {results.failed + results.timeouts + results.connection_errors}",
                      end="\r")

        monitor = asyncio.create_task(progress_monitor())

        await asyncio.gather(*tasks, return_exceptions=True)
        done_count = total_tasks
        monitor.cancel()

    total_time = time.monotonic() - start_time

    print(f"\n\n  Completed in {total_time:.1f}s ({TOTAL / total_time:.0f} req/s throughput)")
    print(results.summary())


# ── Lighter alternative: API stress test (no user creation) ───────────

async def run_api_stress_test(base_url: str):
    """
    Quick stress test that hits lightweight endpoints (health, niches)
    to verify the infrastructure can handle 1000+ concurrent connections
    without needing user accounts.
    """
    print("\n" + "=" * 70)
    print("  MEYDAN API STRESS TEST — 1000 Concurrent Connections")
    print(f"  Target: {base_url}")
    print("=" * 70)

    if not await health_check(base_url):
        print("  ERROR: Server not responding.")
        sys.exit(1)

    results = LoadTestResults()
    connector = aiohttp.TCPConnector(limit=1000, limit_per_host=1000)
    semaphore = asyncio.Semaphore(1000)

    endpoints = [
        "/api/health",
        "/api/health/deep",
        "/api/generator/niches",
    ]

    async def hit_endpoint(session, url, results, semaphore):
        async with semaphore:
            start = time.monotonic()
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    elapsed = time.monotonic() - start
                    await resp.read()
                    error = None if resp.status < 400 else f"Status {resp.status}"
                    results.record(resp.status, elapsed, error)
            except TimeoutError:
                results.record_error("timeout", f"Timeout after {time.monotonic()-start:.1f}s")
            except aiohttp.ClientConnectionError as e:
                results.record_error("connection", str(e))
            except Exception as e:
                results.record_error("other", str(e))

    print(f"\n  Firing 1000 requests across {len(endpoints)} endpoints...")
    start_time = time.monotonic()

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for i in range(1000):
            url = f"{base_url}{endpoints[i % len(endpoints)]}"
            tasks.append(hit_endpoint(session, url, results, semaphore))
        await asyncio.gather(*tasks, return_exceptions=True)

    total_time = time.monotonic() - start_time
    print(f"  Completed in {total_time:.1f}s ({1000 / total_time:.0f} req/s)")
    print(results.summary())


# ── CLI ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Meydan Load Test — 1000 concurrent requests")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--token", default=None, help="Use a single auth token for all requests (skip user creation)")
    parser.add_argument("--stress-only", action="store_true", help="Quick infrastructure stress test (no auth needed)")
    parser.add_argument("--single", type=int, default=SINGLE_PAGE_COUNT, help="Number of single-page requests")
    parser.add_argument("--multi", type=int, default=MULTI_PAGE_COUNT, help="Number of multi-page requests")
    args = parser.parse_args()

    SINGLE_PAGE_COUNT = args.single
    MULTI_PAGE_COUNT = args.multi
    TOTAL = SINGLE_PAGE_COUNT + MULTI_PAGE_COUNT

    if args.stress_only:
        asyncio.run(run_api_stress_test(args.base_url))
    else:
        asyncio.run(run_load_test(args.base_url, use_single_user=args.token))
