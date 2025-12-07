#!/usr/bin/env python3
"""Pre-load the embedding model to avoid delays during testing.

This script downloads and caches the sentence-transformers model
so that subsequent RAG operations are faster.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("="*60)
print("Pre-loading Embedding Model")
print("="*60)
print("\nThis will download the sentence-transformers model (~80MB)")
print("This can take 5-10 minutes on Pi5, but only needs to be done once.")
print("\nModel: sentence-transformers/all-MiniLM-L6-v2")
print("="*60)

try:
    from sentence_transformers import SentenceTransformer
    
    print("\n📥 Downloading model...")
    print("   (This may take several minutes on first run)")
    
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    print("\n✅ Model loaded successfully!")
    print("   The model is now cached and future runs will be faster.")
    
    # Test encoding
    print("\n🧪 Testing model with sample text...")
    test_text = ["This is a test sentence."]
    embeddings = model.encode(test_text)
    print(f"   ✅ Generated embedding with dimension: {len(embeddings[0])}")
    
    print("\n" + "="*60)
    print("✅ Model pre-loading complete!")
    print("="*60)
    
except ImportError:
    print("\n❌ Error: sentence-transformers not installed")
    print("   Install with: pip install sentence-transformers")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Error loading model: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

