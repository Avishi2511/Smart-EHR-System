# E:\\adni_python\\code\\run_all_seq_FIXED.py
"""
FIXED VERSION: Multi-modal AD progression prediction with temporal derivatives.

Key fixes:
1. Uses actual 93-dim MRI and PET ROI features (not just binary flags)
2. Implements Equation (9) from paper: s̃_t = z_{t-1} * W_d + s_{t-1}
3. Proper Model Filling strategy with masking and imputation
"""

import os, sys, math, json, random
from pathlib import Path
import numpy as np
import pandas as pd

print("USING FIXED run_all_seq.py FROM:", __file__)

# -------------------- dependencies --------------------
try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
except ImportError as e:
    print("Missing package:", e)
    print("Install with: pip install torch scikit-learn pandas numpy")
    sys.exit(1)

# -------------------- config --------------------
CSV_PATH = Path(r"E:\adni_python\outputs\master_with_roi_features.csv")
OUT_DIR  = CSV_PATH.parent
BEST_MODEL_PATH = OUT_DIR / "best_seq_model_FIXED.pt"
SEED = 42
EPOCHS = 20
BATCH_SIZE = 32
LR = 1e-3
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# -------------------- utils --------------------
def set_seed(seed=42):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)

VIS_ORDER = [
    "sc","bl","m03","m06","m12","m18","m24","m36","m48","m60","m72",
    "m84","m96","m108","m120","m132","m144","m156","m168","m180",
    "m192","m204","m216","m228"
]
APOE_MAP = {"2/2":0, "2/3":1, "3/2":1, "3/3":2, "3/4":3, "4/3":3, "4/4":4, "2/4":5, "4/2":5}
TARGET_NAMES = ["MMSE", "CDR_GLOBAL", "CDR_SOB", "ADAS_TOTSCORE"]

def norm_visit(v):
    if pd.isna(v): return None
    return str(v).strip().lower().replace(" ","")

def apoe_onehot(g):
    idx = APOE_MAP.get(str(g).strip(), None)
    vec = np.zeros(6, dtype=np.float32)
    if idx is not None:
        vec[idx] = 1.0
    return vec

def gender_bin(g):
    if pd.isna(g): return np.nan
    s = str(g).strip().upper()
    if s.startswith("M"): return 1.0
    if s.startswith("F"): return 0.0
    return np.nan

# -------------------- data building --------------------
def assemble_features(df):
    """
    Assemble multi-modal features: MRI ROIs (93) + PET ROIs (93) + Demographics (7)
    Total: 193 dimensions
    """
    print("assemble_features: using MULTI-MODAL version with ROI features")
    feats = []
    
    # MRI ROI features (93 dimensions)
    for i in range(1, 94):
        col = f"mri_roi_{i:03d}"
        x = df.get(col, pd.Series([np.nan]*len(df))).astype(float)
        feats.append(x.values[:,None])
    
    # PET ROI features (93 dimensions)
    for i in range(1, 94):
        col = f"pet_roi_{i:03d}"
        x = df.get(col, pd.Series([np.nan]*len(df))).astype(float)
        feats.append(x.values[:,None])
    
    # Demographics (7 dimensions)
    # Age
    age = df.get("AGE", pd.Series([np.nan]*len(df))).astype(float)
    feats.append(age.values[:,None])
    
    # Gender
    g = df.get("PTGENDER", pd.Series([np.nan]*len(df))).apply(gender_bin)
    feats.append(g.values[:,None])
    
    # Education
    edu = df.get("PTEDUCAT", pd.Series([np.nan]*len(df))).astype(float)
    feats.append(edu.values[:,None])
    
    # APOE one-hot (6 dims) - but we'll use 4 to keep total at 193
    # Actually, let's keep it simple: just use APOE4 count (0, 1, or 2)
    apoe = df.get("APOE4", pd.Series([np.nan]*len(df))).astype(float)
    feats.append(apoe.values[:,None])
    
    # Total: 93 + 93 + 4 = 190, let's add 3 more clinical for 193
    # Add baseline MMSE, CDR, ADAS as static features
    mmse_bl = df.get("MMSE_SCORE", pd.Series([np.nan]*len(df))).astype(float)
    feats.append(mmse_bl.values[:,None])
    
    cdr_bl = df.get("CDR_GLOBAL", pd.Series([np.nan]*len(df))).astype(float)
    feats.append(cdr_bl.values[:,None])
    
    adas_bl = df.get("ADAS_TOTSCORE", pd.Series([np.nan]*len(df))).astype(float)
    feats.append(adas_bl.values[:,None])
    
    # Concatenate all features
    X = np.concatenate(feats, axis=1).astype(np.float32)
    obs_mask = ~np.isnan(X)
    X = np.nan_to_num(X, nan=0.0)
    
    print(f"  Feature dimensions: {X.shape[1]} (93 MRI + 93 PET + 7 demographics)")
    return X, obs_mask.astype(np.float32)

def assemble_targets(df):
    cols = ["MMSE_SCORE","CDR_GLOBAL","CDR_SOB","ADAS_TOTSCORE"]
    Y, M = [], []
    for c in cols:
        v = df.get(c, pd.Series([np.nan]*len(df))).astype(float)
        Y.append(v.values[:,None])
        M.append((~v.isna()).values[:,None])
    Y = np.concatenate(Y, axis=1).astype(np.float32)
    M = np.concatenate(M, axis=1).astype(np.float32)
    Y = np.nan_to_num(Y, nan=0.0)
    return Y, M

def build_sequences(csv_path, min_visits=1):
    df = pd.read_csv(csv_path, low_memory=False)
    df["visit"] = df["visit"].apply(norm_visit)
    df = df[df["visit"].isin(VIS_ORDER)]
    order_map = {v:i for i,v in enumerate(VIS_ORDER)}
    df["visit_idx"] = df["visit"].map(order_map)

    seqs = []
    for pid, g in df.groupby("subject_id"):
        g = g.sort_values("visit_idx")
        X, Xmask = assemble_features(g)
        Y, Ymask = assemble_targets(g)
        if len(g) >= min_visits:
            seqs.append({
                "pid": pid,
                "visits": g["visit"].tolist(),
                "X": X, "Xmask": Xmask,
                "Y": Y, "Ymask": Ymask
            })
    return seqs

def pad_batch(batch):
    T = [b["X"].shape[0] for b in batch]
    Tmax = max(T)
    Din = batch[0]["X"].shape[1]
    Dy  = batch[0]["Y"].shape[1]
    B   = len(batch)
    Xp = np.zeros((B, Tmax, Din), np.float32)
    Xmask = np.zeros((B, Tmax, Din), np.float32)
    Yp = np.zeros((B, Tmax, Dy), np.float32)
    Ymask = np.zeros((B, Tmax, Dy), np.float32)
    seq_mask = np.zeros((B, Tmax), np.float32)
    for i,b in enumerate(batch):
        t = b["X"].shape[0]
        Xp[i,:t,:] = b["X"]
        Xmask[i,:t,:] = b["Xmask"]
        Yp[i,:t,:] = b["Y"]
        Ymask[i,:t,:] = b["Ymask"]
        seq_mask[i,:t] = 1.0
    return Xp, Xmask, Yp, Ymask, seq_mask

# -------------------- model --------------------
class FusionDegradation(nn.Module):
    def __init__(self, d_in, d_latent, out_slices):
        """
        Multi-modality fusion with degradation networks.
        
        Args:
            d_in: Total input dimension (193)
            d_latent: Latent representation dimension (64)
            out_slices: List of output dimensions for each modality [93, 93, 7]
        """
        super().__init__()
        self.enc = nn.Sequential(
            nn.Linear(d_in, 256), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(256, 128), nn.ReLU(),
            nn.Linear(128, d_latent)
        )
        self.decoders = nn.ModuleList([
            nn.Sequential(nn.Linear(d_latent, 128), nn.ReLU(), nn.Linear(128, dm))
            for dm in out_slices
        ])
    
    def forward(self, X):
        H = self.enc(X)
        recons = [dec(H) for dec in self.decoders]
        Xrec = torch.cat(recons, dim=-1)
        return H, Xrec
    
    @staticmethod
    def recon_loss(X, Xmask, Xrec):
        diff = (Xrec - X) * Xmask
        denom = Xmask.sum() + 1e-6
        return diff.pow(2).sum() / denom

class ModelFillingLSTM(nn.Module):
    def __init__(self, d_in, d_latent, d_targets, d_hidden=128, num_layers=1):
        """
        LSTM with Model Filling strategy (Equation 9).
        
        Args:
            d_in: Input dimension (193)
            d_latent: Latent dimension (64)
            d_targets: Number of target scores (4)
            d_hidden: LSTM hidden size (128)
        """
        super().__init__()
        # Multi-modal fusion: MRI (93) + PET (93) + Demographics (7)
        self.fusion = FusionDegradation(d_in, d_latent, [93, 93, 7])
        self.lstm  = nn.LSTM(input_size=d_latent + d_targets, 
                            hidden_size=d_hidden, 
                            num_layers=num_layers, 
                            batch_first=True)
        self.pred_targets = nn.Linear(d_hidden, d_targets)
        
        # ✅ FIX: Dense layer for Model Filling (Equation 9)
        self.dense_layer = nn.Linear(d_hidden, d_latent + d_targets)
    
    def forward(self, X, Xmask, Y, Ymask, seq_mask):
        """
        Forward pass with Model Filling strategy.
        
        Implements Equation (9): s̃_t = z_{t-1} * W_d + s_{t-1}
        And imputation: ŝ_t = δ_t ⊙ s_t + (1 - δ_t) ⊙ s̃_t
        """
        B, T, _ = X.shape
        d_latent = 64  # Fixed latent dimension
        d_targets = Y.shape[-1]
        
        # Get latent representations from fusion module
        Henc, Xrec = self.fusion(X)
        Lrec = self.fusion.recon_loss(X, Xmask, Xrec)
        
        # ✅ FIX: Sequential LSTM processing with Model Filling
        outputs = []
        h_state = None
        s_prev = None
        
        for t in range(T):
            # Current actual input: s_t = [h_t, y_t]
            s_t = torch.cat([Henc[:, t], Y[:, t]], dim=-1)  # (B, d_latent + d_targets)
            
            # ✅ FIX: Mask only for latent+target space, not full input space
            # Create mask for latent (assume all latent dims are observed after fusion)
            # and use Ymask for target dims
            latent_mask = torch.ones(B, d_latent, device=s_t.device)
            mask_t = torch.cat([latent_mask, Ymask[:, t]], dim=-1)  # (B, d_latent + d_targets)
            
            if t == 0:
                # First timestep: use actual data
                s_hat = s_t
            else:
                # ✅ Equation (9): s̃_t = z_{t-1} * W_d + s_{t-1}
                z_prev = h_state[0][-1]  # Hidden state from previous timestep
                s_tilde = self.dense_layer(z_prev) + s_prev  # ← THE KEY FIX!
                
                # Imputation: ŝ_t = δ_t ⊙ s_t + (1 - δ_t) ⊙ s̃_t
                s_hat = mask_t * s_t + (1 - mask_t) * s_tilde
            
            # Feed into LSTM
            lstm_in = s_hat.unsqueeze(1)  # (B, 1, d_latent + d_targets)
            lstm_out, h_state = self.lstm(lstm_in, h_state)
            
            outputs.append(lstm_out.squeeze(1))
            s_prev = s_hat  # Save for next timestep's derivative
        
        # Stack outputs
        lstm_out_seq = torch.stack(outputs, dim=1)  # (B, T, d_hidden)
        
        # Predict targets
        Yhat = self.pred_targets(lstm_out_seq)
        
        # Target prediction loss
        Ltar = (torch.abs(Yhat - Y) * Ymask).sum() / (Ymask.sum() + 1e-6)
        
        return {"loss": Lrec + Ltar, "Lrec": Lrec, "Ltar": Ltar, "Yhat": Yhat}

# -------------------- training & eval --------------------
def collate(batch):
    X, Xmask, Y, Ymask, S = pad_batch(batch)
    to_t = lambda a: torch.from_numpy(a)
    return to_t(X), to_t(Xmask), to_t(Y), to_t(Ymask), to_t(S)

def train_and_eval():
    set_seed(SEED)
    print("CSV:", CSV_PATH)
    if not CSV_PATH.exists():
        print("CSV not found. Expected:", CSV_PATH)
        print("Please run 05_extract_roi_features.py and 06_merge_roi_features.py first.")
        sys.exit(1)

    print("Loading sequences from:", CSV_PATH)
    seqs = build_sequences(CSV_PATH, min_visits=1)
    if len(seqs) == 0:
        print("No sequences built. Check CSV content.")
        return

    pids = [s["pid"] for s in seqs]
    train_ids, val_ids = train_test_split(pids, test_size=0.2, random_state=SEED)
    train = [s for s in seqs if s["pid"] in train_ids]
    val   = [s for s in seqs if s["pid"] in val_ids]

    Din = train[0]["X"].shape[1]
    Dy  = train[0]["Y"].shape[1]
    print(f"Dims -> Din={Din}, Dy={Dy}, train_n={len(train)}, val_n={len(val)}")

    model = ModelFillingLSTM(d_in=Din, d_latent=64, d_targets=Dy, d_hidden=128).to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=LR)

    dl_train = DataLoader(train, batch_size=BATCH_SIZE, shuffle=True,  collate_fn=collate)
    dl_val   = DataLoader(val,   batch_size=BATCH_SIZE, shuffle=False, collate_fn=collate)

    best_val = float("inf")
    for ep in range(1, EPOCHS+1):
        model.train(); tr_loss=tr_rec=tr_tar=0.0; ntr=0
        for X,Xm,Y,Ym,S in dl_train:
            X=X.to(DEVICE); Xm=Xm.to(DEVICE); Y=Y.to(DEVICE); Ym=Ym.to(DEVICE); S=S.to(DEVICE)
            out = model(X,Xm,Y,Ym,S); loss=out["loss"]
            opt.zero_grad(); loss.backward(); opt.step()
            bs=X.size(0); tr_loss+=loss.item()*bs; tr_rec+=out["Lrec"].item()*bs; tr_tar+=out["Ltar"].item()*bs; ntr+=bs
        tr_loss/=max(ntr,1); tr_rec/=max(ntr,1); tr_tar/=max(ntr,1)

        model.eval(); vl_loss=vl_rec=vl_tar=0.0; nvl=0
        with torch.no_grad():
            for X,Xm,Y,Ym,S in dl_val:
                X=X.to(DEVICE); Xm=Xm.to(DEVICE); Y=Y.to(DEVICE); Ym=Ym.to(DEVICE); S=S.to(DEVICE)
                out = model(X,Xm,Y,Ym,S)
                bs=X.size(0); vl_loss+=out["loss"].item()*bs; vl_rec+=out["Lrec"].item()*bs; vl_tar+=out["Ltar"].item()*bs; nvl+=bs
        vl_loss/=max(nvl,1); vl_rec/=max(nvl,1); vl_tar/=max(nvl,1)
        print(f"Epoch {ep:03d} | train {tr_loss:.4f} (rec {tr_rec:.4f}, tar {tr_tar:.4f}) | val {vl_loss:.4f} (rec {vl_rec:.4f}, tar {vl_tar:.4f})")

        if vl_loss < best_val:
            best_val = vl_loss
            torch.save(model.state_dict(), str(BEST_MODEL_PATH))
            print("  saved best:", BEST_MODEL_PATH)

    # Evaluation on validation (observed entries only)
    model.eval()
    y_true = [[] for _ in range(Dy)]
    y_pred = [[] for _ in range(Dy)]
    with torch.no_grad():
        for X,Xm,Y,Ym,S in dl_val:
            X=X.to(DEVICE); Xm=Xm.to(DEVICE); Y=Y.to(DEVICE); Ym=Ym.to(DEVICE)
            out = model(X,Xm,Y,Ym,S.to(DEVICE))
            Yhat = out["Yhat"].cpu().numpy()
            Ynp = Y.cpu().numpy()
            Mnp = Ym.cpu().numpy()
            B,T,_ = Ynp.shape
            for d in range(Dy):
                mask = Mnp[:,:,d] > 0.5
                y_true[d].extend(list(Ynp[:,:,d][mask]))
                y_pred[d].extend(list(Yhat[:,:,d][mask]))

    print("\nValidation metrics (current-visit prediction):")
    for d, name in enumerate(TARGET_NAMES[:Dy]):
        yt = np.array(y_true[d]); yp = np.array(y_pred[d])
        if yt.size == 0:
            print(f"- {name}: no observed targets")
            continue
        mae = mean_absolute_error(yt, yp)
        mse = mean_squared_error(yt, yp)
        rmse = math.sqrt(mse)
        try:
            r2 = r2_score(yt, yp)
        except Exception:
            r2 = float("nan")
        print(f"- {name}: MAE={mae:.3f}, RMSE={rmse:.3f}, R2={r2:.3f} ({r2*100:.1f}%)")

# -------------------- run --------------------
if __name__ == "__main__":
    if not CSV_PATH.exists():
        print("CSV not found. Expected:", CSV_PATH)
        print("\nPlease run the following scripts first:")
        print("1. python code/05_extract_roi_features.py")
        print("2. python code/06_merge_roi_features.py")
        sys.exit(1)
    train_and_eval()
