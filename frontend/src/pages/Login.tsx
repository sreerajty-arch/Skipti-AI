import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, LockKeyhole } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiPost } from "@/lib/api";
import type { AuthResponse } from "@/lib/skipti";

export default function Login() {
  const location = useLocation(); const navigate = useNavigate(); const client = useQueryClient();
  const signup = location.pathname === "/signup";
  const [email, setEmail] = useState(""); const [password, setPassword] = useState(""); const [displayName, setDisplayName] = useState("");
  const auth = useMutation({
    mutationFn: () => apiPost<AuthResponse>(signup ? "/auth/signup" : "/auth/login", signup ? { email, password, display_name: displayName } : { email, password }),
    onSuccess: (result) => {
      if (result.requires_confirmation) { toast.success(result.message); navigate("/login"); return; }
      if (result.user) client.setQueryData(["auth", "me"], result.user);
      toast.success(signup ? "Account created" : "Welcome back");
      navigate("/dashboard");
    },
    onError: (error) => toast.error(error instanceof Error ? error.message : "Authentication failed"),
  });
  return <main className="page-enter relative grid min-h-screen overflow-hidden bg-[#0c0a09] text-foreground lg:grid-cols-2" data-testid={signup ? "signup-page" : "login-page"}>
    <section className="relative hidden overflow-hidden border-r border-border bg-[#100e0e] lg:block" data-testid="login-texture-panel"><img src="https://static.prod-images.emergentagent.com/jobs/998467b0-e0cb-41de-9528-3854c8262275/images/86651936e90994e3fab1ceb2e1097038611957257229a46dca61f4133da8715e.jpeg" alt="Abstract map of connected context" className="animate-hero-drift absolute inset-0 h-full w-full object-cover opacity-70" data-testid="login-custom-artwork" /><div className="absolute inset-0 bg-gradient-to-t from-[#0c0a09] via-[#0c0a09]/35 to-[#0c0a09]/20" /><div className="absolute inset-x-12 bottom-14 z-10"><p className="font-mono text-[10px] uppercase tracking-[.3em] text-[#c47a91]" data-testid="login-quote-label">Private by design</p><blockquote className="mt-5 max-w-xl font-heading text-5xl font-light leading-[1.04] tracking-[-.025em]" data-testid="login-quote">“Your context should travel with you — and remain yours.”</blockquote></div></section>
    <section className="flex items-center justify-center px-6 py-16" data-testid="login-form-section"><div className="w-full max-w-md"><Link to="/" className="flex items-center gap-3 font-heading text-3xl" data-testid="login-product-name"><img src="/skipti-mark.svg" alt="" className="size-10 rounded-xl" /> Skipti AI</Link><form className="panel mt-12 p-7 md:p-10" onSubmit={(event) => { event.preventDefault(); auth.mutate(); }} data-testid={signup ? "signup-form" : "login-form"}><span className="grid size-11 place-items-center rounded-xl border border-[#581d30] bg-[#1b0c10] text-[#d7a0b1]"><LockKeyhole className="size-4" /></span><h1 className="mt-8 font-heading text-5xl font-light" data-testid="login-title">{signup ? "Create your context room." : "Enter your context room."}</h1><p className="mt-4 text-sm leading-6 text-muted-foreground" data-testid="login-description">{signup ? "One private account for your Persona, projects, files, and temporary AI connections." : "Sign in to your private Persona and canonical project memory."}</p><div className="mt-8 space-y-4">{signup ? <div><label htmlFor="display-name" className="mb-2 block text-xs text-muted-foreground">Display name</label><Input id="display-name" value={displayName} onChange={(event) => setDisplayName(event.target.value)} autoComplete="name" required data-testid="signup-display-name-input" /></div> : null}<div><label htmlFor="email" className="mb-2 block text-xs text-muted-foreground">Email address</label><Input id="email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required data-testid="auth-email-input" /></div><div><label htmlFor="password" className="mb-2 block text-xs text-muted-foreground">Password</label><Input id="password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete={signup ? "new-password" : "current-password"} minLength={8} required data-testid="auth-password-input" /></div></div><Button className="mt-7 w-full" size="lg" type="submit" disabled={auth.isPending} data-testid="auth-submit-button">{auth.isPending ? "Securing account…" : signup ? "Create account" : "Sign in"}<ArrowRight className="size-4" /></Button><p className="mt-6 text-center text-xs text-muted-foreground">{signup ? "Already have an account?" : "New to Skipti?"} <Link to={signup ? "/login" : "/signup"} className="font-medium text-[#d7a0b1] underline-offset-4 hover:underline" data-testid="auth-mode-switch-link">{signup ? "Sign in" : "Create an account"}</Link></p></form></div></section>
  </main>;
}