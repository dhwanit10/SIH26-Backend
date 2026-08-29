from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.document import Document

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