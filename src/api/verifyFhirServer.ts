import type { CapabilityStatement } from "fhir/r4";

export async function verifyFhirServer(
  endpointUrl: string
): Promise<{ isValidFhirServer: boolean; feedbackMessage: string }> {
  return {
    isValidFhirServer: true,
    feedbackMessage: "Mocked FHIR server verified successfully"
  };
}

export function metadataResponseIsValid(
  response: any
): response is CapabilityStatement {
  return response && response.resourceType === "CapabilityStatement";
}