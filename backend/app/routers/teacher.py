from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from typing import List, Annotated

from ..database import get_session
from ..models import User, UserRole, Class, Resource, Assignment, Grade, ResourceType
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
    resource_data: Resource,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    check_teacher_role(current_user)
    # Check if class exists and belongs to teacher? (Skip for now or add check)
    
    session.add(resource_data)
    session.commit()
    session.refresh(resource_data)
    
    # Trigger Agent Analysis in Background
    background_tasks.add_task(trigger_resource_analysis, resource_data.id, resource_data.url)
    
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
