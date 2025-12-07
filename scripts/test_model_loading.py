#!/usr/bin/env python3
"""Test embedding model loading to diagnose issues.

This script tests if the embedding model can be loaded successfully.
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("="*60)
print("Testing Embedding Model Loading")
print("="*60)

try:
    from sentence_transformers import SentenceTransformer
    
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    
    print(f"\n📥 Loading model: {model_name}")
    print("   This may take 1-3 minutes on Pi5...")
    print("   (Model is already downloaded, just loading into memory)")
    
    start_time = time.time()
    
    try:
        model = SentenceTransformer(model_name)
        load_time = time.time() - start_time
        
        print(f"\n✅ Model loaded successfully in {load_time:.1f} seconds!")
        
        # Test encoding
        print("\n🧪 Testing encoding...")
        test_text = ["This is a test sentence for embedding."]
        encode_start = time.time()
        embeddings = model.encode(test_text)
        encode_time = time.time() - encode_start
        
        print(f"   ✅ Encoding completed in {encode_time:.2f} seconds")
        print(f"   Embedding dimension: {len(embeddings[0])}")
        
        print("\n" + "="*60)
        print("✅ Model loading test PASSED")
        print(f"   Load time: {load_time:.1f}s")
        print(f"   Encode time: {encode_time:.2f}s")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error loading model: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
except ImportError:
    print("\n❌ Error: sentence-transformers not installed")
    print("   Install with: pip install sentence-transformers")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

