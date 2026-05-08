import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { Scissors, Lock } from "lucide-react";
import toast from "react-hot-toast";

import { useLogin, useMe } from "../lib/queries";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { data: me } = useMe();
  const login = useLogin();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  if (me) {
    const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname ?? "/";
    return <Navigate to={from} replace />;
  }

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    login.mutate(
      { username, password },
      {
        onSuccess: () => navigate("/", { replace: true }),
        onError: (err: unknown) => {
          const msg = err instanceof Error ? err.message : "Login failed";
          toast.error(msg);
        },
      }
    );
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-lavender-300 to-lavender-600 flex items-center justify-center shadow-glow-lg mb-4">
            <Scissors className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-semibold text-ink">Costuras Lucía</h1>
          <p className="text-sm text-ink-soft mt-1">Sign in to manage your atelier</p>
        </div>

        <form onSubmit={submit} className="card p-7 space-y-4">
          <div>
            <label className="label">Username</label>
            <input
              autoFocus
              className="input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="label">Password</label>
            <input
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button
            type="submit"
            disabled={login.isPending}
            className="btn btn-primary w-full mt-2 disabled:opacity-60"
          >
            <Lock className="w-4 h-4" />
            {login.isPending ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <p className="text-center text-xs text-ink-soft mt-6">
          Default seed: <span className="font-mono">admin</span> /{" "}
          <span className="font-mono">admin</span>
        </p>
      </div>
    </div>
  );
}
