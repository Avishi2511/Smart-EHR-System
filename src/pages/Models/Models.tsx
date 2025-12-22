import { useState, useContext } from "react";
import { Brain, TrendingDown, Calendar, Activity } from "lucide-react";
import AlzheimerPredictionLoading from "@/components/AlzheimerPredictionLoading";
import AlzheimerTimeline from "@/components/AlzheimerTimeline";
import { PatientContext } from "@/contexts/PatientContext";
import { getAdniPatientId } from "@/config/patientIdMapping";
import axios from "axios";

interface PredictionPoint {
    months_from_last_visit: number;
    predicted_scores: {
        MMSE: number;
        CDR_Global: number;
        CDR_SOB: number;
        ADAS_Cog: number;
    };
}

interface PredictionResponse {
    patient_id: string;
    prediction_time: string;
    last_visit: {
        date: string;
        scores: {
            MMSE: number;
            CDR_Global: number;
            CDR_SOB: number;
            ADAS_Cog: number;
        };
    };
    future_predictions: PredictionPoint[];
}

function Models() {
    const { selectedPatient } = useContext(PatientContext);
    const [isLoading, setIsLoading] = useState(false);
    const [predictions, setPredictions] = useState<PredictionResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleRunModel = async () => {
        if (!selectedPatient?.id) {
            setError("No patient selected");
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            // Map patient ID to ADNI ID
            const adniPatientId = getAdniPatientId(selectedPatient.id);

            console.log(`Running ADNI model for patient: ${selectedPatient.id} (ADNI ID: ${adniPatientId})`);

            // Call the ADNI pipeline
            const response = await axios.post(
                "/api/alzheimers/run-prediction",
                { patient_id: adniPatientId },
                { timeout: 120000 } // 2 minute timeout
            );

            // Simulate minimum loading time for smooth UX
            await new Promise((resolve) => setTimeout(resolve, 15000)); // 15 seconds minimum

            setPredictions(response.data);
        } catch (err: any) {
            console.error("Error running prediction:", err);
            setError(err.response?.data?.detail || "Failed to run prediction model");
        } finally {
            setIsLoading(false);
        }
    };

    // Show loading screen
    if (isLoading) {
        return <AlzheimerPredictionLoading />;
    }

    // Show timeline if predictions exist
    if (predictions) {
        return (
            <div>
                <AlzheimerTimeline
                    predictions={predictions.future_predictions}
                />
                <div className="fixed bottom-8 right-8">
                    <button
                        onClick={() => setPredictions(null)}
                        className="px-6 py-3 bg-white text-slate-700 font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 border border-slate-200"
                    >
                        Back to Models
                    </button>
                </div>
            </div>
        );
    }

    // Show models page
    return (
        <div className="min-h-screen bg-muted/40 p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-12">
                    <h1 className="text-4xl font-bold text-foreground mb-3">
                        Predictive Models
                    </h1>
                    <p className="text-muted-foreground text-lg">
                        Advanced AI-powered disease progression models for personalized patient care
                    </p>
                </div>

                {/* Error Message */}
                {error && (
                    <div className="mb-6 bg-red-50 border border-red-200 rounded-xl p-4">
                        <p className="text-red-700 font-medium">{error}</p>
                    </div>
                )}

                {/* Models Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {/* Alzheimer's Progression Model Card */}
                    <div className="group relative bg-card rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden border border-border hover:border-primary">
                        {/* Gradient Background Accent */}
                        <div className="absolute top-0 left-0 w-full h-2 bg-primary"></div>

                        {/* Card Content */}
                        <div className="p-8">
                            {/* Icon */}
                            <div className="mb-6 relative">
                                <div className="w-20 h-20 bg-primary/10 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                                    <Brain className="w-10 h-10 text-primary" />
                                </div>
                                <div className="absolute -top-2 -right-2 w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                                    <Activity className="w-4 h-4 text-white" />
                                </div>
                            </div>

                            {/* Title */}
                            <h3 className="text-2xl font-bold text-foreground mb-3">
                                Alzheimer's Progression Model
                            </h3>

                            {/* Description */}
                            <p className="text-muted-foreground mb-6 leading-relaxed">
                                Predict cognitive decline using multi-modal LSTM neural networks
                            </p>

                            {/* Key Features */}
                            <div className="space-y-3 mb-8">
                                <div className="flex items-start gap-3">
                                    <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                                        <Brain className="w-3.5 h-3.5 text-primary" />
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium text-foreground">Multi-modal Analysis</p>
                                        <p className="text-xs text-muted-foreground">MRI + PET + Clinical Data</p>
                                    </div>
                                </div>

                                <div className="flex items-start gap-3">
                                    <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                                        <TrendingDown className="w-3.5 h-3.5 text-primary" />
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium text-foreground">Progression Tracking</p>
                                        <p className="text-xs text-muted-foreground">MMSE, CDR, ADAS-Cog scores</p>
                                    </div>
                                </div>

                                <div className="flex items-start gap-3">
                                    <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                                        <Calendar className="w-3.5 h-3.5 text-primary" />
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium text-foreground">Future Predictions</p>
                                        <p className="text-xs text-muted-foreground">Up to 90 months ahead</p>
                                    </div>
                                </div>
                            </div>

                            {/* Action Button */}
                            <button
                                onClick={handleRunModel}
                                disabled={!selectedPatient}
                                className="w-full py-4 px-6 bg-primary text-primary-foreground font-semibold rounded-xl hover:bg-primary/90 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <span className="flex items-center justify-center gap-2">
                                    <Brain className="w-5 h-5" />
                                    Run Model
                                </span>
                            </button>

                            {!selectedPatient && (
                                <p className="mt-2 text-xs text-center text-muted-foreground">
                                    Please select a patient first
                                </p>
                            )}

                            {/* Model Stats */}
                            <div className="mt-6 pt-6 border-t border-border grid grid-cols-3 gap-4">
                                <div className="text-center">
                                    <p className="text-2xl font-bold text-primary">93%</p>
                                    <p className="text-xs text-muted-foreground">Accuracy</p>
                                </div>
                                <div className="text-center">
                                    <p className="text-2xl font-bold text-primary">193</p>
                                    <p className="text-xs text-muted-foreground">Features</p>
                                </div>
                                <div className="text-center">
                                    <p className="text-2xl font-bold text-primary">4</p>
                                    <p className="text-xs text-muted-foreground">Scores</p>
                                </div>
                            </div>
                        </div>

                        {/* Hover Effect Overlay */}
                        <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
                    </div>

                    {/* Placeholder for future models */}
                    <div className="bg-card/50 rounded-2xl border-2 border-dashed border-border p-8 flex flex-col items-center justify-center min-h-[500px] hover:border-muted-foreground transition-colors">
                        <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
                            <Activity className="w-8 h-8 text-muted-foreground" />
                        </div>
                        <h3 className="text-lg font-semibold text-muted-foreground mb-2">More Models Coming Soon</h3>
                        <p className="text-sm text-muted-foreground text-center">
                            Additional predictive models will be added here
                        </p>
                    </div>
                </div>

                {/* Info Section */}
                <div className="mt-12 bg-card rounded-2xl shadow-lg p-8 border border-border">
                    <h2 className="text-2xl font-bold text-foreground mb-4">About Predictive Models</h2>
                    <div className="grid md:grid-cols-2 gap-6 text-muted-foreground">
                        <div>
                            <h3 className="font-semibold text-foreground mb-2">How It Works</h3>
                            <p className="text-sm leading-relaxed">
                                Our AI models analyze patient data including medical imaging, clinical assessments,
                                and demographic information to predict disease progression with high accuracy.
                            </p>
                        </div>
                        <div>
                            <h3 className="font-semibold text-foreground mb-2">Clinical Applications</h3>
                            <p className="text-sm leading-relaxed">
                                These predictions help clinicians make informed decisions about treatment plans,
                                monitor disease progression, and provide personalized care strategies.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Models;
