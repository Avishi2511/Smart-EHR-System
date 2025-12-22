"""
ADNI Alzheimer's Disease Progression Model Service

Wrapper for the ADNI PyTorch model with inference capabilities.
Handles model loading, input preparation, and prediction generation.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)

# Add ADNI code to Python path
ADNI_CODE_PATH = Path(__file__).parent.parent.parent.parent / "adni-python" / "code"
if str(ADNI_CODE_PATH) not in sys.path:
    sys.path.insert(0, str(ADNI_CODE_PATH))

try:
    from run_all_seq_FIXED import ModelFillingLSTM, VIS_ORDER
except ImportError as e:
    logger.error(f"Failed to import ADNI model: {e}")
    logger.error(f"ADNI_CODE_PATH: {ADNI_CODE_PATH}")
    # Don't raise - allow backend to start without ADNI model
    logger.warning("ADNI model will not be available")
    ModelFillingLSTM = None
    VIS_ORDER = None


class ADNIModelService:
    """Service for ADNI Alzheimer's progression prediction"""
    
    def __init__(self):
        self.model_path = Path(__file__).parent.parent.parent.parent / "adni-python" / "outputs" / "best_seq_model_FIXED.pt"
        self.model: Optional[ModelFillingLSTM] = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.d_in = 193  # 93 MRI + 93 PET + 7 demographics
        self.d_latent = 64
        self.d_targets = 4  # MMSE, CDR_GLOBAL, CDR_SOB, ADAS
        self.d_hidden = 128
        
        logger.info(f"ADNI Model Service initialized (device: {self.device})")
    
    def load_model(self) -> None:
        """Load pre-trained PyTorch model"""
        if self.model is not None:
            logger.info("Model already loaded")
            return
        
        try:
            # Create model architecture
            self.model = ModelFillingLSTM(
                d_in=self.d_in,
                d_latent=self.d_latent,
                d_targets=self.d_targets,
                d_hidden=self.d_hidden
            ).to(self.device)
            
            # Load trained weights
            if self.model_path.exists():
                state_dict = torch.load(str(self.model_path), map_location=self.device)
                self.model.load_state_dict(state_dict)
                self.model.eval()
                logger.info(f"Model loaded from {self.model_path}")
            else:
                logger.warning(f"Model file not found: {self.model_path}")
                logger.warning("Model will use random weights (for testing only)")
                self.model.eval()
        
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def prepare_input(
        self, 
        patient_data: Dict[str, Any]
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Convert patient data to model input format
        
        Args:
            patient_data: Dictionary containing:
                - mri_rois: List[float] (93 dims) or None
                - pet_rois: List[float] (93 dims) or None
                - demographics: Dict with age, gender, education, apoe4
                - clinical_scores: Dict with mmse, cdr_global, cdr_sob, adas
                - historical_visits: List[Dict] (optional)
        
        Returns:
            X: Input features (B, T, 193)
            Xmask: Observation mask (B, T, 193)
            Y: Target scores (B, T, 4)
            Ymask: Target mask (B, T, 4)
            seq_mask: Sequence mask (B, T)
        """
        # Extract data
        mri_rois = patient_data.get("mri_rois")
        pet_rois = patient_data.get("pet_rois")
        demographics = patient_data.get("demographics", {})
        clinical_scores = patient_data.get("clinical_scores", {})
        historical_visits = patient_data.get("historical_visits", [])
        
        # Determine sequence length (at least 1 for baseline)
        T = max(1, len(historical_visits))
        
        # Initialize arrays
        X = np.zeros((1, T, self.d_in), dtype=np.float32)
        Xmask = np.zeros((1, T, self.d_in), dtype=np.float32)
        Y = np.zeros((1, T, self.d_targets), dtype=np.float32)
        Ymask = np.zeros((1, T, self.d_targets), dtype=np.float32)
        seq_mask = np.ones((1, T), dtype=np.float32)
        
        # Process each visit
        visits_to_process = historical_visits if historical_visits else [patient_data]
        
        for t, visit_data in enumerate(visits_to_process[:T]):
            # Get visit-specific data or use baseline
            v_mri = visit_data.get("mri_rois", mri_rois)
            v_pet = visit_data.get("pet_rois", pet_rois)
            v_demo = visit_data.get("demographics", demographics)
            v_scores = visit_data.get("clinical_scores", clinical_scores)
            
            # Assemble features
            features = []
            masks = []
            
            # MRI ROIs (93 dims)
            if v_mri is not None and len(v_mri) == 93:
                features.extend(v_mri)
                masks.extend([1.0] * 93)
            else:
                features.extend([0.0] * 93)
                masks.extend([0.0] * 93)  # Mark as missing
            
            # PET ROIs (93 dims)
            if v_pet is not None and len(v_pet) == 93:
                features.extend(v_pet)
                masks.extend([1.0] * 93)
            else:
                features.extend([0.0] * 93)
                masks.extend([0.0] * 93)  # Mark as missing
            
            # Demographics (7 dims)
            demo_features = [
                v_demo.get("age", 0.0),
                v_demo.get("gender", 0.0),
                v_demo.get("education", 15.0),  # Default median
                v_demo.get("apoe4", 0.0),
                v_scores.get("mmse", 0.0),
                v_scores.get("cdr_global", 0.0),
                v_scores.get("adas", 0.0)
            ]
            features.extend(demo_features)
            # Demographics are always "observed" if provided
            demo_mask = [1.0 if v is not None and v != 0.0 else 0.0 for v in demo_features]
            masks.extend(demo_mask)
            
            # Set features and masks
            X[0, t, :] = features
            Xmask[0, t, :] = masks
            
            # Set targets
            targets = [
                v_scores.get("mmse", 0.0),
                v_scores.get("cdr_global", 0.0),
                v_scores.get("cdr_sob", 0.0),
                v_scores.get("adas", 0.0)
            ]
            Y[0, t, :] = targets
            
            # Target masks (1 if observed, 0 if missing)
            target_masks = [
                1.0 if v_scores.get("mmse") is not None else 0.0,
                1.0 if v_scores.get("cdr_global") is not None else 0.0,
                1.0 if v_scores.get("cdr_sob") is not None else 0.0,
                1.0 if v_scores.get("adas") is not None else 0.0
            ]
            Ymask[0, t, :] = target_masks
        
        # Convert to tensors
        X_tensor = torch.from_numpy(X).to(self.device)
        Xmask_tensor = torch.from_numpy(Xmask).to(self.device)
        Y_tensor = torch.from_numpy(Y).to(self.device)
        Ymask_tensor = torch.from_numpy(Ymask).to(self.device)
        seq_mask_tensor = torch.from_numpy(seq_mask).to(self.device)
        
        return X_tensor, Xmask_tensor, Y_tensor, Ymask_tensor, seq_mask_tensor
    
    def run_inference(
        self,
        X: torch.Tensor,
        Xmask: torch.Tensor,
        Y: torch.Tensor,
        Ymask: torch.Tensor,
        seq_mask: torch.Tensor,
        num_future_points: int = 5
    ) -> Dict[str, Any]:
        """
        Run model inference
        
        Args:
            X, Xmask, Y, Ymask, seq_mask: Model inputs
            num_future_points: Number of future timepoints to predict
        
        Returns:
            Dictionary with predictions, timepoints, and confidence scores
        """
        if self.model is None:
            self.load_model()
        
        try:
            with torch.no_grad():
                # Get current predictions
                output = self.model(X, Xmask, Y, Ymask, seq_mask)
                Yhat = output["Yhat"]  # (B, T, 4)
                
                # Extract predictions
                predictions = Yhat[0].cpu().numpy()  # (T, 4)
                
                # Get historical length
                T_hist = X.shape[1]
                
                # Generate future predictions
                # For simplicity, use the last hidden state to predict future
                # In production, you'd want to implement proper sequential prediction
                future_predictions = []
                
                # Use simple linear extrapolation for future points
                if T_hist >= 2:
                    # Calculate trend from last two points
                    last_pred = predictions[-1]
                    second_last_pred = predictions[-2] if T_hist > 1 else predictions[-1]
                    trend = last_pred - second_last_pred
                    
                    for i in range(1, num_future_points + 1):
                        future_pred = last_pred + (trend * i)
                        # Clip to valid ranges
                        future_pred[0] = np.clip(future_pred[0], 0, 30)  # MMSE
                        future_pred[1] = np.clip(future_pred[1], 0, 3)   # CDR_GLOBAL
                        future_pred[2] = np.clip(future_pred[2], 0, 18)  # CDR_SOB
                        future_pred[3] = np.clip(future_pred[3], 0, 70)  # ADAS
                        future_predictions.append(future_pred)
                else:
                    # If only one point, assume stable
                    for i in range(num_future_points):
                        future_predictions.append(predictions[-1].copy())
                
                # Generate timepoint labels
                timepoints = VIS_ORDER[:T_hist]
                future_timepoints = VIS_ORDER[T_hist:T_hist + num_future_points]
                
                # Calculate confidence (simple heuristic based on data availability)
                observed_ratio = Xmask[0].sum().item() / (T_hist * self.d_in)
                confidence = min(0.95, 0.5 + (observed_ratio * 0.45))
                
                return {
                    "historical_predictions": predictions.tolist(),
                    "future_predictions": [fp.tolist() for fp in future_predictions],
                    "historical_timepoints": timepoints,
                    "future_timepoints": future_timepoints,
                    "confidence_score": confidence,
                    "observed_data_ratio": observed_ratio
                }
        
        except Exception as e:
            logger.error(f"Error during inference: {e}")
            raise
    
    def predict_progression(
        self,
        patient_data: Dict[str, Any],
        num_future_points: int = 5
    ) -> Dict[str, Any]:
        """
        High-level method to predict disease progression
        
        Args:
            patient_data: Patient data dictionary
            num_future_points: Number of future visits to predict
        
        Returns:
            Formatted prediction results
        """
        # Prepare input
        X, Xmask, Y, Ymask, seq_mask = self.prepare_input(patient_data)
        
        # Run inference
        results = self.run_inference(X, Xmask, Y, Ymask, seq_mask, num_future_points)
        
        # Format results
        score_names = ["mmse", "cdr_global", "cdr_sob", "adas_totscore"]
        
        formatted_results = {
            "predictions": {
                name: {
                    "historical": [pred[i] for pred in results["historical_predictions"]],
                    "future": [pred[i] for pred in results["future_predictions"]]
                }
                for i, name in enumerate(score_names)
            },
            "timepoints": {
                "historical": results["historical_timepoints"],
                "future": results["future_timepoints"]
            },
            "confidence_score": results["confidence_score"],
            "metadata": {
                "observed_data_ratio": results["observed_data_ratio"],
                "num_historical_visits": len(results["historical_timepoints"]),
                "num_future_predictions": num_future_points
            }
        }
        
        return formatted_results


# Global instance
adni_service = ADNIModelService()
