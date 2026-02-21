import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { handleAuthCallback } from "@/lib/auth";
import { Zap, Loader2, AlertCircle } from "lucide-react";

export default function AuthCallback() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const code = searchParams.get("code");
    const error = searchParams.get("error");
    const [status, setStatus] = useState<"loading" | "error">("loading");
    const [errorMessage, setErrorMessage] = useState("");

    useEffect(() => {
        const exchangeCode = async () => {
            // GitHub returned an error (e.g. user denied access)
            if (error) {
                setStatus("error");
                setErrorMessage("GitHub authorization was denied. Please try again.");
                return;
            }

            if (!code) {
                navigate("/login", { replace: true });
                return;
            }

            try {
                const user = await handleAuthCallback(code);
                // Small delay so user sees the success state
                navigate("/dashboard", { replace: true });
            } catch (err) {
                console.error("Auth callback error:", err);
                setStatus("error");
                setErrorMessage(
                    err instanceof Error
                        ? err.message
                        : "Authentication failed. Please try again."
                );
            }
        };

        exchangeCode();
    }, [code, error, navigate]);

    return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4">
            <div className="flex flex-col items-center gap-6 text-center max-w-sm">
                {/* Logo */}
                <div className="flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
                        <Zap className="h-4 w-4 text-primary-foreground" />
                    </div>
                    <span className="text-lg font-semibold">DevIntel AI</span>
                </div>

                {status === "loading" ? (
                    <>
                        <Loader2 className="h-10 w-10 animate-spin text-primary" />
                        <div>
                            <h2 className="text-xl font-semibold">Authenticating...</h2>
                            <p className="mt-1 text-sm text-muted-foreground">
                                Connecting to GitHub. Please wait.
                            </p>
                        </div>
                    </>
                ) : (
                    <>
                        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
                            <AlertCircle className="h-6 w-6 text-destructive" />
                        </div>
                        <div>
                            <h2 className="text-xl font-semibold">Authentication Failed</h2>
                            <p className="mt-1 text-sm text-muted-foreground">
                                {errorMessage}
                            </p>
                        </div>
                        <button
                            onClick={() => navigate("/login", { replace: true })}
                            className="mt-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
                        >
                            Back to Login
                        </button>
                    </>
                )}
            </div>
        </div>
    );
}
