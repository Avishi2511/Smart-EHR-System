import React, { useState } from 'react';
import { CreditCard, Wifi, WifiOff } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import CardReader from './CardReader';
import CardWriter from './CardWriter';
import OfflineIndicator from './OfflineIndicator';

function CardManagement() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  React.useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return (
    <main className="grid flex-1 items-start gap-4 p-4 sm:px-6 sm:py-0">
      <div className="mx-auto grid w-full max-w-6xl gap-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CreditCard className="h-6 w-6" />
            <h1 className="text-2xl font-bold">Emergency Card Management</h1>
          </div>
          <div className="flex items-center gap-2">
            {isOnline ? (
              <div className="flex items-center gap-1 text-green-600">
                <Wifi className="h-4 w-4" />
                <span className="text-sm">Online</span>
              </div>
            ) : (
              <div className="flex items-center gap-1 text-orange-600">
                <WifiOff className="h-4 w-4" />
                <span className="text-sm">Offline</span>
              </div>
            )}
          </div>
        </div>

        <OfflineIndicator />

        <Card>
          <CardHeader>
            <CardTitle>NFC Health Card System</CardTitle>
            <CardDescription>
              Read patient information from NFC cards for emergency access, or write new patient data to cards.
              This system works offline for disaster scenarios and emergency medical situations.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="read" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="read">Read Card</TabsTrigger>
                <TabsTrigger value="write">Write Card</TabsTrigger>
              </TabsList>
              
              <TabsContent value="read" className="mt-6">
                <CardReader />
              </TabsContent>
              
              <TabsContent value="write" className="mt-6">
                <CardWriter />
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}

export default CardManagement;
