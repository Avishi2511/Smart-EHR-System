import { TooltipProvider } from "@/components/ui/tooltip";
import ActivePageContextProvider from "@/contexts/ActivePageContext.tsx";
import { SnackbarProvider } from "notistack";
import PatientContextProvider from "@/contexts/PatientContext.tsx";
import SessionContextProvider from "@/contexts/SessionContext.tsx";

import {
  createBrowserRouter,
  Navigate,
  RouterProvider,
} from "react-router-dom";
import PatientSummary from "@/pages/PatientSummary/PatientSummary.tsx";
import EmbeddedApp from "@/pages/EmbeddedApp/EmbeddedApp.tsx";
import AuthCallback from "@/pages/AuthCallback/AuthCallback.tsx";
import CardManagement from "@/pages/CardManagement/CardManagement.tsx";
import HomePage from "@/pages/HomePage/HomePage.tsx";
import Home from "@/layout/Home.tsx";
import StandaloneLayout from "@/layout/StandaloneLayout.tsx";
import ProtectedRoute from "@/components/ProtectedRoute.tsx";
import FhirServerContextProvider from "@/contexts/FhirServerContext.tsx";
import CloseSnackbar from "@/components/CloseSnackbar.tsx";
import DocumentUpload from "@/pages/DocumentUpload/DocumentUpload.tsx";
import PatientQueryChat from "@/components/chat/PatientQueryChat.tsx";
import Models from "@/pages/Models/Models.tsx";
import Analytics from "@/pages/Analytics/Analytics.tsx";
import Observations from "@/pages/Observations/Observations.tsx";

function App() {
  const router = createBrowserRouter([
    {
      path: "authcallback",
      element: <AuthCallback />,
    },
    // Entry point - standalone HomePage
    {
      path: "/",
      element: <StandaloneLayout />,
      children: [
        {
          path: "",
          element: <HomePage />,
        },
      ],
    },
    // Main application - protected routes with full dashboard
    {
      path: "/app",
      element: (
        <ProtectedRoute>
          <Home />
        </ProtectedRoute>
      ),
      children: [
        {
          path: "",
          element: <Navigate to="/app/dashboard" replace />,
        },
        {
          path: "dashboard",
          element: <PatientSummary />,
        },
        {
          path: "upload-documents",
          element: <DocumentUpload />,
        },
        {
          path: "query-chat",
          element: <PatientQueryChat />,
        },
        {
          path: "analytics",
          element: <Analytics />,
        },
        {
          path: "observations",
          element: <Observations />,
        },
        {
          path: "models",
          element: <Models />,
        },
        {
          path: "embedded",
          element: <EmbeddedApp />,
        },
        {
          path: "card-management",
          element: <CardManagement />,
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
        <SessionContextProvider>
          <FhirServerContextProvider>
            <ActivePageContextProvider>
              <PatientContextProvider>
                <RouterProvider router={router} />
              </PatientContextProvider>
            </ActivePageContextProvider>
          </FhirServerContextProvider>
        </SessionContextProvider>
      </SnackbarProvider>
    </TooltipProvider>
  );
}

export default App;
