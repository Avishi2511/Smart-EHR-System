import { useState } from 'react';

const BACKEND_URL = 'http://localhost:8001/api';

export interface ChatMessage {
    id: string;
    type: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    data?: any[];
    queryType?: string;
    error?: string;
}

export interface QueryResult {
    success: boolean;
    query: string;
    query_type: string;
    data: any[];
    count: number;
    error?: string;
    time_period?: {
        amount: number;
        unit: string;
        start_date: string;
        end_date: string;
    };
}

export const usePatientQuery = (patientId: string | undefined) => {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const sendQuery = async (query: string) => {
        if (!patientId || !query.trim()) return;

        // Add user message
        const userMessage: ChatMessage = {
            id: Date.now().toString(),
            type: 'user',
            content: query,
            timestamp: new Date(),
        };
        setMessages(prev => [...prev, userMessage]);

        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch(`${BACKEND_URL}/chat/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    patient_id: patientId,
                    query: query,
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result: QueryResult = await response.json();

            // Add assistant response
            const assistantMessage: ChatMessage = {
                id: (Date.now() + 1).toString(),
                type: 'assistant',
                content: formatResponse(result),
                timestamp: new Date(),
                data: result.data,
                queryType: result.query_type,
                error: result.error,
            };

            setMessages(prev => [...prev, assistantMessage]);
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'An error occurred';
            setError(errorMessage);

            // Add error message
            const errorMsg: ChatMessage = {
                id: (Date.now() + 1).toString(),
                type: 'assistant',
                content: `Sorry, I encountered an error: ${errorMessage}`,
                timestamp: new Date(),
                error: errorMessage,
            };
            setMessages(prev => [...prev, errorMsg]);
        } finally {
            setIsLoading(false);
        }
    };

    const formatResponse = (result: QueryResult): string => {
        if (!result.success || result.error) {
            return result.error || 'Unable to process your query.';
        }

        if (result.count === 0) {
            // Provide context-specific messages when no data is found
            switch (result.query_type) {
                case 'medications':
                    return 'No medications found in the patient record. The patient may not have any active prescriptions.';
                case 'conditions':
                    return 'No diagnoses or conditions found in the patient record.';
                case 'latest':
                case 'time_series':
                case 'average':
                    return 'No data found for the requested health parameter. Try asking about medications, diagnoses, or different measurements.';
                default:
                    return 'No data found for your query. Try asking about medications, diagnoses, or specific health measurements like blood pressure or glucose.';
            }
        }

        switch (result.query_type) {
            case 'latest':
                return `Found ${result.count} latest reading(s).`;
            case 'time_series':
                return `Found ${result.count} reading(s)${result.time_period ? ` from the last ${result.time_period.amount} ${result.time_period.unit}(s)` : ''}.`;
            case 'average':
                return `Calculated average(s) from ${result.count} reading(s).`;
            case 'medications':
                return `Found ${result.count} medication(s).`;
            case 'conditions':
                return `Found ${result.count} condition(s).`;
            default:
                return `Found ${result.count} result(s).`;
        }
    };

    const clearMessages = () => {
        setMessages([]);
        setError(null);
    };

    return {
        messages,
        isLoading,
        error,
        sendQuery,
        clearMessages,
    };
};
