import os
from datetime import timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from lib.db import db
from models.skipti import (
    ApproveProposalRequest,
    ContextSearchRequest,
    ContextSearchResponse,
    ExportResponse,
    GuestContext,
    InterviewAnswerRequest,
    InterviewAnswerResponse,
    InterviewCompleteRequest,
    InterviewStart,
    MessageResponse,
    Overview,
    PersonaEntry,
    PersonaEntryCreate,
    PersonaEntryUpdate,
    PersonaView,
    PlaygroundRequest,
    PlaygroundResponse,
    ProgressProposal,
    ProgressProposalCreate,
    Project,
    ProjectCheckpoint,
    ProjectCreate,
    ProjectDetail,
    RedeemRequest,
    RestoreRequest,
    ShareCreate,
    ShareCreated,
    ShareGrant,
    UserView,
    utc_now,
)
from services.ai import MODEL_NAME, MODEL_PROVIDER, extract_interview_answer
from services.skipti import (
    OWNER_EMAIL,
    OWNER_ID,
    OWNER_NAME,
    approve_progress_proposal,
    ask_gemini,
    create_owner_session,
    create_progress_proposal,
    create_share,
    get_persona_entries,
    get_project,
    normalize_document,
    redeem_share,
    resolve_guest_session,
    resolve_owner_session,
    restore_checkpoint,
    search_context,
    share_view,
)


router = APIRouter()
DEMO_USER = UserView(id=OWNER_ID, email=OWNER_EMAIL, display_name=OWNER_NAME)
INTERVIEW_BANK = [
    ("Current situation", "What are you currently studying, building, or responsible for?"),
    ("Goals", "What outcome would make the next three months feel successful?"),
    ("Technical skills", "Which technical skills feel strongest, and which are you actively improving?"),
    ("Response style", "How should an AI explain unfamiliar ideas to you?"),
    ("Tools", "Which tools, editors, and platforms do you prefer to work with?"),
    ("Constraints", "Are there hardware, time, accessibility, or budget constraints an assistant should respect?"),
]


async def require_owner(request: Request) -> str:
    owner_id = await resolve_owner_session(request.cookies.get("skipti_owner"))
    if not owner_id:
        raise HTTPException(status_code=401, detail="Owner session required")
    return owner_id


@router.post("/auth/demo", response_model=UserView)
async def demo_login(response: Response):
    token = await create_owner_session()
    response.set_cookie("skipti_owner", token, httponly=True, samesite="lax", max_age=604800, path="/")
    return DEMO_USER


@router.get("/auth/me", response_model=UserView)
async def auth_me(owner_id: str = Depends(require_owner)):
    return DEMO_USER


@router.post("/auth/logout", response_model=MessageResponse)
async def logout(request: Request, response: Response):
    token = request.cookies.get("skipti_owner")
    if token:
        from services.skipti import hash_token

        await db.auth_sessions.delete_one({"token_hash": hash_token(token)})
    response.delete_cookie("skipti_owner", path="/")
    return MessageResponse(message="Signed out")


@router.get("/overview", response_model=Overview)
async def overview(owner_id: str = Depends(require_owner)):
    entries = await get_persona_entries(owner_id)
    projects = [Project(**normalize_document(doc)) for doc in await db.projects.find({"owner_id": owner_id}).sort("updated_at", -1).to_list(20)]
    persona = await db.personas.find_one({"owner_id": owner_id}) or {"revision": 1}
    active_shares = await db.temporary_grants.count_documents({"owner_id": owner_id, "expires_at": {"$gt": utc_now()}, "revoked_at": None})
    return Overview(
        owner=DEMO_USER,
        persona_revision=persona.get("revision", 1),
        persona_entries=len(entries),
        project_count=len(projects),
        active_shares=active_shares,
        projects=projects,
        recent_entries=entries[:4],
        mcp_endpoint=f"{os.environ.get('APP_URL', '').rstrip('/')}/mcp/",
        integration_status={"gemini": "connected" if os.environ.get("EMERGENT_LLM_KEY") else "configuration_required", "database": "local_mongo_adapter", "mcp": "streamable_http"},
    )


@router.get("/persona", response_model=PersonaView)
async def persona(owner_id: str = Depends(require_owner)):
    entries = await get_persona_entries(owner_id, approved_only=False)
    meta = await db.personas.find_one({"owner_id": owner_id}) or {"revision": 1}
    return PersonaView(owner=DEMO_USER, revision=meta.get("revision", 1), entries=entries, categories=sorted({entry.category for entry in entries}))


@router.post("/persona/entries", response_model=PersonaEntry, status_code=201)
async def create_persona_entry(payload: PersonaEntryCreate, owner_id: str = Depends(require_owner)):
    entry = PersonaEntry(owner_id=owner_id, **payload.model_dump())
    await db.persona_entries.insert_one(entry.model_dump())
    await db.personas.update_one({"owner_id": owner_id}, {"$inc": {"revision": 1}, "$set": {"updated_at": utc_now()}}, upsert=True)
    return entry


@router.patch("/persona/entries/{entry_id}", response_model=PersonaEntry)
async def update_persona_entry(entry_id: str, payload: PersonaEntryUpdate, owner_id: str = Depends(require_owner)):
    changes = payload.model_dump(exclude_none=True)
    changes["updated_at"] = utc_now()
    document = await db.persona_entries.find_one_and_update(
        {"id": entry_id, "owner_id": owner_id}, {"$set": changes}, return_document=True
    )
    if not document:
        raise HTTPException(status_code=404, detail="Context entry not found")
    await db.personas.update_one({"owner_id": owner_id}, {"$inc": {"revision": 1}, "$set": {"updated_at": utc_now()}}, upsert=True)
    return PersonaEntry(**normalize_document(document))


@router.delete("/persona/entries/{entry_id}", response_model=MessageResponse)
async def delete_persona_entry(entry_id: str, owner_id: str = Depends(require_owner)):
    result = await db.persona_entries.delete_one({"id": entry_id, "owner_id": owner_id})
    if not result.deleted_count:
        raise HTTPException(status_code=404, detail="Context entry not found")
    await db.personas.update_one({"owner_id": owner_id}, {"$inc": {"revision": 1}, "$set": {"updated_at": utc_now()}}, upsert=True)
    return MessageResponse(message="Context entry deleted")


@router.get("/persona/export", response_model=ExportResponse)
async def export_persona(owner_id: str = Depends(require_owner)):
    entries = await get_persona_entries(owner_id)
    meta = await db.personas.find_one({"owner_id": owner_id}) or {"revision": 1}
    lines = ["# SKIPTI BASE PERSONA", "", f"Revision: {meta.get('revision', 1)}", ""]
    categories: dict[str, list[PersonaEntry]] = {}
    for entry in entries:
        if entry.sensitivity != "sensitive":
            categories.setdefault(entry.category, []).append(entry)
    for category, items in categories.items():
        lines.extend([f"## {category}", *[f"- **{item.label}:** {item.value}" for item in items], ""])
    return ExportResponse(filename="skipti-base-persona.md", markdown="\n".join(lines), revision=meta.get("revision", 1), exported_at=utc_now())


@router.post("/interview/start", response_model=InterviewStart, status_code=201)
async def start_interview(owner_id: str = Depends(require_owner)):
    session_id = str(uuid4())
    category, question = INTERVIEW_BANK[0]
    await db.interview_sessions.insert_one({"id": session_id, "owner_id": owner_id, "index": 0, "current_question": question, "categories": [], "candidates": [], "history": [], "created_at": utc_now()})
    return InterviewStart(session_id=session_id, question=question, category=category, progress=0)


@router.post("/interview/answer", response_model=InterviewAnswerResponse)
async def answer_interview(payload: InterviewAnswerRequest, owner_id: str = Depends(require_owner)):
    session = await db.interview_sessions.find_one({"id": payload.session_id, "owner_id": owner_id})
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    index = session.get("index", 0)
    current_question = session["current_question"]
    candidates = list(session.get("candidates", []))
    ai_available = False
    next_question: str | None = None
    next_category: str | None = None
    if not payload.skipped:
        try:
            extracted = await extract_interview_answer(current_question, payload.answer, session.get("categories", []))
            ai_available = True
            for raw in extracted.get("entries", [])[:4]:
                if not all(raw.get(key) for key in ("category", "label", "value")):
                    continue
                entry = PersonaEntry(
                    owner_id=owner_id,
                    category=str(raw["category"])[:60],
                    label=str(raw["label"])[:100],
                    value=str(raw["value"])[:2000],
                    entry_type=raw.get("entry_type") if raw.get("entry_type") in {"fact", "preference", "constraint", "goal"} else "fact",
                    approval_status="candidate",
                    source="gemini_interview",
                )
                candidates.append(entry.model_dump())
            next_question = extracted.get("next_question")
            next_category = extracted.get("next_category")
        except Exception:
            ai_available = False
    next_index = index + 1
    complete = next_index >= len(INTERVIEW_BANK)
    if not complete and (not next_question or not next_category):
        next_category, next_question = INTERVIEW_BANK[next_index]
    categories = [*session.get("categories", []), INTERVIEW_BANK[min(index, len(INTERVIEW_BANK) - 1)][0]]
    await db.interview_sessions.update_one(
        {"id": payload.session_id},
        {"$set": {"index": next_index, "current_question": next_question, "categories": categories, "candidates": candidates}, "$push": {"history": {"question": current_question, "answer": payload.answer, "skipped": payload.skipped, "created_at": utc_now()}}},
    )
    return InterviewAnswerResponse(
        session_id=payload.session_id,
        question=None if complete else next_question,
        category=None if complete else next_category,
        progress=min(100, round(next_index / len(INTERVIEW_BANK) * 100)),
        candidates=[PersonaEntry(**normalize_document(item)) for item in candidates],
        complete=complete,
        ai_available=ai_available,
    )


@router.post("/interview/complete", response_model=PersonaView)
async def complete_interview(payload: InterviewCompleteRequest, owner_id: str = Depends(require_owner)):
    session = await db.interview_sessions.find_one({"id": payload.session_id, "owner_id": owner_id})
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    selected = []
    for raw in session.get("candidates", []):
        if raw["id"] in payload.approved_entry_ids:
            raw["approval_status"] = "approved"
            raw["updated_at"] = utc_now()
            selected.append(raw)
    if selected:
        for entry in selected:
            await db.persona_entries.update_one({"id": entry["id"]}, {"$set": entry}, upsert=True)
    await db.interview_sessions.update_one({"id": payload.session_id}, {"$set": {"completed_at": utc_now()}})
    await db.personas.update_one({"owner_id": owner_id}, {"$inc": {"revision": 1}, "$set": {"updated_at": utc_now()}}, upsert=True)
    return await persona(owner_id)


@router.get("/projects", response_model=list[Project])
async def list_projects(owner_id: str = Depends(require_owner)):
    docs = await db.projects.find({"owner_id": owner_id}).sort("updated_at", -1).to_list(100)
    return [Project(**normalize_document(doc)) for doc in docs]


@router.post("/projects", response_model=Project, status_code=201)
async def create_project(payload: ProjectCreate, owner_id: str = Depends(require_owner)):
    project = Project(owner_id=owner_id, **payload.model_dump())
    await db.projects.insert_one(project.model_dump())
    checkpoint = ProjectCheckpoint(project_id=project.id, owner_id=owner_id, revision=1, summary="Project Holder created", state=project.model_dump(mode="json"), source="owner")
    await db.project_checkpoints.insert_one(checkpoint.model_dump())
    return project


@router.get("/projects/{project_id}", response_model=ProjectDetail)
async def project_detail(project_id: str, owner_id: str = Depends(require_owner)):
    project = await get_project(owner_id, project_id)
    context_docs = await db.project_context_entries.find({"owner_id": owner_id, "project_id": project_id}).to_list(200)
    pending = await db.project_update_proposals.count_documents({"owner_id": owner_id, "project_id": project_id, "status": "pending_approval"})
    return ProjectDetail(project=project, context_entries=[PersonaEntry(**normalize_document(doc)) for doc in context_docs], pending_proposals=pending)


@router.get("/projects/{project_id}/proposals", response_model=list[ProgressProposal])
async def list_proposals(project_id: str, owner_id: str = Depends(require_owner)):
    await get_project(owner_id, project_id)
    docs = await db.project_update_proposals.find({"owner_id": owner_id, "project_id": project_id}).sort("created_at", -1).to_list(100)
    return [ProgressProposal(**normalize_document(doc)) for doc in docs]


@router.post("/projects/{project_id}/proposals", response_model=ProgressProposal, status_code=201)
async def propose_progress(project_id: str, payload: ProgressProposalCreate, owner_id: str = Depends(require_owner)):
    return await create_progress_proposal(owner_id, project_id, payload.update_text, payload.expected_revision, payload.source_provider)


@router.post("/projects/{project_id}/proposals/{proposal_id}/approve", response_model=ProjectCheckpoint)
async def approve_progress(project_id: str, proposal_id: str, payload: ApproveProposalRequest, owner_id: str = Depends(require_owner)):
    return await approve_progress_proposal(owner_id, project_id, proposal_id, payload.expected_revision)


@router.get("/projects/{project_id}/history", response_model=list[ProjectCheckpoint])
async def project_history(project_id: str, owner_id: str = Depends(require_owner)):
    await get_project(owner_id, project_id)
    docs = await db.project_checkpoints.find({"owner_id": owner_id, "project_id": project_id}).sort("revision", -1).to_list(200)
    return [ProjectCheckpoint(**normalize_document(doc)) for doc in docs]


@router.get("/projects/{project_id}/history/{revision}", response_model=ProjectCheckpoint)
async def project_checkpoint(project_id: str, revision: int, owner_id: str = Depends(require_owner)):
    doc = await db.project_checkpoints.find_one({"owner_id": owner_id, "project_id": project_id, "revision": revision})
    if not doc:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    return ProjectCheckpoint(**normalize_document(doc))


@router.post("/projects/{project_id}/restore", response_model=ProjectCheckpoint)
async def restore_project(project_id: str, payload: RestoreRequest, owner_id: str = Depends(require_owner)):
    return await restore_checkpoint(owner_id, project_id, payload.revision, payload.expected_revision)


@router.post("/context/search", response_model=ContextSearchResponse)
async def context_search(payload: ContextSearchRequest, owner_id: str = Depends(require_owner)):
    return await search_context(owner_id, payload.query, payload.project_id, payload.max_entries)


@router.post("/playground/ask", response_model=PlaygroundResponse)
async def playground_ask(payload: PlaygroundRequest, owner_id: str = Depends(require_owner)):
    try:
        answer, retrieval = await ask_gemini(owner_id, payload.query, payload.project_id, payload.max_entries, payload.session_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Gemini is temporarily unavailable: {type(exc).__name__}") from exc
    return PlaygroundResponse(answer=answer, retrieval=retrieval, provider=MODEL_PROVIDER, model=MODEL_NAME)


@router.post("/shares", response_model=ShareCreated, status_code=201)
async def create_persona_pass(payload: ShareCreate, owner_id: str = Depends(require_owner)):
    grant, token, qr_data_uri = await create_share(owner_id, payload.project_id, payload.permissions, payload.duration_minutes)
    return ShareCreated(**grant.model_dump(), connect_url=f"{os.environ.get('APP_URL', '').rstrip('/')}/connect/{token}", qr_data_uri=qr_data_uri)


@router.get("/shares", response_model=list[ShareGrant])
async def list_persona_passes(owner_id: str = Depends(require_owner)):
    docs = await db.temporary_grants.find({"owner_id": owner_id}).sort("created_at", -1).to_list(100)
    return [await share_view(normalize_document(doc)) for doc in docs]


@router.post("/shares/{grant_id}/revoke", response_model=MessageResponse)
async def revoke_persona_pass(grant_id: str, owner_id: str = Depends(require_owner)):
    now = utc_now()
    result = await db.temporary_grants.update_one({"id": grant_id, "owner_id": owner_id}, {"$set": {"revoked_at": now}})
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="Persona Pass not found")
    await db.guest_sessions.update_many({"grant_id": grant_id}, {"$set": {"revoked_at": now}})
    return MessageResponse(message="Persona Pass revoked; future retrieval is blocked")


@router.post("/shares/redeem", response_model=ShareGrant)
async def redeem_persona_pass(payload: RedeemRequest, response: Response):
    session_token, grant = await redeem_share(payload.token)
    response.set_cookie("skipti_guest", session_token, httponly=True, samesite="strict", max_age=3600, path="/")
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return grant


@router.get("/guest/context", response_model=GuestContext)
async def guest_context(request: Request, response: Response):
    resolved = await resolve_guest_session(request.cookies.get("skipti_guest"))
    if not resolved:
        raise HTTPException(status_code=401, detail="Temporary access has ended")
    grant_doc = resolved["grant"]
    grant = await share_view(grant_doc)
    permissions = set(grant.permissions)
    entries = await get_persona_entries(resolved["session"]["owner_id"])
    category_map = {"goals": "goal", "skills": "skill", "ai_preferences": "preference"}
    if "general_profile" not in permissions:
        allowed_terms = {category_map[key] for key in category_map if key in permissions}
        entries = [entry for entry in entries if any(term in entry.category.lower() or term == entry.entry_type for term in allowed_terms)]
    entries = [entry for entry in entries if entry.sensitivity != "sensitive"]
    project = None
    if grant.project_id and "project" in permissions:
        project = await get_project(resolved["session"]["owner_id"], grant.project_id)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return GuestContext(grant=grant, persona_entries=entries, project=project)
