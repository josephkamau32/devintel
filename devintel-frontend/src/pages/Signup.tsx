import { Link } from "react-router-dom";
import { Zap, Github, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { toast } from "sonner";

export default function SignupPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    // For now, redirect to GitHub as main auth method
    // In future, implement direct signup
    toast.info("Please use 'Continue with GitHub' to create an account");
  };

  const handleGitHubSignup = () => {
    // Redirect to backend GitHub OAuth endpoint
    const backendUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
    window.location.href = `${backendUrl}/api/v1/auth/github/login`;
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <Link to="/" className="inline-flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
              <Zap className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="text-lg font-semibold">DevIntel AI</span>
          </Link>
          <h1 className="mt-6 text-xl font-semibold">Create your account</h1>
          <p className="mt-1 text-sm text-muted-foreground">Start understanding your code in minutes</p>
        </div>

        <div className="space-y-4">
          <Button
            variant="outline"
            className="w-full gap-2"
            onClick={handleGitHubSignup}
            disabled={isLoading}
          >
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Github className="h-4 w-4" />}
            Continue with GitHub
          </Button>

          <div className="flex items-center gap-3">
            <div className="h-px flex-1 bg-border" />
            <span className="text-xs text-muted-foreground">or</span>
            <div className="h-px flex-1 bg-border" />
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-sm font-medium text-foreground">Full name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="John Doe"
                className="mt-1.5 h-9 w-full rounded-md border border-input bg-accent px-3 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:border-primary transition-colors"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-foreground">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                className="mt-1.5 h-9 w-full rounded-md border border-input bg-accent px-3 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:border-primary transition-colors"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-foreground">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="mt-1.5 h-9 w-full rounded-md border border-input bg-accent px-3 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:border-primary transition-colors"
              />
            </div>
          </div>

          <Link to="/dashboard">
            <Button className="w-full">Create Account</Button>
          </Link>

          <p className="text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link to="/login" className="text-primary hover:underline">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
