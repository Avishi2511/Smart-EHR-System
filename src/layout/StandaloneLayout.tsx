import { Outlet } from "react-router-dom";
import Footer from "@/components/ui/Footer.tsx";

function StandaloneLayout() {
  return (
    <div className="flex min-h-screen w-full flex-col bg-muted/40">
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}

export default StandaloneLayout;
