import { useMutation } from "@tanstack/react-query";
import { ArrowRight, LockKeyhole } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { apiPost } from "@/lib/api";
import type { UserView } from "@/lib/skipti";

export default function Login() {
  const navigate = useNavigate();
  const login = useMutation({
    mutationFn: () => apiPost<UserView>("/auth/demo"),
    onSuccess: () => { toast.success("Demo owner session opened"); navigate("/dashboard"); },
    onError: () => toast.error("Could not open the demo workspace"),
  });
  return (
    <main className="relative grid min-h-screen overflow-hidden bg-[#0c0a09] text-foreground lg:grid-cols-2" data-testid="login-page">
      <section className="relative hidden border-r border-border bg-[url('https://images.unsplash.com/photo-1585314062340-f1a5a7c9328d?auto=format&fit=crop&w=1400&q=80')] bg-cover bg-center lg:block" data-testid="login-texture-panel"><div className="absolute inset-0 bg-[#0c0a09]/75" /><div className="absolute inset-x-12 bottom-14 z-10"><p className="font-mono text-[10px] uppercase tracking-[.3em] text-[#c47a91]" data-testid="login-quote-label">Living memory</p><blockquote className="mt-5 max-w-xl font-heading text-5xl font-light leading-[1.04]" data-testid="login-quote">“Your context should travel with you — not remain trapped inside one model.”</blockquote></div></section>
      <section className="flex items-center justify-center px-6 py-16" data-testid="login-form-section">
        <div className="w-full max-w-md">
          <p className="font-heading text-3xl" data-testid="login-product-name">Skipti AI</p>
          <div className="mt-20 border border-border bg-[#151313] p-7 md:p-9" data-testid="login-card">
            <span className="grid size-11 place-items-center border border-[#581d30] bg-[#1b0c10] text-[#d7a0b1]" data-testid="login-lock-icon"><LockKeyhole className="size-4" /></span>
            <h1 className="mt-8 font-heading text-5xl font-light" data-testid="login-title">Enter the context room.</h1>
            <p className="mt-4 text-sm leading-6 text-muted-foreground" data-testid="login-description">This preview uses a seeded demo owner so every Persona, project revision, MCP tool, and temporary pass can be tested immediately.</p>
            <div className="mt-8 border-y border-border py-4" data-testid="login-demo-identity"><p className="text-sm font-medium" data-testid="login-demo-name">Alex Morgan</p><p className="mt-1 font-mono text-[10px] text-muted-foreground" data-testid="login-demo-email">demo@skipti.ai · demo owner</p></div>
            <Button className="mt-8 w-full" size="lg" onClick={() => login.mutate()} disabled={login.isPending} data-testid="login-demo-submit-button">{login.isPending ? "Opening workspace…" : "Enter demo workspace"}<ArrowRight className="size-4" /></Button>
            <p className="mt-5 text-center text-[11px] leading-5 text-muted-foreground" data-testid="login-demo-disclaimer">Demo auth is intentionally isolated from the Supabase production migration included in this build.</p>
          </div>
        </div>
      </section>
    </main>
  );
}