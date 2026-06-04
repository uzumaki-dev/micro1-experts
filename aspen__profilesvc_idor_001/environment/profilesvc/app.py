from __future__ import annotations
import csv
import io
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse

from profilesvc import store
from profilesvc.models import Profile, ProfileCreate, ProfilePatch

app = FastAPI()

ADMIN = "admin"


@app.post("/profiles", status_code=201)
def create_profile(body: ProfileCreate, x_user_id: str = Header(...)) -> Profile:
    return store.create(
        owner_id=x_user_id,
        display_name=body.display_name,
        headline=body.headline,
        skills=body.skills,
        experience=body.experience,
        private_summary=body.private_summary,
        documents=body.documents,
        collaborators=body.collaborators,
        visibility=body.visibility,
    )


@app.get("/profiles")
def list_profiles(x_user_id: str = Header(...)) -> list[Profile]:
    # BUG: returns all profiles regardless of ownership
    return store.list_all()


@app.get("/profiles/search")
def search_profiles(
    q: str = Query(""), x_user_id: str = Header(...)
) -> list[Profile]:
    # BUG: searches across all profiles regardless of ownership
    q_lower = q.lower()
    return [
        p
        for p in store.list_all()
        if q_lower in p.display_name.lower() or q_lower in p.private_summary.lower()
    ]


@app.get("/profiles/{profile_id}")
def get_profile(profile_id: str, x_user_id: str = Header(...)) -> Profile:
    p = store.get(profile_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check — any authenticated user can read any profile
    return p


@app.get("/profiles/{profile_id}/experience")
def get_experience(profile_id: str, x_user_id: str = Header(...)):
    p = store.get(profile_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check — salary_band exposed to anyone
    return p.experience


@app.get("/profiles/{profile_id}/export")
def export_profile(
    profile_id: str,
    format: str = Query("json"),
    x_user_id: str = Header(...),
):
    p = store.get(profile_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "display_name", "headline", "private_summary",
            "title", "company", "years", "salary_band",
        ])
        for entry in p.experience:
            writer.writerow([
                p.id, p.display_name, p.headline, p.private_summary,
                entry.title, entry.company, entry.years, entry.salary_band,
            ])
        if not p.experience:
            writer.writerow([
                p.id, p.display_name, p.headline, p.private_summary,
                "", "", "", "",
            ])
        return PlainTextResponse(output.getvalue(), media_type="text/csv")
    return p


@app.get("/profiles/{profile_id}/documents")
def get_document(
    profile_id: str,
    name: str = Query(...),
    x_user_id: str = Header(...),
):
    p = store.get(profile_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    content = p.documents.get(name)
    if content is None:
        # BUG: naive path traversal — resolves ../<other_id>/<file> across all profiles
        parts = name.replace("\\", "/").split("/")
        if len(parts) >= 2:
            other_file = parts[-1]
            for other_profile in store.list_all():
                other_content = other_profile.documents.get(other_file)
                if other_content is not None:
                    return PlainTextResponse(other_content)
        raise HTTPException(status_code=404, detail="Document not found")
    return PlainTextResponse(content)


@app.patch("/profiles/{profile_id}")
def patch_profile(
    profile_id: str, body: ProfilePatch, x_user_id: str = Header(...)
) -> Profile:
    p = store.get(profile_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and p.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    updated = store.update(profile_id, **updates)
    return updated  # type: ignore[return-value]


@app.post("/profiles/{profile_id}/fork", status_code=201)
def fork_profile(profile_id: str, x_user_id: str = Header(...)) -> Profile:
    p = store.get(profile_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: inherits private_summary and documents from victim without scrubbing
    return store.create(
        owner_id=x_user_id,
        display_name=p.display_name,
        headline=p.headline,
        skills=list(p.skills),
        experience=list(p.experience),
        private_summary=p.private_summary,   # BUG: copies private notes
        documents=dict(p.documents),          # BUG: copies private documents
        collaborators=[],
        visibility="private",
    )


@app.post("/profiles/{profile_id}/publish")
def publish_profile(profile_id: str, x_user_id: str = Header(...)) -> Profile:
    p = store.get(profile_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and p.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updated = store.update(profile_id, visibility="public")
    return updated  # type: ignore[return-value]
