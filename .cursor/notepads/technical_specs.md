# Technical Specifications & Constraints

## Hardware Profile

- **Device:** Raspberry Pi 5

- **RAM:** 16GB (Shared memory for CPU/GPU).

- **Storage:** 2TB NVMe SSD (Primary/Boot Drive - Fast I/O).

- **OS:** Raspberry Pi OS (Bookworm) - Boots from NVMe.

## Stack Choices

- **Language:** Python 3.11+

- **Local Inference:** Ollama (Service) with Llama 3.2 3B model.

- **Cloud Inference:** Google Gemini 2.0 Flash API (for complex reasoning and tool-use).

- **Agent Framework:** LangGraph or Swarm (for MCP support) - Planned.

- **Database:** SQLite (Metadata) + ChromaDB (Vectors) - Planned.

## Storage Configuration

- **Primary Drive:** 2TB NVMe SSD (boot drive) - All data, models, and OS on fast storage.

- **Ollama Models:** Default location `~/.ollama/models` (on NVMe). Models stored on fast NVMe for quick loading.

- **Project Data:** All project data (RAG vectors, audio, video) stored on NVMe for optimal I/O performance.

- **No Secondary Storage:** Single drive setup simplifies configuration - everything benefits from NVMe speed.

## Constraints

- **Memory Budget:** Keep local models < 6GB RAM to leave room for OS + RAG.

- **No Discrete GPU:** Avoid CUDA-only libraries; prefer CPU-optimized (OpenVINO / ONNX) or Metal/Vulkan if supported.

- **Storage:** 2TB provides ample space for models, RAG vectors, and media files. No need for external storage.

