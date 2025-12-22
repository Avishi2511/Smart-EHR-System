import { Brain } from "lucide-react";
import "./AlzheimerPredictionLoading.css";

interface AlzheimerPredictionLoadingProps {
    stage?: string;
}

function AlzheimerPredictionLoading({ stage = "Initializing" }: AlzheimerPredictionLoadingProps) {
    return (
        <div className="fixed inset-0 bg-background flex items-center justify-center z-50">
            {/* Animated Background Particles */}
            <div className="absolute inset-0 overflow-hidden">
                <div className="neural-network">
                    {[...Array(20)].map((_, i) => (
                        <div
                            key={i}
                            className="neural-node"
                            style={{
                                left: `${Math.random() * 100}%`,
                                top: `${Math.random() * 100}%`,
                                animationDelay: `${Math.random() * 3}s`,
                                animationDuration: `${3 + Math.random() * 2}s`,
                            }}
                        />
                    ))}
                </div>
            </div>

            {/* Main Content */}
            <div className="relative z-10 text-center">
                {/* Animated Brain Icon */}
                <div className="mb-8 relative">
                    <div className="brain-pulse-container">
                        <div className="brain-pulse-ring brain-pulse-ring-1"></div>
                        <div className="brain-pulse-ring brain-pulse-ring-2"></div>
                        <div className="brain-pulse-ring brain-pulse-ring-3"></div>
                        <div className="brain-icon-wrapper">
                            <Brain className="w-20 h-20 text-white" />
                        </div>
                    </div>
                </div>

                {/* Title */}
                <h2 className="text-3xl font-bold text-foreground mb-4">
                    Analyzing Disease Progression
                </h2>

                {/* Stage Indicator */}
                <p className="text-muted-foreground text-lg mb-8">{stage}</p>

                {/* Progress Bar */}
                <div className="max-w-md mx-auto mb-8">
                    <div className="h-2 bg-muted rounded-full overflow-hidden backdrop-blur-sm">
                        <div className="progress-bar h-full bg-primary"></div>
                    </div>
                </div>

                {/* Loading Steps */}
                <div className="space-y-3 text-sm text-muted-foreground">
                    <div className="loading-step">
                        <div className="loading-dot"></div>
                        <span>Processing multi-modal imaging data</span>
                    </div>
                    <div className="loading-step" style={{ animationDelay: "0.5s" }}>
                        <div className="loading-dot" style={{ animationDelay: "0.5s" }}></div>
                        <span>Extracting ROI features from MRI and PET scans</span>
                    </div>
                    <div className="loading-step" style={{ animationDelay: "1s" }}>
                        <div className="loading-dot" style={{ animationDelay: "1s" }}></div>
                        <span>Running LSTM temporal model</span>
                    </div>
                    <div className="loading-step" style={{ animationDelay: "1.5s" }}>
                        <div className="loading-dot" style={{ animationDelay: "1.5s" }}></div>
                        <span>Generating 15 future predictions</span>
                    </div>
                </div>

                {/* Technical Info */}
                <div className="mt-12 text-xs text-muted-foreground/60">
                    <p>Multi-modal LSTM Neural Network • 193 Features • 4 Clinical Scores</p>
                </div>
            </div>

            {/* Decorative Elements */}
            <div className="absolute top-10 left-10 w-32 h-32 bg-primary/10 rounded-full blur-3xl"></div>
            <div className="absolute bottom-10 right-10 w-40 h-40 bg-primary/10 rounded-full blur-3xl"></div>
        </div>
    );
}

export default AlzheimerPredictionLoading;
