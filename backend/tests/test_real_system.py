"""
Diagnostic tests to check the real system state
Run these to identify the actual problem with "query failed"
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import config
from rag_system import RAGSystem
import os


def test_api_key_exists():
    """Check if ANTHROPIC_API_KEY is set"""
    print("\n=== API Key Check ===")
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        print(f"✓ API key is set (length: {len(api_key)})")
        print(f"  First 10 chars: {api_key[:10]}...")
        return True
    else:
        print("✗ API key is NOT set!")
        print("  Fix: Set ANTHROPIC_API_KEY environment variable")
        return False


def test_chroma_db_exists():
    """Check if ChromaDB directory exists and has data"""
    print("\n=== ChromaDB Check ===")
    import os
    chroma_path = config.CHROMA_PATH

    if os.path.exists(chroma_path):
        print(f"✓ ChromaDB directory exists at: {chroma_path}")
        # List contents
        contents = os.listdir(chroma_path)
        print(f"  Contents: {contents}")
        return True
    else:
        print(f"✗ ChromaDB directory does NOT exist at: {chroma_path}")
        return False


def test_courses_loaded():
    """Check if any courses are loaded in the system"""
    print("\n=== Course Data Check ===")
    try:
        rag = RAGSystem(config)
        analytics = rag.get_course_analytics()

        print(f"Total courses: {analytics['total_courses']}")
        print(f"Course titles: {analytics['course_titles']}")

        if analytics['total_courses'] == 0:
            print("✗ No courses loaded!")
            print("  Fix: Run rag_system.add_course_folder('../docs')")
            return False
        else:
            print(f"✓ {analytics['total_courses']} courses loaded")
            return True
    except Exception as e:
        print(f"✗ Error checking courses: {e}")
        return False


def test_search_tool_works():
    """Test if search tool can execute"""
    print("\n=== Search Tool Test ===")
    try:
        rag = RAGSystem(config)

        # Test with a generic query
        result = rag.search_tool.execute(query="introduction")

        print(f"Search result length: {len(result)} characters")
        print(f"First 200 chars: {result[:200]}...")

        if "No relevant content found" in result:
            print("✗ Search returned no results")
            print("  This means either no data is loaded or search isn't working")
            return False
        else:
            print("✓ Search tool returned results")
            return True
    except Exception as e:
        print(f"✗ Error executing search: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tool_manager():
    """Test if tool manager has tools registered"""
    print("\n=== Tool Manager Check ===")
    try:
        rag = RAGSystem(config)
        tools = rag.tool_manager.get_tool_definitions()

        print(f"Number of tools registered: {len(tools)}")
        for tool in tools:
            print(f"  - {tool['name']}: {tool.get('description', 'No description')[:50]}...")

        if len(tools) == 0:
            print("✗ No tools registered!")
            return False
        else:
            print(f"✓ {len(tools)} tools registered")
            return True
    except Exception as e:
        print(f"✗ Error checking tools: {e}")
        return False


def test_ai_generator_initialization():
    """Test if AI generator can be initialized"""
    print("\n=== AI Generator Check ===")
    try:
        from ai_generator import AIGenerator

        api_key = config.ANTHROPIC_API_KEY
        if not api_key:
            print("✗ Cannot initialize - no API key")
            return False

        generator = AIGenerator(api_key, config.ANTHROPIC_MODEL)
        print(f"✓ AI Generator initialized with model: {config.ANTHROPIC_MODEL}")
        print(f"  Max tokens: {generator.base_params['max_tokens']}")
        print(f"  Temperature: {generator.base_params['temperature']}")
        return True
    except Exception as e:
        print(f"✗ Error initializing AI generator: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_query_flow():
    """Test a full query end-to-end (will fail if no API key)"""
    print("\n=== Full Query Test ===")
    print("WARNING: This will make a real API call if API key is set!")

    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("✗ Skipping - no API key set")
        return False

    try:
        rag = RAGSystem(config)

        # Check if data is loaded
        analytics = rag.get_course_analytics()
        if analytics['total_courses'] == 0:
            print("✗ Cannot test - no courses loaded")
            return False

        print("Attempting real query (this will call Anthropic API)...")
        answer, sources = rag.query("What is machine learning?")

        print(f"✓ Query succeeded!")
        print(f"  Answer length: {len(answer)} characters")
        print(f"  Number of sources: {len(sources)}")
        print(f"  First 200 chars of answer: {answer[:200]}...")

        return True
    except Exception as e:
        print(f"✗ Query failed with error: {e}")
        print("\nFull traceback:")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("="*60)
    print("DIAGNOSTIC TEST SUITE FOR RAG CHATBOT")
    print("="*60)

    results = {
        "API Key": test_api_key_exists(),
        "ChromaDB Exists": test_chroma_db_exists(),
        "Courses Loaded": test_courses_loaded(),
        "Search Tool": test_search_tool_works(),
        "Tool Manager": test_tool_manager(),
        "AI Generator": test_ai_generator_initialization(),
    }

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    # Only run full query test if basics pass
    if all([results["API Key"], results["Courses Loaded"], results["Search Tool"]]):
        print("\n" + "="*60)
        print("Running Full Query Test...")
        print("="*60)
        test_full_query_flow()

    print("\n" + "="*60)
    print("LIKELY ISSUE:")
    print("="*60)

    if not results["API Key"]:
        print("Missing ANTHROPIC_API_KEY - set this environment variable")
    elif not results["Courses Loaded"]:
        print("No courses loaded - ChromaDB is empty")
        print("Fix: Load docs with rag_system.add_course_folder('../docs')")
    elif not results["Search Tool"]:
        print("Search tool not working - check vector store")
    else:
        print("All basic checks pass - issue is likely in AI tool calling")
        print("Check app.py logs for detailed error messages")
