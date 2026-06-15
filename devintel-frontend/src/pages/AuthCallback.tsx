import { useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { apiClient } from "../lib/api-client";
import { useAuth } from "../contexts/AuthContext";

interface TokenResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
    user: {
        id: string;
        email: string;
        name: string;
        avatar_url: string;
    };
}

export default function AuthCallback() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const { setTokens } = useAuth();
    const code = searchParams.get("code");
    // Guard against double-invocation (React strict mode / fast-refresh)
    const hasFetched = useRef(false);

    useEffect(() => {
        if (hasFetched.current) return;
        hasFetched.current = true;

        const exchangeCodeForToken = async () => {
            if (!code) {
                navigate("/login");
                return;
            }

            try {
                const response = await apiClient.post<TokenResponse>("/api/v1/auth/github/callback", {
                    code,
                });

                const { access_token, refresh_token, user } = response;

                setTokens(access_token, refresh_token, user);

                toast.success(`Welcome back, ${user.name || "Developer"}!`);
                navigate("/dashboard");
            } catch (error: unknown) {
                console.error("Auth callback error:", error);

                // Show a meaningful error if the backend gave one
                const detail =
                    (error as any)?.response?.data?.detail
                        ? String((error as any).response.data.detail)
                        : "Authentication failed. Please try again.";

                toast.error(detail);
                navigate("/login");
            }
        };

        exchangeCodeForToken();
    }, [code, navigate]);

    return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-background">
            <div className="flex flex-col items-center gap-4">
                <Loader2 className="h-10 w-10 animate-spin text-primary" />
                <h2 className="text-xl font-semibold">Authenticating...</h2>
                <p className="text-muted-foreground">Please wait while we connect to GitHub.</p>
            </div>
        </div>
    );
}
