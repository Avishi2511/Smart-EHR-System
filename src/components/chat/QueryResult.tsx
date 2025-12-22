import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface QueryResultProps {
    data: any[];
    queryType: string;
}

const QueryResult = ({ data, queryType }: QueryResultProps) => {
    if (!data || data.length === 0) {
        return null;
    }

    // Render based on query type
    switch (queryType) {
        case 'latest':
            return <LatestResults data={data} />;
        case 'time_series':
        case 'all':
            return <TimeSeriesResults data={data} />;
        case 'average':
            return <AverageResults data={data} />;
        case 'medications':
            return <MedicationsResults data={data} />;
        case 'conditions':
            return <ConditionsResults data={data} />;
        default:
            return <GenericResults data={data} />;
    }
};

// Latest Results Component
const LatestResults = ({ data }: { data: any[] }) => {
    return (
        <div className="space-y-2">
            {data.map((item, index) => (
                <Card key={index} className="bg-background">
                    <CardContent className="pt-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="font-medium">{item.display}</p>
                                <p className="text-sm text-muted-foreground">
                                    {new Date(item.date).toLocaleDateString()}
                                </p>
                            </div>
                            <div className="text-right">
                                <p className="text-2xl font-bold">
                                    {item.value} <span className="text-sm font-normal text-muted-foreground">{item.unit}</span>
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            ))}
        </div>
    );
};

// Time Series Results Component
const TimeSeriesResults = ({ data }: { data: any[] }) => {
    return (
        <div className="rounded-md border bg-background">
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead>Parameter</TableHead>
                        <TableHead>Value</TableHead>
                        <TableHead>Date</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {data.map((item, index) => (
                        <TableRow key={index}>
                            <TableCell className="font-medium">{item.display}</TableCell>
                            <TableCell>
                                {item.value} {item.unit}
                            </TableCell>
                            <TableCell>{new Date(item.date).toLocaleDateString()}</TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    );
};

// Average Results Component
const AverageResults = ({ data }: { data: any[] }) => {
    return (
        <div className="space-y-2">
            {data.map((item, index) => (
                <Card key={index} className="bg-background">
                    <CardContent className="pt-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="font-medium">{item.display}</p>
                                <p className="text-sm text-muted-foreground">
                                    Average from {item.count} reading(s)
                                </p>
                            </div>
                            <div className="text-right">
                                <p className="text-2xl font-bold">
                                    {item.average} <span className="text-sm font-normal text-muted-foreground">{item.unit}</span>
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            ))}
        </div>
    );
};

// Medications Results Component
const MedicationsResults = ({ data }: { data: any[] }) => {
    return (
        <div className="rounded-md border bg-background">
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead>Medication</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Date</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {data.map((item, index) => (
                        <TableRow key={index}>
                            <TableCell className="font-medium">{item.medication}</TableCell>
                            <TableCell>
                                <Badge variant={item.status === 'active' ? 'default' : 'secondary'}>
                                    {item.status}
                                </Badge>
                            </TableCell>
                            <TableCell>{item.date ? new Date(item.date).toLocaleDateString() : 'N/A'}</TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    );
};

// Conditions Results Component
const ConditionsResults = ({ data }: { data: any[] }) => {
    return (
        <div className="rounded-md border bg-background">
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead>Condition</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Onset</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {data.map((item, index) => (
                        <TableRow key={index}>
                            <TableCell className="font-medium">{item.condition}</TableCell>
                            <TableCell>
                                <Badge variant={item.status === 'active' ? 'destructive' : 'secondary'}>
                                    {item.status}
                                </Badge>
                            </TableCell>
                            <TableCell>{item.onset ? new Date(item.onset).toLocaleDateString() : 'N/A'}</TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    );
};

// Generic Results Component
const GenericResults = ({ data }: { data: any[] }) => {
    return (
        <div className="rounded-md border bg-background p-4">
            <pre className="text-sm overflow-auto">
                {JSON.stringify(data, null, 2)}
            </pre>
        </div>
    );
};

export default QueryResult;
