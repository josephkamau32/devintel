/**
 * useIndexingProgress — Real-time WebSocket hook for repository indexing progress.
 * Falls back to polling if WebSocket is unavailable.
 */

import { useEffect, useRef, useState } from "react";
import type { IndexingProgress } from "@/lib/types";

const WS_BASE_URL = import.meta.env.VITE_WS_URL ||
    (window.location.protocol === "https:" ? "wss:" : "ws:") + "//" + (import.meta.env.VITE_API_HOST || window.location.host);

interface UseIndexingProgressOptions {
    repoId: string | null;
    enabled?: boolean;
    onComplete?: () => void;
}

interface UseIndexingProgressResult {
    progress: number;
    status: IndexingProgress["status"] | "idle";
    connected: boolean;
    error: string | null;
}

export function useIndexingProgress({
    repoId,
    enabled = true,
    onComplete,
}: UseIndexingProgressOptions): UseIndexingProgressResult {
    const [progress, setProgress] = useState(0);
    const [status, setStatus] = useState<IndexingProgress["status"] | "idle">("idle");
    const [connected, setConnected] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const onCompleteRef = useRef(onComplete);
    onCompleteRef.current = onComplete;

    useEffect(() => {
        if (!repoId || !enabled) return;

        const token = localStorage.getItem("access_token");
        if (!token) {
            setError("No access token — cannot connect to progress stream");
            return;
        }

        let isCancelled = false;

        function connect() {
            const url = `${WS_BASE_URL}/ws/repos/${repoId}/progress?token=${encodeURIComponent(token!)}`;

            try {
                const ws = new WebSocket(url);
                wsRef.current = ws;

                ws.onopen = () => {
                    if (!isCancelled) setConnected(true);
                };

                ws.onmessage = (event) => {
                    if (isCancelled) return;
                    try {
                        const data: IndexingProgress = JSON.parse(event.data);

                        if ("error" in data) {
                            setError((data as Record<string, string>).error);
                            setConnected(false);
                            ws.close();
                            return;
                        }

                        setProgress(data.progress ?? 0);
                        setStatus(data.status ?? "idle");

                        if (data.progress >= 100 || data.status === "done") {
                            setConnected(false);
                            ws.close();
                            onCompleteRef.current?.();
                        }
                    } catch {
                        // Skip malformed frames
                    }
                };

                ws.onerror = () => {
                    if (!isCancelled) {
                        setConnected(false);
                        setError("WebSocket connection failed — falling back to polling");
                        startPollingFallback();
                    }
                };

                ws.onclose = () => {
                    if (!isCancelled) setConnected(false);
                };
            } catch {
                setError("WebSocket not supported — falling back to polling");
                startPollingFallback();
            }
        }

        function startPollingFallback() {
            // Polling fallback: fetch /api/v1/repos/{id}/status every 3 seconds
            const interval = setInterval(async () => {
                if (isCancelled) {
                    clearInterval(interval);
                    return;
                }
                try {
                    const token = localStorage.getItem("access_token");
                    const res = await fetch(`/api/v1/repos/${repoId}/status`, {
                        headers: token ? { Authorization: `Bearer ${token}` } : {},
                    });
                    if (!res.ok) return;
                    const data = await res.json();
                    setProgress(data.indexing_progress ?? 0);
                    if (data.indexed_status) {
                        setStatus("done");
                        setProgress(100);
                        clearInterval(interval);
                        onCompleteRef.current?.();
                    }
                } catch {
                    // Ignore polling failures
                }
            }, 3000);

            return () => clearInterval(interval);
        }

        connect();

        return () => {
            isCancelled = true;
            if (wsRef.current) {
                wsRef.current.close();
                wsRef.current = null;
            }
        };
    }, [repoId, enabled]);

    return { progress, status, connected, error };
}
