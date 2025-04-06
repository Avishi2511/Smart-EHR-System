export async function fetchResourceFromEHR(
  axiosInstance: any,
  requestUrl: string
): Promise<any> {
  console.log("Mock fetchResourceFromEHR called with URL:", requestUrl);

  if (requestUrl.includes("Patient")) {
    return {
      resourceType: "Patient",
      id: "mock-patient-123",
      name: [{ given: ["Jane"], family: "Doe" }],
      gender: "female",
      birthDate: "1985-05-05"
    };
  }

  if (requestUrl.includes("Observation")) {
    return {
      resourceType: "Bundle",
      entry: [
        {
          resource: {
            resourceType: "Observation",
            code: { text: "Blood Pressure" },
            valueQuantity: { value: 120, unit: "mmHg" },
            effectiveDateTime: "2024-01-01T10:00:00Z"
          }
        }
      ]
    };
  }

  return {
    resourceType: "OperationOutcome",
    issue: [{ severity: "information", diagnostics: "Mock data used" }]
  };
}
