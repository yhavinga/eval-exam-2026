#!/bin/bash
# Gemma 4 31B with vLLM on dual RTX 3090
# Based on club-3090 configuration + local optimizations
# https://github.com/noonghunna/club-3090
#
# Advantages over ik_llama.cpp:
#   - Vision + MTP work TOGETHER
#   - Multi-stream batching (4 concurrent requests)
#   - Higher throughput via tensor parallelism
#
# Requirements:
#   - Intel AutoRound INT4 model: Intel/gemma-4-31B-it-int4-AutoRound
#   - Google MTP assistant: google/gemma-4-31B-it-assistant
#   - NVIDIA driver 595+ / CUDA 13.2+
#
# Performance (dual 3090, tested 2026-05-25):
#   - Generation: ~57+ tok/s (warming up to higher)
#   - MTP acceptance: 80-100%
#   - Context: 32K (BF16 KV)
#
# Reasoning output: enabled via --reasoning-parser gemma4
#   Response field: "reasoning" (not "reasoning_content")
#   Request params for thinking:
#     "chat_template_kwargs": {"enable_thinking": true},
#     "skip_special_tokens": false  (workaround for issue #38855)
#
# Key settings for RTX 3090:
#   - --disable-custom-all-reduce: Required for CUDA graphs on RTX 3090
#   - cudagraph_mode: FULL_DECODE_ONLY: Enables graphs on 24GB GPUs
#   - cudagraph_capture_sizes: Reduced set for memory efficiency

MODEL_DIR="${MODEL_DIR:-/home/yeb/.lmstudio/models}"
PORT="${PORT:-8030}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-32768}"
GPU_MEM_UTIL="${GPU_MEM_UTIL:-0.92}"
NUM_SPEC_TOKENS="${NUM_SPEC_TOKENS:-4}"

# Use vLLM nightly with Gemma 4 MTP support (PR #41745, merged 2026-05-06)
# Club-3090 recommends: nightly-1acd67a795... or newer
# Check available tags: docker pull vllm/vllm-openai:latest (or specific nightly)
VLLM_IMAGE="${VLLM_IMAGE:-vllm/vllm-openai:latest}"
# For specific nightly: VLLM_IMAGE=vllm/vllm-openai:nightly-1acd67a795...

docker run --rm -it \
  --gpus all \
  --shm-size 16gb \
  --ipc host \
  -p "${PORT}:8000" \
  -v "${MODEL_DIR}:/models:ro" \
  -e VLLM_WORKER_MULTIPROC_METHOD=spawn \
  -e NCCL_CUMEM_ENABLE=0 \
  -e NCCL_P2P_DISABLE=1 \
  -e VLLM_NO_USAGE_STATS=1 \
  -e VLLM_ALLOW_LONG_MAX_MODEL_LEN=1 \
  -e PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:512 \
  "${VLLM_IMAGE}" \
  --host 0.0.0.0 \
  --port 8000 \
  --model /models/Intel/gemma-4-31B-it-int4-AutoRound \
  --served-model-name gemma-4-31b \
  --tensor-parallel-size 2 \
  --dtype bfloat16 \
  --max-model-len "${MAX_MODEL_LEN}" \
  --gpu-memory-utilization "${GPU_MEM_UTIL}" \
  --max-num-seqs 4 \
  --max-num-batched-tokens 4096 \
  --trust-remote-code \
  --disable-custom-all-reduce \
  --compilation-config '{"cudagraph_mode": "FULL_DECODE_ONLY", "cudagraph_capture_sizes": [1, 2, 4, 8]}' \
  --enable-auto-tool-choice \
  --tool-call-parser gemma4 \
  --reasoning-parser gemma4 \
  --speculative-config "{\"model\":\"/models/google/gemma-4-31B-it-assistant\",\"num_speculative_tokens\":${NUM_SPEC_TOKENS}}" \
  "$@"
