import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RotateCcw } from "lucide-react";
import { useParams } from "react-router-dom";
import { toast } from "sonner";
import { AppShell, PageHeader, StatusPill } from "@/components/AppShell";
import { Button } from "@/components/ui/button";
import { apiGet, apiPost } from "@/lib/api";
import type { ProjectCheckpoint, ProjectDetail } from "@/lib/skipti";

export default function ProjectHistory() {
  const { id = "" } = useParams(); const client = useQueryClient();
  const detail = useQuery({ queryKey: ["project", id], queryFn: () => apiGet<ProjectDetail>(`/projects/${id}`), enabled: Boolean(id) });
  const history = useQuery({ queryKey: ["project-history", id], queryFn: () => apiGet<ProjectCheckpoint[]>(`/projects/${id}/history`), enabled: Boolean(id) });
  const restore = useMutation({ mutationFn: (revision: number) => apiPost<ProjectCheckpoint>(`/projects/${id}/restore`, { revision, expected_revision: detail.data?.project.revision }), onSuccess: (checkpoint) => { client.invalidateQueries({ queryKey: ["project-history", id] }); client.invalidateQueries({ queryKey: ["project", id] }); toast.success(`Revision ${checkpoint.revision} created from restore`); }, onError: () => toast.error("Restore conflicted with a newer revision") });
  const current = detail.data?.project.revision;
  return <AppShell><PageHeader eyebrow="Immutable history" title={`${detail.data?.project.name ?? "Project"} revisions`} description="Restoring never overwrites history. Skipti writes the selected state as a new checkpoint." />
    <section className="relative mx-auto max-w-4xl pl-9" data-testid="project-history-timeline"><div className="absolute bottom-0 left-3 top-0 w-px bg-border" />{(history.data ?? []).map((checkpoint, index) => <article className="relative mb-5 border border-border bg-[#151313] p-6" key={checkpoint.id} data-testid={`project-history-revision-${checkpoint.revision}`}><span className={`absolute -left-[30px] top-7 size-2.5 rounded-full border-2 border-[#0c0a09] ${index === 0 ? "bg-[#c47a91] shadow-[0_0_0_5px_rgba(110,13,37,.2)]" : "bg-[#51494b]"}`} /><div className="flex flex-wrap items-start justify-between gap-4"><div><div className="flex items-center gap-3"><StatusPill tone={index === 0 ? "brand" : "neutral"}>Revision {checkpoint.revision}</StatusPill><span className="font-mono text-[9px] text-muted-foreground" data-testid={`project-history-revision-${checkpoint.revision}-date`}>{new Date(checkpoint.created_at).toLocaleString()}</span></div><h2 className="mt-5 font-heading text-3xl" data-testid={`project-history-revision-${checkpoint.revision}-summary`}>{checkpoint.summary}</h2><p className="mt-2 font-mono text-[9px] uppercase tracking-widest text-muted-foreground" data-testid={`project-history-revision-${checkpoint.revision}-source`}>Source · {checkpoint.source}</p></div>{current && checkpoint.revision !== current ? <Button variant="outline" size="sm" onClick={() => restore.mutate(checkpoint.revision)} disabled={restore.isPending} data-testid={`project-history-revision-${checkpoint.revision}-restore-button`}><RotateCcw className="size-3.5" /> Restore as revision {current + 1}</Button> : <StatusPill tone="good">Current</StatusPill>}</div></article>)}</section>
  </AppShell>;
}