import { useContext, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { PatientContext } from "../../contexts/PatientContext.tsx";
import useLauncherQuery from "../../hooks/useLauncherQuery.ts";
import PatientCard from "@/pages/PatientSummary/PatientCard.tsx";
import PatientDetails from "@/pages/PatientSummary/PatientDetails.tsx";

function PatientSummary() {
  const { selectedPatient } = useContext(PatientContext);
  const [searchParams] = useSearchParams();
  const { setQuery } = useLauncherQuery();

  useEffect(() => {
    const patientIdFromUrl = searchParams.get('patient');
    if (patientIdFromUrl) {
      setQuery({ patient: patientIdFromUrl });
    }
  }, [searchParams, setQuery]);

  return (
    <main className="grid flex-1 items-start gap-4 p-4 sm:px-6 sm:py-0">
      <div className="mx-auto grid w-full max-w-6xl gap-4">
        <div className="grid gap-6">
          <PatientCard patient={selectedPatient} />
          <PatientDetails patient={selectedPatient} />
        </div>
      </div>
    </main>
  );
}

export default PatientSummary;
