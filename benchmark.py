import os
import sys
import time
import requests
import io
import csv
import numpy as np
import soundfile as sf
import librosa
from datasets import load_dataset, Audio
from jiwer import wer

# --- CONFIGURATION ---
API_URL = "http://localhost:8000/api/transcribe"
DEFAULT_MODELS = ["whisper", "canary", "parakeet"]
HF_TOKEN = os.getenv("HF_TOKEN")
LOCAL_DATA_ROOT = "CommonVoice_Datasets" 

def print_progress_bar(iteration, total, prefix='', suffix='', length=40, fill='█'):
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()
    if iteration == total: print()

def load_local_samples(lang_code, num_samples, dataset_type="standard"):
    lang_path = os.path.join(LOCAL_DATA_ROOT, lang_code)
    if dataset_type == "spontaneous":
        tsv_path = os.path.join(lang_path, f"ss-corpus-{lang_code}.tsv")
        audios_dir = os.path.join(lang_path, "audios")
        text_col = "transcription"
    else:
        tsv_path = os.path.join(lang_path, "test.tsv")
        audios_dir = os.path.join(lang_path, "clips")
        text_col = "sentence"
    
    if not os.path.exists(tsv_path): return None

    samples = []
    try:
        with open(tsv_path, "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f, delimiter="\t"))
            limit = min(num_samples, len(reader))
            for row in reader:
                if len(samples) >= limit: break
                text = row.get(text_col, "").strip()
                if not text: continue
                audio_file = row.get("path") or row.get("audio_file")
                if not audio_file: continue
                audio_path = os.path.join(audios_dir, audio_file)
                if os.path.exists(audio_path):
                    samples.append({"path": audio_path, "text": text, "lang": lang_code})
    except Exception as e: print(f"Error reading TSV: {e}")
    return samples

def run_multilingual_benchmark(num_samples=150):
    datasets_to_run = [
        {"id": "pipecat-ai/stt-benchmark-data", "lang": "en", "type": "hf", "col": "transcription", "label": "Pipecat English"},
        {"id": "es", "lang": "es", "type": "local", "sub_type": "spontaneous", "label": "CV Spontaneous Spanish"},
        {"id": "pl", "lang": "pl", "type": "local", "sub_type": "standard", "label": "CV Polish"},
    ]

    all_summary_data = []
    case_analysis = []
    csv_summary_out = "stt_advanced_benchmark_summary.csv"
    csv_cases_out = "stt_model_best_worst_cases.csv"

    for d_cfg in datasets_to_run:
        print(f"\nPROCESSING: {d_cfg['label']}")
        subset = []
        try:
            if d_cfg["type"] == "hf":
                ds = load_dataset(d_cfg["id"], split="train", streaming=True, token=HF_TOKEN)
                ds = ds.cast_column("audio", Audio(decode=False))
                for item in ds.take(num_samples):
                    subset.append({"bytes": item["audio"].get("bytes"), "text": item[d_cfg["col"]], "lang": d_cfg["lang"]})
            else:
                local_samples = load_local_samples(d_cfg["lang"], num_samples, d_cfg.get("sub_type", "standard"))
                if local_samples: subset.extend(local_samples)
        except Exception as e: print(f"Error loading {d_cfg['label']}: {e}"); continue

        if not subset: continue

        results = {m: {
            "wers": [], "refs": [], "hyps": [], "perfect_count": 0,
            "total_audio_duration": 0.0, "total_inference_time": 0.0,
            "samples": [] # Store for best/worst sorting
        } for m in DEFAULT_MODELS}
        
        for idx, row in enumerate(subset):
            print_progress_bar(idx + 1, len(subset), prefix=f'Benchmarking {d_cfg["lang"].upper()}:', suffix='Done', length=30)
            ref_text = row["text"].lower().strip()
            
            try:
                if row.get("bytes"):
                    audio_array, sr = librosa.load(io.BytesIO(row["bytes"]), sr=16000)
                else:
                    audio_array, sr = librosa.load(row["path"], sr=16000)
                
                audio_duration = len(audio_array) / sr
                buffer = io.BytesIO()
                sf.write(buffer, audio_array, sr, format='WAV')
                audio_bytes = buffer.getvalue()
            except Exception: continue

            for model_name in DEFAULT_MODELS:
                try:
                    start_time = time.time()
                    payload = {"model_name": model_name, "language": row["lang"]}
                    resp = requests.post(API_URL, files={"file": ("audio.wav", audio_bytes)}, data=payload, timeout=90)
                    inference_time = time.time() - start_time
                    
                    if resp.status_code == 200:
                        hyp = resp.json().get("transcription", "").lower().strip()
                        current_wer = wer(ref_text, hyp) if hyp else 1.0
                        
                        results[model_name]["wers"].append(current_wer)
                        results[model_name]["refs"].append(ref_text)
                        results[model_name]["hyps"].append(hyp)
                        results[model_name]["total_audio_duration"] += audio_duration
                        results[model_name]["total_inference_time"] += inference_time
                        
                        if current_wer == 0.0: results[model_name]["perfect_count"] += 1
                        
                        # Store sample for sorting
                        results[model_name]["samples"].append({
                            "wer": current_wer,
                            "ref": ref_text,
                            "hyp": hyp,
                            "lang": row["lang"]
                        })
                except Exception: pass

        for model_name, m_data in results.items():
            count = len(m_data["wers"])
            if count == 0: continue

            # Summary metrics
            mean_wer = np.mean(m_data["wers"])
            pooled_wer = wer(m_data["refs"], m_data["hyps"])
            total_audio = m_data["total_audio_duration"]
            total_inf = m_data["total_inference_time"]
            rtf = total_inf / total_audio if total_audio > 0 else 0
            perfect_pct = (m_data["perfect_count"] / count) * 100

            all_summary_data.append({
                "Dataset": d_cfg['label'], "Model": model_name, 
                "Mean_WER": round(float(mean_wer), 4), "Pooled_WER": round(float(pooled_wer), 4),
                "Perfect_Pct": round(float(perfect_pct), 2), "Total_Audio_Sec": round(total_audio, 2),
                "Total_Inference_Sec": round(total_inf, 2), "RTF": round(rtf, 3), "Sample_Count": count
            })

            # Case Analysis sorting
            all_samples = m_data["samples"]
            # 5 Worst Cases (Highest WER)
            worst = sorted(all_samples, key=lambda x: x["wer"], reverse=True)[:5]
            for w in worst:
                case_analysis.append({"Model": model_name, "Dataset": d_cfg['label'], "Type": "Worst", **w})
            
            # 5 Best (Lowest WER > 0)
            non_perfect = [s for s in all_samples if s["wer"] > 0]
            if non_perfect:
                best_non_perf = sorted(non_perfect, key=lambda x: x["wer"])[:5]
                for b in best_non_perf:
                    case_analysis.append({"Model": model_name, "Dataset": d_cfg['label'], "Type": "Best (Non-Perfect)", **b})

    # Save outputs
    if all_summary_data:
        keys = all_summary_data[0].keys()
        with open(csv_summary_out, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys); writer.writeheader(); writer.writerows(all_summary_data)
    
    if case_analysis:
        keys = case_analysis[0].keys()
        with open(csv_cases_out, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys); writer.writeheader(); writer.writerows(case_analysis)

    print(f"\nReports saved: {csv_summary_out}, {csv_cases_out}")

if __name__ == "__main__":
    run_multilingual_benchmark(num_samples=1000)