/**
 * Patient ID Mapping for ADNI Model
 * 
 * Maps Smart EHR patient IDs to ADNI-specific patient IDs
 * This is only used for the ADNI Alzheimer's progression model
 * All other features use the normal patient IDs
 */

export const ADNI_PATIENT_ID_MAP: Record<string, string> = {
    "patient-002": "033S0567",
    // Add more mappings as needed
    // "patient-003": "ADNI_ID_HERE",
};

/**
 * Get ADNI patient ID from Smart EHR patient ID
 */
export function getAdniPatientId(smartEhrPatientId: string): string {
    return ADNI_PATIENT_ID_MAP[smartEhrPatientId] || smartEhrPatientId;
}

/**
 * Check if patient has ADNI mapping
 */
export function hasAdniMapping(smartEhrPatientId: string): boolean {
    return smartEhrPatientId in ADNI_PATIENT_ID_MAP;
}
