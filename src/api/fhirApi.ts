export interface SmartConfiguration {
  authorization_endpoint: string;
  token_endpoint: string;
  scopes_supported?: string[];
}

export async function fetchResourceFromEHR(
  axiosInstance: any,
  requestUrl: string
): Promise<any> {
  try {
    console.log("Fetching from FHIR server:", requestUrl);
    const response = await axiosInstance.get(requestUrl);
    return response.data;
  } catch (error) {
    console.error('FHIR API Error:', error);

    // Return a proper FHIR OperationOutcome for errors
    return {
      resourceType: "OperationOutcome",
      issue: [{
        severity: "error",
        code: "processing",
        diagnostics: `Failed to fetch resource: ${error instanceof Error ? error.message : 'Unknown error'}`
      }]
    };
  }
}
