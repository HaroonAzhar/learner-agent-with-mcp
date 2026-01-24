from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form
from ..services.gcs_service import upload_to_gcs
from sqlmodel import Session, select
from typing import List, Annotated

from ..database import get_session
from ..models import User, UserRole, Class, Resource, Assignment, Grade, ResourceType, KeyConcept, Topic, Occurrence
from ..auth import get_current_user
from ..services.agent_service import trigger_resource_analysis

router = APIRouter(
    prefix="/teacher",
    tags=["teacher"],
    responses={404: {"description": "Not found"}},
)

def check_teacher_role(user: User):
    if user.role != UserRole.TEACHER and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

@router.post("/resources", response_model=Resource)
async def add_resource(
    title: str = Form(...),
    type: ResourceType = Form(...),
    class_id: int = Form(...),
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    session: Session = Depends(get_session)
):
    check_teacher_role(current_user)
    
    # Upload to GCS
    # Generate a unique path: classes/{class_id}/resources/{filename}
    destination = f"classes/{class_id}/resources/{file.filename}"
    public_url = await upload_to_gcs(file, destination)
    
    resource_data = Resource(
        title=title,
        type=type,
        url=public_url,
        class_id=class_id,
        teacher_id=current_user.id
    )
    
    session.add(resource_data)
    session.commit()
    session.refresh(resource_data)
    
    # Trigger Agent Analysis in Background
    # Trigger Agent Analysis Synchronously (Wait for completion)
    # This ensures the user sees the spinner until analysis is actually stored.
    try:
        await trigger_resource_analysis(resource_data.id, resource_data.url)
    except Exception as e:
        # Log error but don't fail the upload entirely? 
        # Or fail it? User wants "until backend gets response".
        # If agent fails, we probably should let the upload succeed but analysis fail.
        # But for "successful storage" requirement, maybe we shouldn't error 500.
        print(f"Analysis failed: {e}")
        pass
    
    return resource_data

@router.post("/assignments", response_model=Assignment)
async def create_assignment(
    assignment_data: Assignment,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    check_teacher_role(current_user)
    session.add(assignment_data)
    session.commit()
    session.refresh(assignment_data)
    return assignment_data

@router.post("/assignments/{assignment_id}/grade/{student_id}", response_model=Grade)
async def grade_student(
    assignment_id: int,
    student_id: int,
    score: float,
    feedback: str,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    check_teacher_role(current_user)
    grade = Grade(
        assignment_id=assignment_id,
        student_id=student_id,
        score=score,
        feedback=feedback
    )
    session.add(grade)
    session.commit()
    session.refresh(grade)
    return grade

@router.get("/classes", response_model=List[Class])
async def list_teacher_classes(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    check_teacher_role(current_user)
    if current_user.role == UserRole.ADMIN:
        # Admins can see all classes? Or just return all for now to be safe/useful
        return session.exec(select(Class)).all()
    
    # Return classes where teacher_id matches
    return session.exec(select(Class).where(Class.teacher_id == current_user.id)).all()

@router.get("/classes/{class_id}/resources", response_model=List[Resource])
async def list_class_resources(
    class_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    check_teacher_role(current_user)
    resources = session.exec(select(Resource).where(Resource.class_id == class_id)).all()
    return resources
@router.get("/resources/{resource_id}/analysis")
async def get_resource_analysis(
    resource_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    check_teacher_role(current_user)
    
    # Get Resource
    resource = session.get(Resource, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
        
    # Get Topics associated with this resource via Occurrences
    # We want to return { resource: ..., topics: [ {name: ..., occurrences: [...] } ] }
    # Let's verify if topics are linked.
    # Logic: Select Topic where Topic.id in (select topic_id from Occurrence where resource_id = X)
    
    from ..models import Topic, Occurrence, KeyConcept
    
    # Fetch all occurrences for this resource, loading topic and key_concepts
    occurrences = session.exec(
        select(Occurrence)
        .where(Occurrence.resource_id == resource_id)
    ).all()
    
    # Group by Topic
    topics_map = {}
    for occ in occurrences:
        # Manually load topic if not lazy loaded? SQLModel relationships are lazy by default? 
        # We need to ensure we have the topic.
        # It's better to use explicit join or .options(selectinload(...))
        # But for MVP loop is okay if volume is low.
        
        # Note: session.get(Topic, occ.topic_id) might be needed if relationship not loaded.
        # Let's assume lazy loading works or we re-fetch.
        
        # Actually, let's just return the raw occurrences and let frontend group?
        # Or construct a nice JSON.
        
        # Explicitly fetching to avoid N+1 if possible, but simplest is:
        topic = session.get(Topic, occ.topic_id)
        if not topic: continue
        
        if topic.id not in topics_map:
            topics_map[topic.id] = {
                "id": topic.id,
                "name": topic.name,
                "concepts": [] # We called it "occurrences" in the prompt, but effectively key concepts are time-bound?
                # Wait, Occurrence HAS KeyConcepts.
                # So Topic -> Occurrence -> KeyConcepts.
            }
            
        # Get KeyConcepts for this occurrence
        key_concepts = session.exec(select(KeyConcept).where(KeyConcept.occurrence_id == occ.id)).all()
        
        # Add to the structure. 
        # Frontend expects: Topic -> Concepts (with timestamps).
        # Our model: Occurrence (with Topic) -> KeyConcepts.
        # So multiple concepts in one occurrence share the same "time" roughly?
        # But KeyConcept has timestamp_start.
        
        for kc in key_concepts:
            topics_map[topic.id]["concepts"].append({
                "id": kc.id,
                "name": kc.name,
                "description": kc.description,
                "timestamp": kc.timestamp_start
            })

    return {
        "resource": resource,
        "topics": list(topics_map.values())
    }

@router.put("/key-concepts/{concept_id}", response_model=KeyConcept)
async def update_key_concept(
    concept_id: int,
    concept_data: KeyConcept,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    check_teacher_role(current_user)
    concept = session.get(KeyConcept, concept_id)
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")
        
    concept.name = concept_data.name
    concept.description = concept_data.description
    # Update other fields if needed
    
    session.add(concept)
    session.commit()
    session.refresh(concept)
    return concept
