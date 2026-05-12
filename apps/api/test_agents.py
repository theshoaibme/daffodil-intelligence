import asyncio
import sys
sys.path.insert(0, '/Users/ratulhasan/Desktop/Shoaib/daffodil-intelligence/apps/api')

from app.agents.academic import AcademicAgent
from app.agents.library import LibraryAgent
from app.agents.campus import CampusAgent
from app.agents.career import CareerAgent
from app.agents.coding import CodingAgent
from app.agents.research import ResearchAgent
from app.agents.wellness import WellnessAgent
from app.agents.finance import FinanceAgent
from app.agents.vision import VisionAgent
from app.agents.voice import VoiceAgent


async def test_all_agents():
    print("\n" + "="*60)
    print("DAFFODIL INTELLIGENCE - AGENT TEST SUITE")
    print("="*60)
    
    agents = [
        ("Academic Agent", AcademicAgent(), "What's my CGPA?"),
        ("Library Agent", LibraryAgent(), "Find books on Machine Learning"),
        ("Campus Agent", CampusAgent(), "What's the shuttle schedule?"),
        ("Career Agent", CareerAgent(), "Show me available jobs"),
        ("Coding Agent", CodingAgent(), "Debug: undefined is not a function"),
        ("Research Agent", ResearchAgent(), "Find papers on Deep Learning"),
        ("Wellness Agent", WellnessAgent(), "I'm feeling stressed"),
        ("Finance Agent", FinanceAgent(), "What's my pending fees?"),
        ("Vision Agent", VisionAgent(), "Analyze this image"),
        ("Voice Agent", VoiceAgent(), "Convert speech to text"),
    ]
    
    for name, agent, query in agents:
        print(f"\n{'='*50}")
        print(f"TESTING: {name}")
        print(f"{'='*50}")
        print(f"Query: {query}")
        try:
            result = await agent.process(query)
            print(f"\n✓ Response: {result[:300]}...")
        except Exception as e:
            print(f"\n✗ Error: {e}")
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_all_agents())