import React from 'react';
import { Shield, Zap, WifiOff } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

function OfflineIndicator() {
  return (
    <Card className="border-green-200 bg-green-50">
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-green-600" />
              <span className="font-medium text-green-800">Emergency Ready System</span>
            </div>
            <Badge variant="secondary" className="bg-green-100 text-green-800">
              <WifiOff className="h-3 w-3 mr-1" />
              Offline Capable
            </Badge>
          </div>
          <div className="flex items-center gap-2 text-green-700">
            <Zap className="h-4 w-4" />
            <span className="text-sm font-medium">Instant Access</span>
          </div>
        </div>
        <div className="mt-3 text-sm text-green-700">
          This system works completely offline for emergency situations, disaster areas, and locations with limited connectivity.
          Patient data is stored securely on the NFC card for immediate access by medical personnel.
        </div>
      </CardContent>
    </Card>
  );
}

export default OfflineIndicator;
