"""
Load testing script for AI Gateway MCP Server
Simulates concurrent requests to test auto-scaling
"""
import asyncio
import time
import statistics
from typing import List, Dict
import aiohttp
import argparse
from datetime import datetime

async def make_request(session: aiohttp.ClientSession, url: str, prompt: str) -> Dict:
    """Make a single request to the gateway"""
    start = time.time()
    
    payload = {
        "prompt": prompt,
        "max_tokens": 100,
        "requirements": {"low_latency": True}
    }
    
    try:
        async with session.post(f"{url}/tools/unified_completion", json=payload) as response:
            result = await response.json()
            latency = (time.time() - start) * 1000
            
            return {
                "success": response.status == 200,
                "latency_ms": latency,
                "model": result.get("model"),
                "cached": result.get("cached", False)
            }
    except Exception as e:
        return {
            "success": False,
            "latency_ms": (time.time() - start) * 1000,
            "error": str(e)
        }

async def run_load_test(url: str, num_requests: int, concurrent: int):
    """Run load test with specified concurrency"""
    
    print(f"🚀 Starting load test")
    print(f"Target: {url}")
    print(f"Requests: {num_requests}")
    print(f"Concurrency: {concurrent}")
    print("-" * 50)
    
    # Test prompts with variety
    prompts = [
        "What is machine learning?",
        "Explain quantum computing",
        "How do neural networks work?",
        "What is cloud computing?",
        "Describe artificial intelligence"
    ]
    
    results = []
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        # Create batches
        for i in range(0, num_requests, concurrent):
            batch = []
            for j in range(min(concurrent, num_requests - i)):
                prompt = prompts[(i + j) % len(prompts)]
                batch.append(make_request(session, url, prompt))
            
            # Run batch concurrently
            batch_results = await asyncio.gather(*batch)
            results.extend(batch_results)
            
            print(f"Completed {len(results)}/{num_requests} requests")
    
    total_time = time.time() - start_time
    
    # Calculate statistics
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    latencies = [r["latency_ms"] for r in successful]
    cached = [r for r in successful if r.get("cached", False)]
    
    print("\n" + "=" * 50)
    print("📊 Load Test Results")
    print("=" * 50)
    print(f"Total Time: {total_time:.2f} seconds")
    print(f"Requests/sec: {num_requests / total_time:.2f}")
    print(f"Success Rate: {len(successful)}/{num_requests} ({len(successful)/num_requests*100:.1f}%)")
    print(f"Cache Hit Rate: {len(cached)}/{len(successful)} ({len(cached)/len(successful)*100:.1f}%)")
    
    if latencies:
        print(f"\nLatency Statistics (ms):")
        print(f"  Min: {min(latencies):.2f}")
        print(f"  Max: {max(latencies):.2f}")
        print(f"  Mean: {statistics.mean(latencies):.2f}")
        print(f"  Median: {statistics.median(latencies):.2f}")
        print(f"  P95: {statistics.quantiles(latencies, n=20)[18]:.2f}")
        print(f"  P99: {statistics.quantiles(latencies, n=100)[98]:.2f}")
    
    if failed:
        print(f"\n⚠️ Failed Requests: {len(failed)}")
        for f in failed[:5]:  # Show first 5 errors
            print(f"  - {f.get('error', 'Unknown error')}")

def main():
    parser = argparse.ArgumentParser(description="Load test AI Gateway MCP Server")
    parser.add_argument("--url", default="http://localhost:8080", help="Server URL")
    parser.add_argument("--requests", type=int, default=100, help="Total requests")
    parser.add_argument("--concurrent", type=int, default=10, help="Concurrent requests")
    
    args = parser.parse_args()
    
    asyncio.run(run_load_test(args.url, args.requests, args.concurrent))

if __name__ == "__main__":
    main()
