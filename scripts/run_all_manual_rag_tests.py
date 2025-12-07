#!/usr/bin/env python3
"""Run all manual RAG tests sequentially.

This script runs all 5 manual test scenarios one by one.
Each test can be run individually or all together.
"""

import asyncio
import sys
import subprocess
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def run_test(test_number: int, test_name: str, script_path: str):
    """Run a single manual test."""
    print("\n" + "="*70)
    print(f"Running Test {test_number}: {test_name}")
    print("="*70)
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=False,
            text=True,
            timeout=120  # 2 minute timeout per test
        )
        
        if result.returncode == 0:
            print(f"\n✅ Test {test_number} completed successfully")
            return True
        else:
            print(f"\n❌ Test {test_number} failed with exit code {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"\n⏱️  Test {test_number} timed out after 2 minutes")
        return False
    except Exception as e:
        print(f"\n❌ Test {test_number} error: {e}")
        return False


async def main():
    """Run all manual tests."""
    print("="*70)
    print("Mini-JARVIS RAG Pipeline - Manual Testing Suite")
    print("="*70)
    print("\nThis will run 5 manual test scenarios:")
    print("  1. Ingest TXT → Verify Retrieval")
    print("  2. Ingest PDF → Test Chunking")
    print("  3. Query with No Matches → Graceful Failure")
    print("  4. Large Document → Performance Test")
    print("  5. Reboot → Persistence Check")
    
    response = input("\nRun all tests? (y/n): ").strip().lower()
    if response != 'y':
        print("Cancelled.")
        return
    
    scripts_dir = Path(__file__).parent
    tests = [
        (1, "Ingest TXT → Verify Retrieval", scripts_dir / "manual_test_rag_1_txt_retrieval.py"),
        (2, "Ingest PDF → Test Chunking", scripts_dir / "manual_test_rag_2_pdf_chunking.py"),
        (3, "Query with No Matches → Graceful Failure", scripts_dir / "manual_test_rag_3_no_matches.py"),
        (4, "Large Document → Performance Test", scripts_dir / "manual_test_rag_4_performance.py"),
        (5, "Reboot → Persistence Check", scripts_dir / "manual_test_rag_5_persistence.py"),
    ]
    
    results = []
    for test_num, test_name, script_path in tests:
        if not script_path.exists():
            print(f"\n❌ Script not found: {script_path}")
            results.append(False)
            continue
        
        success = await run_test(test_num, test_name, str(script_path))
        results.append(success)
        
        # Ask if user wants to continue after each test
        if test_num < len(tests):
            response = input(f"\nContinue to next test? (y/n): ").strip().lower()
            if response != 'y':
                print("Stopped by user.")
                break
    
    # Summary
    print("\n" + "="*70)
    print("MANUAL TEST SUMMARY")
    print("="*70)
    passed = sum(results)
    total = len(results)
    
    for i, (test_num, test_name, _) in enumerate(tests[:len(results)]):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"{status} - Test {test_num}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*70)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

