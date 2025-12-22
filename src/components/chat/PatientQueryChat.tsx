import { useContext, useState, useEffect, useRef } from 'react';
import { PatientContext } from '@/contexts/PatientContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Loader2, Sparkles, Trash2 } from 'lucide-react';
import { usePatientQuery, ChatMessage } from '@/hooks/usePatientQuery';
import QueryResult from './QueryResult';

const BACKEND_URL = 'http://localhost:8001/api';

const PatientQueryChat = () => {
    const { selectedPatient } = useContext(PatientContext);
    const [query, setQuery] = useState('');
    const [suggestions, setSuggestions] = useState<string[]>([]);
    const scrollRef = useRef<HTMLDivElement>(null);

    const { messages, isLoading, error, sendQuery, clearMessages } = usePatientQuery(
        selectedPatient?.id
    );

    // Fetch query suggestions
    useEffect(() => {
        if (selectedPatient?.id) {
            fetch(`${BACKEND_URL}/chat/suggestions/${selectedPatient.id}`)
                .then(res => res.json())
                .then(data => setSuggestions(data.suggestions || []))
                .catch(err => console.error('Error fetching suggestions:', err));
        }
    }, [selectedPatient?.id]);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (query.trim() && !isLoading) {
            sendQuery(query);
            setQuery('');
        }
    };

    const handleSuggestionClick = (suggestion: string) => {
        setQuery(suggestion);
    };

    if (!selectedPatient) {
        return (
            <div className="flex items-center justify-center h-full">
                <Card className="w-full max-w-md">
                    <CardHeader>
                        <CardTitle>No Patient Selected</CardTitle>
                        <CardDescription>Please select a patient to start querying</CardDescription>
                    </CardHeader>
                </Card>
            </div>
        );
    }

    return (
        <div className="container mx-auto p-6 max-w-6xl h-[calc(100vh-120px)] flex flex-col">
            <div className="mb-4">
                <h1 className="text-3xl font-bold">Patient Query Assistant</h1>
                <p className="text-muted-foreground mt-2">
                    Ask questions about {selectedPatient.name?.[0]?.given?.[0]}{' '}
                    {selectedPatient.name?.[0]?.family}'s medical data
                </p>
            </div>

            <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6 min-h-0">
                {/* Suggestions Panel */}
                <Card className="lg:col-span-1">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Sparkles className="h-5 w-5" />
                            Suggested Queries
                        </CardTitle>
                        <CardDescription>Click to use a suggested query</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <ScrollArea className="h-[500px]">
                            <div className="space-y-2">
                                {suggestions.map((suggestion, index) => (
                                    <Button
                                        key={index}
                                        variant="outline"
                                        className="w-full justify-start text-left h-auto py-3 px-4"
                                        onClick={() => handleSuggestionClick(suggestion)}
                                    >
                                        <span className="text-sm">{suggestion}</span>
                                    </Button>
                                ))}
                            </div>
                        </ScrollArea>
                    </CardContent>
                </Card>

                {/* Chat Panel */}
                <Card className="lg:col-span-2 flex flex-col">
                    <CardHeader className="flex-shrink-0">
                        <div className="flex items-center justify-between">
                            <div>
                                <CardTitle>Chat</CardTitle>
                                <CardDescription>Ask questions in natural language</CardDescription>
                            </div>
                            {messages.length > 0 && (
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={clearMessages}
                                    className="text-muted-foreground"
                                >
                                    <Trash2 className="h-4 w-4 mr-2" />
                                    Clear
                                </Button>
                            )}
                        </div>
                    </CardHeader>

                    <CardContent className="flex-1 flex flex-col min-h-0">
                        {/* Messages */}
                        <ScrollArea className="flex-1 pr-4 mb-4" ref={scrollRef}>
                            {messages.length === 0 ? (
                                <div className="flex items-center justify-center h-full text-center">
                                    <div className="text-muted-foreground">
                                        <Sparkles className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                        <p className="text-lg font-medium">Start a conversation</p>
                                        <p className="text-sm mt-2">
                                            Ask me anything about the patient's medical data
                                        </p>
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {messages.map((message) => (
                                        <MessageBubble key={message.id} message={message} />
                                    ))}
                                    {isLoading && (
                                        <div className="flex items-center gap-2 text-muted-foreground">
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                            <span className="text-sm">Thinking...</span>
                                        </div>
                                    )}
                                </div>
                            )}
                        </ScrollArea>

                        {/* Input */}
                        <form onSubmit={handleSubmit} className="flex gap-2 flex-shrink-0">
                            <Input
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="Ask a question about the patient's data..."
                                disabled={isLoading}
                                className="flex-1"
                            />
                            <Button type="submit" disabled={isLoading || !query.trim()}>
                                {isLoading ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                    <Send className="h-4 w-4" />
                                )}
                            </Button>
                        </form>

                        {error && (
                            <div className="mt-2 text-sm text-red-600">
                                Error: {error}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};

// Message Bubble Component
const MessageBubble = ({ message }: { message: ChatMessage }) => {
    const isUser = message.type === 'user';

    return (
        <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
            <div
                className={`max-w-[80%] rounded-lg px-4 py-3 ${isUser
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted'
                    }`}
            >
                <div className="text-sm whitespace-pre-wrap">{message.content}</div>

                {/* Show data if available */}
                {!isUser && message.data && message.data.length > 0 && (
                    <div className="mt-3">
                        <QueryResult data={message.data} queryType={message.queryType || 'general'} />
                    </div>
                )}

                <div className="text-xs opacity-70 mt-2">
                    {message.timestamp.toLocaleTimeString()}
                </div>
            </div>
        </div>
    );
};

export default PatientQueryChat;
