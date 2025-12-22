# E:\adni_python\code\evaluate_model.py
"""
Evaluate the trained model and get metrics for all 4 Alzheimer's scores.
"""

import sys, math
from pathlib import Path
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Import the model architecture
sys.path.insert(0, str(Path(__file__).parent))
from run_all_seq_FIXED import (
    ModelFillingLSTM, build_sequences, collate, 
    set_seed, SEED, DEVICE, TARGET_NAMES
)

CSV_PATH = Path(r"E:\adni_python\outputs\master_with_roi_features.csv")
MODEL_PATH = Path(r"E:\adni_python\outputs\best_seq_model_FIXED.pt")

def evaluate_model():
    set_seed(SEED)
    
    print("=" * 80)
    print("Model Evaluation - All 4 Alzheimer's Scores")
    print("=" * 80)
    
    # Load data
    print(f"\nLoading data from: {CSV_PATH}")
    seqs = build_sequences(CSV_PATH, min_visits=1)
    
    if len(seqs) == 0:
        print("No sequences found!")
        return
    
    print(f"Total sequences: {len(seqs)}")
    
    # Use all data for evaluation (or split if you want)
    from sklearn.model_selection import train_test_split
    pids = [s["pid"] for s in seqs]
    train_ids, val_ids = train_test_split(pids, test_size=0.2, random_state=SEED)
    val = [s for s in seqs if s["pid"] in val_ids]
    
    print(f"Validation sequences: {len(val)}")
    
    # Get dimensions
    Din = val[0]["X"].shape[1]
    Dy = val[0]["Y"].shape[1]
    
    print(f"Input dims: {Din}, Target dims: {Dy}")
    
    # Load model
    print(f"\nLoading model from: {MODEL_PATH}")
    model = ModelFillingLSTM(d_in=Din, d_latent=64, d_targets=Dy, d_hidden=128).to(DEVICE)
    model.load_state_dict(torch.load(str(MODEL_PATH), map_location=DEVICE))
    model.eval()
    
    print("Model loaded successfully!")
    
    # Prepare data loader
    from torch.utils.data import DataLoader
    dl_val = DataLoader(val, batch_size=32, shuffle=False, collate_fn=collate)
    
    # Collect predictions
    y_true = [[] for _ in range(Dy)]
    y_pred = [[] for _ in range(Dy)]
    
    print("\nRunning inference...")
    with torch.no_grad():
        for X, Xm, Y, Ym, S in dl_val:
            X = X.to(DEVICE)
            Xm = Xm.to(DEVICE)
            Y = Y.to(DEVICE)
            Ym = Ym.to(DEVICE)
            S = S.to(DEVICE)
            
            out = model(X, Xm, Y, Ym, S)
            Yhat = out["Yhat"].cpu().numpy()
            Ynp = Y.cpu().numpy()
            Mnp = Ym.cpu().numpy()
            
            B, T, _ = Ynp.shape
            for d in range(Dy):
                mask = Mnp[:, :, d] > 0.5
                y_true[d].extend(list(Ynp[:, :, d][mask]))
                y_pred[d].extend(list(Yhat[:, :, d][mask]))
    
    # Calculate metrics
    print("\n" + "=" * 80)
    print("VALIDATION METRICS FOR ALL 4 ALZHEIMER'S SCORES")
    print("=" * 80)
    
    results = []
    for d, name in enumerate(TARGET_NAMES[:Dy]):
        yt = np.array(y_true[d])
        yp = np.array(y_pred[d])
        
        if yt.size == 0:
            print(f"\n{name}:")
            print(f"  ⚠️  No observed targets in validation set")
            results.append({
                'Score': name,
                'N': 0,
                'MAE': None,
                'RMSE': None,
                'R2': None,
                'R2_pct': None
            })
            continue
        
        mae = mean_absolute_error(yt, yp)
        mse = mean_squared_error(yt, yp)
        rmse = math.sqrt(mse)
        
        try:
            r2 = r2_score(yt, yp)
        except Exception:
            r2 = float("nan")
        
        print(f"\n{name}:")
        print(f"  Samples: {len(yt)}")
        print(f"  MAE:     {mae:.4f}")
        print(f"  RMSE:    {rmse:.4f}")
        print(f"  R²:      {r2:.4f} ({r2*100:.2f}%)")
        
        results.append({
            'Score': name,
            'N': len(yt),
            'MAE': mae,
            'RMSE': rmse,
            'R2': r2,
            'R2_pct': r2 * 100
        })
    
    # Summary table
    print("\n" + "=" * 80)
    print("SUMMARY TABLE")
    print("=" * 80)
    
    df_results = pd.DataFrame(results)
    print(df_results.to_string(index=False))
    
    # Save results
    results_csv = MODEL_PATH.parent / "evaluation_results.csv"
    df_results.to_csv(results_csv, index=False)
    print(f"\n✓ Results saved to: {results_csv}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    evaluate_model()
