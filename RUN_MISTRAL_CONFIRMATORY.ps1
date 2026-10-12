$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== Dream confirmatory / Mistral ==="
Set-Location "$ROOT\experiments\v0_7_1_dream_confirmatory"
python clean_results.py
python run_synthetic.py `
  --backend ollama `
  --model mistral:instruct `
  --scenarios all `
  --seeds 2 `
  --methods no_memory,fact_rag,replay_only,dream_recombine,oracle_relevant,full_history `
  --temperature 0.1 `
  --top-k 2 `
  --distractors 100 `
  --num-ctx 8192 `
  --fresh
python analyze_dream.py

Write-Host "=== Curiosity confirmatory / Mistral ==="
Set-Location "$ROOT\experiments\v0_7_2_curiosity_confirmatory"
python clean_results.py
python run_curiosity.py `
  --backend ollama `
  --model mistral:instruct `
  --scenarios all `
  --seeds 2 `
  --temperature 0.1 `
  --top-k 2 `
  --distractors 40 `
  --curiosity-budget 3 `
  --min-gap-confidence 0.50 `
  --num-ctx 8192 `
  --fresh
python analyze_curiosity.py
