# Web Service Docker Image Optimization

## Problem
The web service Docker image was **~4GB** due to:
- `torch>=2.0.0` (~2GB)
- `transformers>=4.35.0` (~500MB)
- Other ML packages

## Solution
Optimized the Dockerfile to:

1. **Use ML base image** (`nuniesmith/fks:docker-ml-latest`) which already includes:
   - `sentence-transformers` (for embeddings)
   - `langchain`, `chromadb`, `ollama` (for RAG)
   - `numpy`, `pandas`, `TA-Lib`

2. **Make torch/transformers optional** via build argument:
   - Default: `ENABLE_TRANSFORMERS=false` (saves ~2.5GB)
   - Set `ENABLE_TRANSFORMERS=true` only if you need transformer models in RAG

3. **Filter requirements** to avoid installing packages already in base image

## Image Size Reduction

| Configuration | Estimated Size | Notes |
|--------------|----------------|-------|
| **Before** | ~4GB | Included torch + transformers |
| **After (default)** | ~1.5GB | torch/transformers skipped |
| **After (with transformers)** | ~4GB | If ENABLE_TRANSFORMERS=true |

## Usage

### Build without transformers (recommended - smaller image):
```bash
docker build -t nuniesmith/fks:web-latest .
# or explicitly:
docker build --build-arg ENABLE_TRANSFORMERS=false -t nuniesmith/fks:web-latest .
```

### Build with transformers (if needed for RAG):
```bash
docker build --build-arg ENABLE_TRANSFORMERS=true -t nuniesmith/fks:web-latest .
```

## RAG Features Impact

- ✅ **Still works**: sentence-transformers embeddings (in base image)
- ✅ **Still works**: LangChain, ChromaDB, Ollama (in base image)
- ❌ **Not available**: HuggingFace transformers models (needs torch)
- ⚠️ **Impact**: RAG features using transformers will fall back to Ollama/sentence-transformers

## GitHub Actions

The workflow builds with `ENABLE_TRANSFORMERS=false` by default to keep images small.
If you need transformers, modify the workflow or build locally with the flag.

## Recommendation

For production, use the default (without torch/transformers):
- Much smaller image (~1.5GB vs ~4GB)
- Faster pull/deploy times
- Still supports RAG via sentence-transformers and Ollama
- If you need transformers models, use the dedicated AI/analyze services instead

