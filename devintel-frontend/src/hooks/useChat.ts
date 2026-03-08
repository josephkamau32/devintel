import { useState, useCallback, useRef } from 'react';
import { getChatHistory, type ChatMessage } from '@/lib/api';
import apiClient from '@/lib/api-client';

export function useChat(repositoryId?: string) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [loading, setLoading] = useState(false);
    const [streamingContent, setStreamingContent] = useState('');
    const [error, setError] = useState<string | null>(null);
    const abortControllerRef = useRef<AbortController | null>(null);

    const loadHistory = useCallback(async (repoId: string) => {
        setLoading(true);
        setError(null);
        try {
            const data = await getChatHistory(repoId);
            setMessages(data.messages);
        } catch (e: unknown) {
            const err = e as { response?: { data?: { detail?: string } }, message?: string };
            const msg = err?.response?.data?.detail || err?.message || 'Failed to load chat history';
            setError(msg);
        } finally {
            setLoading(false);
        }
    }, []);

    const sendMessage = useCallback(async (question: string) => {
        if (!repositoryId) return;

        // Reset state
        setError(null);
        setStreamingContent('');

        // Add user message to UI immediately
        const userMsg: ChatMessage = { role: 'user', content: question, timestamp: new Date().toISOString() };
        setMessages(prev => [...prev, userMsg]);

        setLoading(true);

        try {
            // Cancel any existing request
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
            abortControllerRef.current = new AbortController();

            const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                },
                body: JSON.stringify({
                    repository_id: repositoryId,
                    question,
                    chat_history: messages.slice(-10), // Send last 10 messages for context
                }),
                signal: abortControllerRef.current.signal,
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.detail || 'Failed to send message');
            }

            const reader = response.body?.getReader();
            if (!reader) throw new Error('No reader available');

            const decoder = new TextDecoder();
            let accumulatedResponse = '';
            let streamError: string | null = null;

            outer: while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (!line.startsWith('data: ')) continue;

                    const payload = line.slice(6).trim();
                    if (payload === '[DONE]') break outer;

                    let data: Record<string, unknown>;
                    try {
                        data = JSON.parse(payload);
                    } catch {
                        // Malformed chunk — skip silently
                        continue;
                    }

                    // Backend sent an explicit error — surface it immediately
                    if (data.error) {
                        streamError = String(data.error);
                        break outer;
                    }

                    if (data.content) {
                        accumulatedResponse += String(data.content);
                        setStreamingContent(accumulatedResponse);
                    }

                    if (data.done) {
                        // Stream finished — persist assistant message
                        setMessages(prev => [
                            ...prev,
                            { role: 'assistant', content: accumulatedResponse, timestamp: new Date().toISOString() }
                        ]);
                        setStreamingContent('');
                    }
                }
            }

            if (streamError) {
                // Remove the optimistic user message so the UI is clean
                setMessages(prev => prev.slice(0, -1));
                setError(streamError);
            }

        } catch (e: unknown) {
            const err = e as { name?: string, message?: string };
            if (err.name === 'AbortError') return;
            // Remove the optimistic user message on hard failures too
            setMessages(prev => prev.slice(0, -1));
            const msg = err.message || 'Something went wrong. Please try again.';
            setError(msg);
        } finally {
            setLoading(false);
            abortControllerRef.current = null;
        }
    }, [repositoryId, messages]);

    const clearHistory = useCallback(() => {
        setMessages([]);
        setStreamingContent('');
        setError(null);
    }, []);

    return {
        messages,
        loading,
        streamingContent,
        error,
        loadHistory,
        sendMessage,
        clearHistory,
    };
}
