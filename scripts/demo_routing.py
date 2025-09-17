#!/usr/bin/env python3
"""
Demo script to show intelligent routing system
"""
import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gateway.router import IntelligentRouter

async def demo_routing():
    """Demonstrate the intelligent routing system"""

    print("🧠 AI Gateway Intelligent Routing Demo")
    print("=" * 50)

    router = IntelligentRouter()

    # Test scenarios
    scenarios = [
        {
            "prompt": "Write a Python function to calculate fibonacci numbers",
            "requirements": {},
            "description": "Code Generation Task"
        },
        {
            "prompt": "Tell me a creative story about robots",
            "requirements": {},
            "description": "Creative Writing Task"
        },
        {
            "prompt": "Analyze this data and explain the trends",
            "requirements": {"high_quality": True},
            "description": "Analysis Task (High Quality)"
        },
        {
            "prompt": "Quick answer: What's 2+2?",
            "requirements": {"low_latency": True},
            "description": "Simple Query (Low Latency)"
        },
        {
            "prompt": "Summarize this long document..." * 100,  # Long prompt
            "requirements": {"low_cost": True},
            "description": "Long Document (Cost Sensitive)"
        }
    ]

    print("Available Models:")
    for model_name, capabilities in router.providers.items():
        print(f"  • {model_name} ({capabilities.provider}) - {', '.join(capabilities.specialties)}")

    print("\n" + "=" * 50)

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n🎯 Scenario {i}: {scenario['description']}")
        print(f"Prompt: {scenario['prompt'][:50]}{'...' if len(scenario['prompt']) > 50 else ''}")
        print(f"Requirements: {scenario['requirements']}")

        # Get task classification
        task_type = router._classify_task(scenario['prompt'])
        print(f"Task Type: {task_type}")

        # Route the request
        result = await router.route_request(
            prompt=scenario['prompt'],
            preferred_model="auto",
            requirements=scenario['requirements']
        )

        selected_model = result['capabilities']
        print(f"✅ Selected: {selected_model.name} ({selected_model.provider})")
        print(f"   Reasons: Quality={selected_model.quality_score}, Cost=${selected_model.cost_per_1m_tokens:.2f}/1M")
        print(f"   Latency: {selected_model.avg_latency_ms}ms, Specialties: {selected_model.specialties}")

if __name__ == "__main__":
    asyncio.run(demo_routing())