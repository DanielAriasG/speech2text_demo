import os
import sys
import time
import io
import soundfile as sf
from datasets import load_dataset, Audio
from jiwer import wer

# Ensure path is correct to import backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.core.model_registry import ModelRegistry

def run_benchmark(num_samples=10):
    print("Loading local ASR models into ModelRegistry...")
    try:
        from backend.models.whisper_impl import WhisperModel
        ModelRegistry.register("whisper", WhisperModel())
    except Exception as e:
        print(f"Skipping whisper: {e}")
        
    try:
        from backend.models.canary_impl import CanaryModel
        ModelRegistry.register("canary", CanaryModel())
    except Exception as e:
        print(f"Skipping canary: {e}")
        
    try:
        from backend.models.parakeet_impl import ParakeetModel
        ModelRegistry.register("parakeet", ParakeetModel())
    except Exception as e:
        print(f"Skipping parakeet: {e}")

    print("Loading HuggingFace dataset...")
    # Attempting the dataset names provided by the user and the repository
    try:
        ds = load_dataset("pipecat-ai/stt-benchmark-data", split="train")
    except Exception:
        print("Fallback to pipecat-ai/smart-turn-data-v3.1-train")
        ds = load_dataset("pipecat-ai/smart-turn-data-v3.1-train", split="train")

    # Cast Audio column to NOT decode, dodging torchaudio DLL crashing on Windows
    ds = ds.cast_column("audio", Audio(decode=False))
    subset = ds.select(range(min(num_samples, len(ds))))
    
    models_to_test = ["whisper", "canary", "parakeet"]
    results = {m: {"wer": 0.0, "latency": 0.0, "count": 0} for m in models_to_test}

    print(f"Beginning benchmarking for {len(subset)} samples...\n")
    
    for idx, row in enumerate(subset):
        # Extract audio and ground truth text
        audio_dict = row["audio"]
        reference_text = row.get("transcription", "")
        
        # Protect against empty strings
        if not reference_text.strip():
            continue

        # Extract raw WAV bytes provided by the parquet structure
        if "bytes" in audio_dict and audio_dict["bytes"] is not None:
            audio_bytes = audio_dict["bytes"]
        else:
            # If path, load from file path manually
            with open(audio_dict["path"], "rb") as f:
                audio_bytes = f.read()

        print(f"Sample {idx+1}/{len(subset)}: '{reference_text[:40]}...'")

        for model_name in models_to_test:
            model_instance = ModelRegistry.get_model(model_name)
            if not model_instance:
                continue
                
            try:
                start_time = time.time()
                hypothesis_text = model_instance.transcribe(audio_bytes)
                latency = time.time() - start_time
                
                # Normalize and calculate Word Error Rate
                ref_norm = reference_text.lower().strip()
                hyp_norm = hypothesis_text.lower().strip()
                
                # Handling empty hypothesis safely
                current_wer = wer(ref_norm, hyp_norm) if hyp_norm else 1.0
                
                results[model_name]["wer"] += current_wer
                results[model_name]["latency"] += latency
                results[model_name]["count"] += 1
            except Exception as e:
                print(f"[{model_name}] Error on sample {idx}: {e}")

    print("\n" + "="*40)
    print("BENCHMARK RESULTS (Acoustic WER + TTFS Latency)")
    print("="*40)
    for model_name, data in results.items():
        if data["count"] > 0:
            avg_wer = data["wer"] / data["count"]
            avg_latency = data["latency"] / data["count"]
            print(f"Model: {model_name.upper()}")
            print(f"  Avg Acoustic WER: {avg_wer:.2%}")
            print(f"  Avg Latency (TTFS): {avg_latency:.3f} sec")
            print(f"  Samples processed: {data['count']}")
            print("-" * 40)

if __name__ == "__main__":
    run_benchmark(num_samples=10) # 10 sample minimum to avoid memory bottlenecking locally
