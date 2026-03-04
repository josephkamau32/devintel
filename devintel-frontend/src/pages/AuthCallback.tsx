import { useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

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
                // Use raw axios — NOT apiClient — so the 401 interceptor does
                // not fire on this intentionally unauthenticated request.
                const { data } = await axios.get<TokenResponse>(
                    `${API_BASE_URL}/api/v1/auth/github/callback?code=${code}`
                );

                const { access_token, refresh_token, user } = data;

                // Store auth data
                localStorage.setItem("access_token", access_token);
                localStorage.setItem("refresh_token", refresh_token);
                localStorage.setItem("user", JSON.stringify(user));

                // Notify the rest of the app
                window.dispatchEvent(new CustomEvent("user-updated", { detail: user }));

                toast.success(`Welcome back, ${user.name || "Developer"}!`);
                navigate("/dashboard");
            } catch (error: unknown) {
                console.error("Auth callback error:", error);

                // Show a meaningful error if the backend gave one
                const detail =
                    axios.isAxiosError(error) && error.response?.data?.detail
                        ? String(error.response.data.detail)
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
