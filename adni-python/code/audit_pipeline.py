# E:\adni_python\code\audit_pipeline.py
import sys
from pathlib import Path
import pandas as pd

# ---------- Config ----------
BASE = Path(r"E:\adni_python")
MASTER = BASE / "outputs" / "master_with_imaging_match.csv"
DERIV = BASE / "outputs" / "derivatives"
OUT_AUDIT = BASE / "outputs" / "audit_imaging_pipeline.csv"
OUT_SUMMARY = BASE / "outputs" / "audit_imaging_pipeline_summary.csv"

# If your derivative filenames differ, change here:
DERIV_T1_NAME = "t1_brain.nii.gz"
DERIV_PET_NAME = "pet_in_t1.nii.gz"
DERIV_SUVR_NAME = "pet_suvr_in_t1.nii.gz"

# ---------- Helpers ----------
def exists_file(p):
    try:
        return Path(p).exists()
    except Exception:
        return False

def nonempty_str(x):
    if pd.isna(x):
        return ""
    s = str(x).strip()
    return s

def check_match_present(row):
    # Treat presence of token and date as a successful match
    tok = nonempty_str(row.get("matched_session_token", ""))
    dt = nonempty_str(row.get("matched_session_date", ""))
    return (tok != "") and (dt != "")

def derivative_flags(subject_id, session_token):
    sub_dir = DERIV / f"sub-{subject_id}" / f"ses-{session_token}"
    t1 = sub_dir / DERIV_T1_NAME
    pet = sub_dir / DERIV_PET_NAME
    suvr = sub_dir / DERIV_SUVR_NAME
    return exists_file(t1), exists_file(pet), exists_file(suvr)

# ---------- Main audit ----------
def audit():
    if not MASTER.exists():
        print(f"Master CSV not found: {MASTER}")
        sys.exit(1)

    df = pd.read_csv(MASTER, low_memory=False)

    # Warn if critical columns are missing (but proceed with defaults)
    needed_cols = [
        "subject_id", "matched_session_token", "matched_session_date",
        "has_pet_match", "has_t1_match", "pet_path", "anat_path"
    ]
    missing = [c for c in needed_cols if c not in df.columns]
    if missing:
        print("Warning: missing columns in master:", ", ".join(missing))

    rows = []
    for _, r in df.iterrows():
        pid = nonempty_str(r.get("subject_id", ""))
        ses = nonempty_str(r.get("matched_session_token", ""))
        matched_ok = check_match_present(r)

        has_pet = bool(r.get("has_pet_match", 0))
        has_t1 = bool(r.get("has_t1_match", 0))
        pet_path = nonempty_str(r.get("pet_path", ""))
        anat_path = nonempty_str(r.get("anat_path", ""))

        if matched_ok and pid and ses:
            d_t1, d_pet, d_suvr = derivative_flags(pid, ses)
        else:
            d_t1 = d_pet = d_suvr = False

        # Decide final_status and failure_reason
        if not matched_ok:
            final_status = "skipped"
            failure_reason = "no_session_within_window"
        elif not has_pet:
            final_status = "skipped"
            failure_reason = "no_pet_for_session"
        elif not has_t1:
            final_status = "skipped"
            failure_reason = "no_t1_for_session"
        elif pet_path and not exists_file(pet_path):
            final_status = "skipped"
            failure_reason = "pet_path_missing_on_disk"
        elif anat_path and not exists_file(anat_path):
            final_status = "skipped"
            failure_reason = "t1_path_missing_on_disk"
        elif not d_t1 and not d_pet and not d_suvr:
            final_status = "skipped"
            failure_reason = "no_derivatives_written"
        elif d_t1 and not d_pet and not d_suvr:
            final_status = "skipped"
            failure_reason = "t1_only_derivative"
        elif d_t1 and d_pet and not d_suvr:
            final_status = "skipped"
            failure_reason = "suvr_missing"
        else:
            final_status = "ok"
            failure_reason = ""

        rows.append({
            "subject_id": pid,
            "matched_session_token": ses,
            "matched_window_ok": int(matched_ok),
            "has_pet_match": int(has_pet),
            "has_t1_match": int(has_t1),
            "pet_path": pet_path,
            "anat_path": anat_path,
            "pet_path_exists": int(exists_file(pet_path)) if pet_path else 0,
            "t1_path_exists": int(exists_file(anat_path)) if anat_path else 0,
            "deriv_t1_ok": int(d_t1),
            "deriv_pet_ok": int(d_pet),
            "deriv_suvr_ok": int(d_suvr),
            "final_status": final_status,
            "failure_reason": failure_reason
        })

    audit_df = pd.DataFrame(rows)
    audit_df.to_csv(OUT_AUDIT, index=False)

    # Build robust summary
    total = len(audit_df)
    ok = int((audit_df["final_status"] == "ok").sum())
    dropped = total - ok

    if "failure_reason" in audit_df.columns:
        fail_df = audit_df[audit_df["final_status"] != "ok"]
        if not fail_df.empty:
            vc = fail_df["failure_reason"].value_counts(dropna=False)
            by_reason = vc.reset_index()
            # Normalize column names across pandas versions
            if by_reason.shape[1] == 2:
                by_reason.columns = ["failure_reason", "count"]
        else:
            by_reason = pd.DataFrame(columns=["failure_reason", "count"])
    else:
        by_reason = pd.DataFrame(columns=["failure_reason", "count"])

    by_reason.to_csv(OUT_SUMMARY, index=False)

    # Print summary (won't crash if empty)
    print("\n=== Audit Summary ===")
    print(f"Total rows: {total}")
    print(f"OK derivatives: {ok}")
    print(f"Dropped: {dropped}")

    print("\nTop failure reasons:")
    if by_reason.empty:
        print("- none (no failures recorded or no failure_reason values)")
    else:
        for _, row in by_reason.iterrows():
            print(f"- {row['failure_reason']}: {row['count']}")

    print("\nSaved:")
    print("-", OUT_AUDIT)
    print("-", OUT_SUMMARY)

    # Optional: show a small peek for sanity
    print("\nSample audit rows:")
    print(audit_df.head(5)[[
        "subject_id","matched_session_token","matched_window_ok",
        "has_pet_match","has_t1_match",
        "pet_path_exists","t1_path_exists",
        "deriv_t1_ok","deriv_pet_ok","deriv_suvr_ok",
        "final_status","failure_reason"
    ]])

if __name__ == "__main__":
    audit()
