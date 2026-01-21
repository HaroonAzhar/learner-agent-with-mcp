from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Annotated

from ..database import get_session
from ..models import User, UserRole, Class, ClassEnrollment
from ..auth import get_current_user

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "Not found"}},
)

def check_admin_role(user: User):
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

@router.post("/users", response_model=User)
async def create_user(
    user_data: User,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    check_admin_role(current_user)
    # Check existing
    if session.exec(select(User).where(User.username == user_data.username)).first():
        raise HTTPException(status_code=400, detail="Username exists")
        
    # In real app, hash password here. 
    # Assuming user_data.password_hash contains the plain password to be hashed as per previous pattern
    # Use auth.get_password_hash (need to import it)
    from ..auth import get_password_hash
    user_data.password_hash = get_password_hash(user_data.password_hash)
    
    session.add(user_data)
    session.commit()
    session.refresh(user_data)
    return user_data

@router.get("/users", response_model=List[User])
async def list_users(
    current_user: Annotated[User, Depends(get_current_user)],
    role: UserRole = None,
    session: Session = Depends(get_session)
):
    check_admin_role(current_user)
    query = select(User)
    if role:
        query = query.where(User.role == role)
    return session.exec(query).all()

@router.post("/classes", response_model=Class)
async def create_class(
    class_data: Class,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    check_admin_role(current_user)
    session.add(class_data)
    session.commit()
    session.refresh(class_data)
    return class_data

@router.post("/classes/{class_id}/enroll", response_model=ClassEnrollment)
async def enroll_student(
    class_id: int,
    student_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session = Depends(get_session)
):
    check_admin_role(current_user)
    enrollment = ClassEnrollment(class_id=class_id, student_id=student_id)
    session.add(enrollment)
    session.commit()
    session.refresh(enrollment)
    return enrollment
