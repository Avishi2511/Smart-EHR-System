import { LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useSession } from "@/contexts/SessionContext";
import { useContext } from "react";
import { PatientContext } from "@/contexts/PatientContext";
import { useNavigate } from "react-router-dom";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const LogoutButton = () => {
  const { logout } = useSession();
  const { setSelectedPatient } = useContext(PatientContext);
  const navigate = useNavigate();

  const handleLogout = () => {
    // Clear patient context
    setSelectedPatient(null);
    
    // Logout from session
    logout();
    
    // Navigate back to home page
    navigate('/');
  };

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleLogout}
          className="h-9 w-9 text-muted-foreground hover:text-foreground"
        >
          <LogOut className="h-4 w-4" />
        </Button>
      </TooltipTrigger>
      <TooltipContent>
        <p>Logout and return to card scanner</p>
      </TooltipContent>
    </Tooltip>
  );
};

export default LogoutButton;
