import { ArrowRight, Braces, Database, KeyRound, Route, ScanLine } from "lucide-react";
import { Link } from "react-router-dom";
import { motion } from "motion/react";
import { buttonVariants } from "@/components/ui/button";

const architecture = [
  { label: "Persona", detail: "Approved user context", icon: KeyRound },
  { label: "Router", detail: "Minimum disclosure", icon: Route },
  { label: "MCP", detail: "Cross-client protocol", icon: Braces },
  { label: "Memory", detail: "Canonical revisions", icon: Database },
];

export default function Home() {
  return (
    <main className="editorial-grid min-h-screen overflow-hidden bg-[#0c0a09] text-[#fafaf9]" data-testid="public-home-page">
      <nav className="relative z-20 flex items-center justify-between border-b border-[#292524] px-6 py-5 lg:px-12" data-testid="public-navigation">
        <Link to="/" className="flex items-center gap-3 font-heading text-3xl" data-testid="home-logo-link"><img src="/skipti-mark.svg" alt="" className="size-9 rounded-xl" /> Skipti AI</Link>
        <div className="flex items-center gap-2"><Link to="/login" className={buttonVariants({ variant: "ghost", size: "sm" })} data-testid="home-login-link">Login</Link><Link to="/signup" className={buttonVariants({ size: "sm" })} data-testid="home-signup-link">Sign up <ArrowRight className="size-3.5" /></Link></div>
      </nav>
      <section className="relative mx-auto grid min-h-[calc(100vh-81px)] max-w-[1500px] lg:grid-cols-[1.18fr_.82fr]" data-testid="home-hero-section">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="relative z-10 flex flex-col justify-center px-6 py-20 lg:px-16 lg:py-28" data-testid="home-hero-copy">
          <p className="mb-8 font-mono text-[10px] uppercase tracking-[0.34em] text-[#c47a91]" data-testid="home-eyebrow">Context intelligence infrastructure</p>
          <h1 className="max-w-4xl font-heading text-[clamp(4rem,9vw,8.8rem)] font-light leading-[.8] tracking-[-.06em]" data-testid="home-headline">Your context.<br /><em className="font-normal text-[#c47a91]">Any AI.</em><br />Temporarily.</h1>
          <p className="mt-10 max-w-xl text-base leading-7 text-[#aaa5a8]" data-testid="home-description">One evolving source of approved Persona and project memory. Routed with minimum disclosure, shared through a real MCP endpoint, and always controlled by you.</p>
          <div className="mt-10 flex flex-wrap gap-3" data-testid="home-hero-actions">
            <Link to="/signup" className={buttonVariants({ size: "lg" })} data-testid="home-create-account-link">Create your account <ArrowRight className="size-4" /></Link>
            <Link to="/login" className={buttonVariants({ variant: "outline", size: "lg" })} data-testid="home-signin-link">Sign in</Link>
          </div>
          <div className="mt-12 grid max-w-2xl grid-cols-3 gap-px overflow-hidden rounded-2xl border border-border bg-border" data-testid="home-proof-grid">
            {[{ value: "18", label: "MCP tools" }, { value: "15", label: "Verified checks" }, { value: "2", label: "Isolated projects" }].map((proof) => <div className="bg-[#12100f] px-4 py-4" key={proof.label} data-testid={`home-proof-${proof.label.toLowerCase().replaceAll(" ", "-")}`}><p className="font-heading text-3xl text-[#f5f1ec]" data-testid={`home-proof-${proof.label.toLowerCase().replaceAll(" ", "-")}-value`}>{proof.value}</p><p className="mt-1 text-[10px] text-[#78716c]" data-testid={`home-proof-${proof.label.toLowerCase().replaceAll(" ", "-")}-label`}>{proof.label}</p></div>)}</div>
          <p className="mt-5 font-mono text-[9px] uppercase tracking-[0.18em] text-[#78716c]" data-testid="home-security-disclosure">Supabase accounts · Private project storage · Gemini connected</p>
        </motion.div>
        <div className="relative overflow-hidden border-t border-[#292524] bg-[#100d0e] p-6 lg:border-l lg:border-t-0 lg:p-12" data-testid="home-architecture-panel">
          <motion.img src="https://static.prod-images.emergentagent.com/jobs/998467b0-e0cb-41de-9528-3854c8262275/images/86651936e90994e3fab1ceb2e1097038611957257229a46dca61f4133da8715e.jpeg" alt="Abstract secure context network" className="absolute inset-0 h-full w-full object-cover opacity-25 mix-blend-screen" initial={{ scale: 1.03 }} animate={{ scale: 1.08, x: -8 }} transition={{ duration: 14, repeat: Infinity, repeatType: "mirror", ease: "easeInOut" }} data-testid="home-context-artwork" />
          <div className="absolute inset-0 bg-[#100d0e]/60" />
          <div className="relative flex h-full flex-col justify-center">
            <div className="mb-7 flex items-center justify-between"><span className="font-mono text-[10px] uppercase tracking-widest text-[#aaa5a8]" data-testid="home-flow-label">Live context flow</span><span className="flex items-center gap-2 font-mono text-[9px] uppercase text-emerald-300" data-testid="home-flow-status"><span className="size-1.5 animate-status-pulse rounded-full bg-emerald-400" /> Operational</span></div>
            <div className="space-y-3" data-testid="home-architecture-list">
              {architecture.map((item, index) => { const Icon = item.icon; return <motion.div key={item.label} initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.12 * index }} className="group relative rounded-2xl border border-[#3a3033] bg-[#151213]/90 p-5 backdrop-blur-sm transition-[border-color,background-color,transform] duration-200 hover:translate-x-1 hover:border-[#6e0d25] hover:bg-[#1b1416]" data-testid={`home-architecture-${item.label.toLowerCase()}-card`}><div className="flex items-center gap-4"><span className="grid size-10 place-items-center rounded-xl border border-[#3a3033] text-[#c47a91]"><Icon className="size-4" /></span><div><p className="font-heading text-2xl" data-testid={`home-architecture-${item.label.toLowerCase()}-title`}>{item.label}</p><p className="text-xs text-[#8d8480]" data-testid={`home-architecture-${item.label.toLowerCase()}-detail`}>{item.detail}</p></div><span className="ml-auto font-mono text-[10px] text-[#655d5a]" data-testid={`home-architecture-${item.label.toLowerCase()}-step`}>0{index + 1}</span></div></motion.div>; })}
            </div>
            <div className="mt-8 rounded-2xl border border-[#581d30] bg-[#160b0e]/95 p-5 backdrop-blur-sm" data-testid="home-mcp-endpoint-card"><div className="mb-3 flex items-center gap-2"><ScanLine className="size-4 text-[#c47a91]" /><span className="font-mono text-[9px] uppercase tracking-widest text-[#c47a91]" data-testid="home-mcp-transport">Streamable HTTP</span></div><code className="break-all font-mono text-xs text-[#ded5d8]" data-testid="home-mcp-endpoint">https://skipti-context.preview.emergentagent.com/mcp/</code></div>
          </div>
        </div>
      </section>
    </main>
  );
}
