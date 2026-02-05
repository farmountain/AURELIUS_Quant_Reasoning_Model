"""
Load testing suite for AURELIUS API
Tests API performance under load using concurrent requests
"""
import asyncio
import aiohttp
import time
import statistics
from datetime import datetime
from typing import List, Dict, Any
import sys

API_BASE_URL = "http://localhost:8000/api"


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'


class LoadTester:
    """Load testing utility for API endpoints"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.results = []
    
    async def make_request(
        self,
        session: aiohttp.ClientSession,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make a single HTTP request and measure time"""
        start_time = time.time()
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with session.request(method, url, **kwargs) as response:
                await response.text()
                elapsed = time.time() - start_time
                
                return {
                    "success": True,
                    "status": response.status,
                    "time": elapsed,
                    "endpoint": endpoint,
                }
        except Exception as e:
            elapsed = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "time": elapsed,
                "endpoint": endpoint,
            }
    
    async def concurrent_requests(
        self,
        method: str,
        endpoint: str,
        num_requests: int,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Make multiple concurrent requests to an endpoint"""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.make_request(session, method, endpoint, **kwargs)
                for _ in range(num_requests)
            ]
            return await asyncio.gather(*tasks)
    
    def calculate_stats(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics from request results"""
        times = [r["time"] for r in results]
        successes = [r for r in results if r.get("success")]
        failures = [r for r in results if not r.get("success")]
        
        if not times:
            return {}
        
        return {
            "total_requests": len(results),
            "successful": len(successes),
            "failed": len(failures),
            "success_rate": (len(successes) / len(results)) * 100,
            "total_time": sum(times),
            "avg_time": statistics.mean(times),
            "median_time": statistics.median(times),
            "min_time": min(times),
            "max_time": max(times),
            "p95_time": statistics.quantiles(times, n=20)[18] if len(times) > 1 else max(times),
            "p99_time": statistics.quantiles(times, n=100)[98] if len(times) > 1 else max(times),
        }
    
    def print_stats(self, endpoint: str, stats: Dict[str, Any]):
        """Print statistics in a formatted way"""
        print(f"\n{Colors.CYAN}{'='*70}{Colors.END}")
        print(f"{Colors.BLUE}Endpoint: {endpoint}{Colors.END}")
        print(f"{Colors.CYAN}{'='*70}{Colors.END}")
        
        print(f"Total Requests:    {stats['total_requests']}")
        print(f"Successful:        {Colors.GREEN}{stats['successful']}{Colors.END}")
        print(f"Failed:            {Colors.RED}{stats['failed']}{Colors.END}")
        print(f"Success Rate:      {stats['success_rate']:.2f}%")
        print(f"\n{Colors.YELLOW}Response Times:{Colors.END}")
        print(f"  Average:         {stats['avg_time']*1000:.2f} ms")
        print(f"  Median:          {stats['median_time']*1000:.2f} ms")
        print(f"  Min:             {stats['min_time']*1000:.2f} ms")
        print(f"  Max:             {stats['max_time']*1000:.2f} ms")
        print(f"  P95:             {stats['p95_time']*1000:.2f} ms")
        print(f"  P99:             {stats['p99_time']*1000:.2f} ms")
        print(f"\n{Colors.YELLOW}Throughput:{Colors.END}")
        print(f"  Requests/sec:    {stats['total_requests']/stats['total_time']:.2f}")


async def test_health_endpoint(tester: LoadTester, num_requests: int = 100):
    """Test /health endpoint"""
    print(f"\n{Colors.BLUE}Testing /health endpoint with {num_requests} requests...{Colors.END}")
    results = await tester.concurrent_requests("GET", "/health", num_requests)
    stats = tester.calculate_stats(results)
    tester.print_stats("/health", stats)
    return stats


async def test_metrics_endpoint(tester: LoadTester, num_requests: int = 50):
    """Test /metrics endpoint"""
    print(f"\n{Colors.BLUE}Testing /metrics endpoint with {num_requests} requests...{Colors.END}")
    results = await tester.concurrent_requests("GET", "/metrics", num_requests)
    stats = tester.calculate_stats(results)
    tester.print_stats("/metrics", stats)
    return stats


async def test_strategies_list(tester: LoadTester, token: str, num_requests: int = 50):
    """Test /strategies/ list endpoint"""
    print(f"\n{Colors.BLUE}Testing /strategies/ endpoint with {num_requests} requests...{Colors.END}")
    headers = {"Authorization": f"Bearer {token}"}
    results = await tester.concurrent_requests(
        "GET", "/strategies/", num_requests, headers=headers
    )
    stats = tester.calculate_stats(results)
    tester.print_stats("/strategies/", stats)
    return stats


async def test_backtests_list(tester: LoadTester, token: str, num_requests: int = 50):
    """Test /backtests/ list endpoint"""
    print(f"\n{Colors.BLUE}Testing /backtests/ endpoint with {num_requests} requests...{Colors.END}")
    headers = {"Authorization": f"Bearer {token}"}
    results = await tester.concurrent_requests(
        "GET", "/backtests/", num_requests, headers=headers
    )
    stats = tester.calculate_stats(results)
    tester.print_stats("/backtests/", stats)
    return stats


async def register_test_user(tester: LoadTester) -> str:
    """Register a test user and return token"""
    test_email = f"loadtest_{int(time.time())}@example.com"
    payload = {
        "email": test_email,
        "password": "testpassword123",
        "name": "Load Test User"
    }
    
    async with aiohttp.ClientSession() as session:
        result = await tester.make_request(
            session, "POST", "/auth/register", json=payload
        )
        
        if result.get("success"):
            # Get token from response
            async with session.post(
                f"{tester.base_url}/auth/register",
                json=payload
            ) as response:
                data = await response.json()
                return data.get("access_token", "")
        return ""


async def main():
    """Run load tests"""
    print(f"\n{Colors.CYAN}{'='*70}")
    print("AURELIUS API Load Testing Suite")
    print(f"{'='*70}{Colors.END}\n")
    print(f"API URL: {API_BASE_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    tester = LoadTester()
    
    # Test public endpoints
    health_stats = await test_health_endpoint(tester, num_requests=100)
    metrics_stats = await test_metrics_endpoint(tester, num_requests=50)
    
    # Register user for authenticated endpoints
    print(f"\n{Colors.BLUE}Registering test user...{Colors.END}")
    token = await register_test_user(tester)
    
    if token:
        print(f"{Colors.GREEN}✓ Test user registered{Colors.END}")
        
        # Test authenticated endpoints
        await test_strategies_list(tester, token, num_requests=50)
        await test_backtests_list(tester, token, num_requests=50)
    else:
        print(f"{Colors.RED}✗ Failed to register test user{Colors.END}")
    
    # Summary
    print(f"\n{Colors.CYAN}{'='*70}")
    print("Load Testing Summary")
    print(f"{'='*70}{Colors.END}\n")
    
    all_stats = [health_stats, metrics_stats]
    total_requests = sum(s.get("total_requests", 0) for s in all_stats)
    total_successful = sum(s.get("successful", 0) for s in all_stats)
    avg_success_rate = statistics.mean([s.get("success_rate", 0) for s in all_stats])
    avg_response_time = statistics.mean([s.get("avg_time", 0) for s in all_stats])
    
    print(f"Total Requests:        {total_requests}")
    print(f"Total Successful:      {Colors.GREEN}{total_successful}{Colors.END}")
    print(f"Average Success Rate:  {avg_success_rate:.2f}%")
    print(f"Average Response Time: {avg_response_time*1000:.2f} ms")
    
    if avg_success_rate >= 99.0 and avg_response_time < 0.5:
        print(f"\n{Colors.GREEN}✓ Performance: EXCELLENT{Colors.END}")
    elif avg_success_rate >= 95.0 and avg_response_time < 1.0:
        print(f"\n{Colors.YELLOW}✓ Performance: GOOD{Colors.END}")
    else:
        print(f"\n{Colors.RED}⚠ Performance: NEEDS IMPROVEMENT{Colors.END}")
    
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Load testing interrupted{Colors.END}\n")
    except Exception as e:
        print(f"\n{Colors.RED}Error: {str(e)}{Colors.END}\n")
        sys.exit(1)
