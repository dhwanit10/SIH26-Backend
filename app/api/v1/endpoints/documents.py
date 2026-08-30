from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.document import Document
from app.models.user import User

router = APIRouter()


@router.get("/photo/{doc_id}")
async def get_document_photo(
    doc_id: int,
    db: Session = Depends(get_db)
):
    document = (
        db.query(Document)
        .filter(Document.id == doc_id)
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    if not document.doc_photo:
        raise HTTPException(
            status_code=404,
            detail="Document photo not found"
        )

    return Response(
        content=document.doc_photo,
        media_type="image/jpeg"
    )

@router.get("/person-image/{doc_id}")
async def get_person_image(
    doc_id: int,
    db: Session = Depends(get_db)
):
    document = (
        db.query(Document)
        .filter(Document.id == doc_id)
        .first()
    )

    if not document or not document.person_image:
        raise HTTPException(
            status_code=404,
            detail="Person image not found"
        )

    return Response(
        content=document.person_image,
        media_type="image/jpeg"
    )

@router.get("/user-face/{user_id}")
async def get_user_face_image(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if not user.face_image:
        raise HTTPException(
            status_code=404,
            detail="User face image not found"
        )

    return Response(
        content=user.face_image,
        media_type="image/jpeg"
    )