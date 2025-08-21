import axios from 'axios';

const FHIR_API_URL = 'http://localhost:8000';

export interface FhirPatientData {
  patient: any;
  conditions: any[];
  observations: any[];
  medications: any[];
  encounters: any[];
}

export const fetchPatientDataFromFhir = async (patientId: string): Promise<FhirPatientData> => {
  try {
    // Fetch all patient-related data in parallel
    const [patientResponse, conditionsResponse, observationsResponse, medicationsResponse, encountersResponse] = await Promise.all([
      axios.get(`${FHIR_API_URL}/Patient/${patientId}`),
      axios.get(`${FHIR_API_URL}/Condition?patient=${patientId}`),
      axios.get(`${FHIR_API_URL}/Observation?patient=${patientId}`),
      axios.get(`${FHIR_API_URL}/MedicationRequest?patient=${patientId}`),
      axios.get(`${FHIR_API_URL}/Encounter?patient=${patientId}`)
    ]);

    return {
      patient: patientResponse.data,
      conditions: conditionsResponse.data.entry?.map((entry: any) => entry.resource) || [],
      observations: observationsResponse.data.entry?.map((entry: any) => entry.resource) || [],
      medications: medicationsResponse.data.entry?.map((entry: any) => entry.resource) || [],
      encounters: encountersResponse.data.entry?.map((entry: any) => entry.resource) || []
    };
  } catch (error) {
    console.error('Error fetching FHIR patient data:', error);
    throw error;
  }
};

export const checkFhirServerStatus = async (): Promise<boolean> => {
  try {
    const response = await axios.get(`${FHIR_API_URL}/health`);
    return response.status === 200;
  } catch (error) {
    return false;
  }
};

export const fetchAllPatients = async (): Promise<any[]> => {
  try {
    const response = await axios.get(`${FHIR_API_URL}/Patient`);
    return response.data.entry?.map((entry: any) => entry.resource) || [];
  } catch (error) {
    console.error('Error fetching patients:', error);
    throw error;
  }
};
