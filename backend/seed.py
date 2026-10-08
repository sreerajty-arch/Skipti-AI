import asyncio
from datetime import timedelta

from lib.db import db, ensure_indexes
from models.skipti import PersonaEntry, Project, ProjectCheckpoint, ProgressProposal, utc_now
from services.skipti import OWNER_EMAIL, OWNER_ID, OWNER_NAME


SKIPTI_PROJECT_ID = "11111111-1111-4111-8111-111111111111"
FOCUS_PROJECT_ID = "22222222-2222-4222-8222-222222222222"


async def seed() -> None:
    await ensure_indexes()
    await db.users.update_one(
        {"id": OWNER_ID},
        {"$set": {"id": OWNER_ID, "email": OWNER_EMAIL, "display_name": OWNER_NAME, "auth_mode": "demo_owner", "updated_at": utc_now()}},
        upsert=True,
    )
    await db.personas.update_one(
        {"owner_id": OWNER_ID},
        {"$set": {"owner_id": OWNER_ID, "revision": 6, "updated_at": utc_now()}},
        upsert=True,
    )
    seed_entries = [
        ("a1000000-0000-4000-8000-000000000001", "Current situation", "Current role", "Data Science student building AI products", "fact"),
        ("a1000000-0000-4000-8000-000000000002", "Goals", "Main direction", "Build practical AI and machine learning systems", "goal"),
        ("a1000000-0000-4000-8000-000000000003", "Technical skills", "Python", "Comfortable with fundamentals; improving API and architecture skills", "fact"),
        ("a1000000-0000-4000-8000-000000000004", "AI preferences", "Programming responses", "Provide working code first, then explain the important decisions", "preference"),
        ("a1000000-0000-4000-8000-000000000005", "Hardware", "Primary laptop", "Lenovo LOQ, 16 GB RAM, NVIDIA RTX 3050 6 GB", "constraint"),
        ("a1000000-0000-4000-8000-000000000006", "Tools", "Preferred workspace", "VS Code, Python, FastAPI, and browser-based development", "preference"),
    ]
    for entry_id, category, label, value, entry_type in seed_entries:
        entry = PersonaEntry(id=entry_id, owner_id=OWNER_ID, category=category, label=label, value=value, entry_type=entry_type, source="seeded_demo")
        await db.persona_entries.update_one({"id": entry.id}, {"$set": entry.model_dump()}, upsert=True)

    skipti = Project(
        id=SKIPTI_PROJECT_ID,
        owner_id=OWNER_ID,
        name="Skipti AI",
        description="MCP-first context intelligence that lets users carry approved Persona and project memory across AI clients.",
        purpose="Give compatible AI systems minimum relevant, user-controlled context.",
        stack=["FastAPI", "React", "MongoDB adapter", "Gemini", "Model Context Protocol"],
        revision=3,
        completed=["Defined normalized context schema", "Built demo owner session", "Connected canonical Project Holder storage"],
        in_progress=["Validate remote MCP retrieval", "Refine adaptive Persona interview"],
        blockers=[],
        decisions=["Use Streamable HTTP for MCP", "Require approval before canonical memory updates", "Use a local Mongo adapter until Supabase credentials are configured"],
        next_steps=["Run cross-client continuity check", "Generate a temporary Persona Pass"],
    )
    focus = Project(
        id=FOCUS_PROJECT_ID,
        owner_id=OWNER_ID,
        name="Focus Room",
        description="A quiet, editorial productivity workspace for deep work sessions.",
        purpose="Help students protect focused time without noisy gamification.",
        stack=["React", "TypeScript", "FastAPI"],
        revision=2,
        completed=["Established charcoal and burgundy design system"],
        in_progress=["Session reflection flow"],
        blockers=["Need to validate notification behavior on mobile"],
        decisions=["Keep interaction motion subtle and purposeful"],
        next_steps=["Test the reflection flow on a phone"],
    )
    for project in (skipti, focus):
        await db.projects.update_one({"id": project.id}, {"$set": project.model_dump()}, upsert=True)
        # The preview seed is a deterministic reset: remove checkpoints created by earlier demo runs
        # before restoring the canonical seeded revision. This preserves the unique revision invariant.
        await db.project_checkpoints.delete_many({"project_id": project.id, "revision": {"$gt": project.revision}})
        for revision in range(1, project.revision + 1):
            checkpoint = ProjectCheckpoint(
                id=f"{project.id[:8]}-0000-4000-8000-{revision:012d}",
                project_id=project.id,
                owner_id=OWNER_ID,
                revision=revision,
                summary=("Initial architecture approved" if revision == 1 else "Canonical project memory updated" if revision < project.revision else "Latest approved project state"),
                state=project.model_dump(mode="json"),
                source="seeded_demo",
                created_at=utc_now() - timedelta(days=project.revision - revision),
            )
            await db.project_checkpoints.update_one({"project_id": project.id, "revision": revision}, {"$set": checkpoint.model_dump()}, upsert=True)
    proposal = ProgressProposal(
        id="33333333-3333-4333-8333-333333333333",
        project_id=SKIPTI_PROJECT_ID,
        owner_id=OWNER_ID,
        summary="MCP remote retrieval validation",
        completed=[],
        in_progress=["Test tool discovery from a second MCP client"],
        blockers=[],
        decisions=[],
        next_steps=["Approve a checkpoint after the real client result is captured"],
        source_provider="gemini",
        base_revision=3,
    )
    await db.project_update_proposals.update_one({"id": proposal.id}, {"$set": proposal.model_dump()}, upsert=True)
    print("Skipti demo data ready")


if __name__ == "__main__":
    asyncio.run(seed())