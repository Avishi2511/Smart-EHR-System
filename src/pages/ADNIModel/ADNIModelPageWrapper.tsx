import { useContext } from "react";
import { PatientContext } from "@/contexts/PatientContext.tsx";
import ADNIModelPage from "@/components/ADNIModelPage.tsx";

function ADNIModelPageWrapper() {
    const { selectedPatient } = useContext(PatientContext);

    if (!selectedPatient || !selectedPatient.id) {
        return (
            <div className="flex items-center justify-center h-full p-8">
                <div className="text-center">
                    <h2 className="text-2xl font-bold text-gray-700 mb-2">No Patient Selected</h2>
                    <p className="text-gray-500">Please select a patient to view ADNI model predictions.</p>
                </div>
            </div>
        );
    }

    return <ADNIModelPage patientId={selectedPatient.id} />;
}

export default ADNIModelPageWrapper;
