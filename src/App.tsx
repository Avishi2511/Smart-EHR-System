import { TooltipProvider } from "@/components/ui/tooltip";
import ActivePageContextProvider from "@/contexts/ActivePageContext.tsx";
import { SnackbarProvider } from "notistack";
import PatientContextProvider from "@/contexts/PatientContext.tsx";

import {
  createBrowserRouter,
  Navigate,
  RouterProvider,
} from "react-router-dom";
import PatientSummary from "@/pages/PatientSummary/PatientSummary.tsx";
import EmbeddedApp from "@/pages/EmbeddedApp/EmbeddedApp.tsx";
import AuthCallback from "@/pages/AuthCallback/AuthCallback.tsx";
import Home from "@/layout/Home.tsx";
import FhirServerContextProvider from "@/contexts/FhirServerContext.tsx";
import CloseSnackbar from "@/components/CloseSnackbar.tsx";

function App() {
  const router = createBrowserRouter([
    {
      path: "authcallback",
      element: <AuthCallback />,
    },
    {
      path: "/",
      element: <Home />,
      children: [
        {
          path: "",
          element: <PatientSummary />,
        },
        {
          path: "embedded",
          element: <EmbeddedApp />,
        },
      ],
    },
    {
      path: "*",
      element: <Navigate to="/" replace />,
    },
  ]);

  return (
    <TooltipProvider delayDuration={100}>
      <SnackbarProvider maxSnack={1} action={CloseSnackbar}>
        <FhirServerContextProvider>
          
            <ActivePageContextProvider>
              <PatientContextProvider>
                 
                    
                      <RouterProvider router={router} />
                   
                  

              </PatientContextProvider>
            </ActivePageContextProvider>
        </FhirServerContextProvider>
      </SnackbarProvider>
    </TooltipProvider>
  );
}

export default App;
