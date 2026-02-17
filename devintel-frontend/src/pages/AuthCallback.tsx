import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

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

    useEffect(() => {
        const exchangeCodeForToken = async () => {
            if (!code) {
                navigate("/login");
                return;
            }

            try {
                // Exchange code for token
                // accurate path based on auth.py: @router.get("/github/callback") 
                // We use apiClient.get which appends the base URL
                const response = await apiClient.get<TokenResponse>(`/api/v1/auth/github/callback?code=${code}`);

                const { access_token, refresh_token, user } = response;

                // Store auth data
                localStorage.setItem("access_token", access_token);
                localStorage.setItem("refresh_token", refresh_token);
                localStorage.setItem("user", JSON.stringify(user));

                // Dispatch event to update UI
                window.dispatchEvent(new CustomEvent("user-updated", { detail: user }));

                toast.success(`Welcome back, ${user.name || "Developer"}!`);
                navigate("/dashboard");
            } catch (error) {
                console.error("Auth callback error:", error);
                toast.error("Authentication failed. Please try again.");
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
