"""
Debug script to see EXACTLY what's in components
"""

import asyncio
import logging
from vanna_setup import get_agent
from vanna.core.user import RequestContext

logging.basicConfig(level=logging.DEBUG, format="%(message)s")
logger = logging.getLogger(__name__)

async def debug():
    print("\n" + "="*70)
    print("🔍 DEBUGGING COMPONENT EXTRACTION")
    print("="*70 + "\n")
    
    try:
        agent = get_agent()
        request_context = RequestContext()
        
        question = "How many patients do we have?"
        print(f"Question: {question}\n")
        
        response_stream = agent.send_message(
            message=question,
            request_context=request_context
        )
        
        component_num = 0
        
        async for component in response_stream:
            component_num += 1
            print(f"\n{'='*70}")
            print(f"COMPONENT {component_num}")
            print(f"{'='*70}")
            
            # Print raw component
            print(f"\nRaw component dict:")
            try:
                if hasattr(component, 'model_dump'):
                    comp_dict = component.model_dump()
                    print(json.dumps(comp_dict, indent=2, default=str)[:500])
                elif hasattr(component, '__dict__'):
                    print(str(component.__dict__)[:500])
            except:
                pass
            
            # Check simple_component
            print(f"\nSimple Component:")
            if hasattr(component, 'simple_component'):
                simple = component.simple_component
                print(f"  Type: {type(simple)}")
                print(f"  Value: {simple}")
                if simple is not None:
                    if hasattr(simple, 'model_dump'):
                        print(f"  Dict: {simple.model_dump()}")
                    elif hasattr(simple, '__dict__'):
                        print(f"  Dict: {simple.__dict__}")
                    if hasattr(simple, 'text'):
                        print(f"  TEXT: {simple.text}")
            
            # Check rich_component
            print(f"\nRich Component:")
            if hasattr(component, 'rich_component'):
                rich = component.rich_component
                print(f"  Type: {type(rich).__name__}")
                print(f"  Class: {rich.__class__.__name__}")
                if rich is not None:
                    if hasattr(rich, 'content'):
                        print(f"  CONTENT: {rich.content}")
                    if hasattr(rich, 'text'):
                        print(f"  TEXT: {rich.text}")
                    if hasattr(rich, 'model_dump'):
                        try:
                            dump = rich.model_dump()
                            print(f"  Keys: {list(dump.keys())}")
                            for k in ['content', 'text', 'message', 'sql', 'dataframe']:
                                if k in dump and dump[k]:
                                    print(f"  {k.upper()}: {str(dump[k])[:100]}")
                        except:
                            pass
        
        print(f"\n\n{'='*70}")
        print(f"Total components: {component_num}")
        print(f"{'='*70}\n")
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import json
    asyncio.run(debug())