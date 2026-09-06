from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException,
    Response
)
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.ocr_parser import process_document_image
from app.models.document import DocumentTypeEnum

from app.blockchain.hash_utils import generate_document_hash
from app.blockchain.service import register_document, verify_document

from app.models.blockchain_document import BlockchainDocument
from app.core.face_matcher import extract_person_photo_for_blockchain

router = APIRouter()


# ============================================================
# Request model for blockchain registration
# ============================================================

class BlockchainRegisterRequest(BaseModel):
    document_id: int
    doc_type: str | None = None
    doc_number: str | None = None
    full_name: str | None = None
    dob: str | None = None
    gender: str | None = None
    nationality: str | None = None



@router.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:

        image_bytes = await file.read()

        # if not image_bytes:
        #     raise HTTPException(
        #         status_code=400,
        #         detail="Document image is empty"
        #     )


        ocr_result = process_document_image(image_bytes)

        if not ocr_result:
            raise HTTPException(
                status_code=400,
                detail="Unable to extract document information from the image"
            )



        doc_number = ocr_result.get("doc_number")
        doc_type = ocr_result.get("doc_type", DocumentTypeEnum.UNKNOWN)
        full_name = ocr_result.get("full_name", "Unknown")



        if (
            not doc_number
            or doc_number == "Unknown"
        ):
            raise HTTPException(
                status_code=400,
                detail="Unable to extract document number from the document"
            )



        person_photo_result = extract_person_photo_for_blockchain(image_bytes)

        if not person_photo_result["success"]:
            raise HTTPException(
                status_code=400,
                detail=person_photo_result["reason"]
            )

        person_image_bytes = person_photo_result["image"]

        existing_document = (
            db.query(BlockchainDocument)
            .filter(
                BlockchainDocument.doc_number == doc_number
            )
            .first()
        )

        if existing_document:

            existing_document.canonical_string = (
                existing_document.canonical_string
                if existing_document.canonical_string
                else ""
            )

            existing_document.person_image = person_image_bytes
            existing_document.original_document_image = image_bytes

            db.commit()
            db.refresh(existing_document)

            blockchain_document = existing_document


        else:

            blockchain_document = BlockchainDocument(
                doc_number=doc_number,

                # Canonical string will be generated during
                # blockchain registration in API 2.
                canonical_string="",

                person_image=person_image_bytes,

                original_document_image=image_bytes,

                # Blockchain registration has not happened yet.
                transaction_hash=None
            )

            db.add(blockchain_document)

            db.commit()
            db.refresh(blockchain_document)


        return {
            "success": True,

            # ID from blockchain_document_registry table
            "document_id": blockchain_document.id,

            "extracted_data": {
                "full_name": ocr_result.get("full_name"),
                "doc_number": ocr_result.get("doc_number"),
                "doc_type": ocr_result.get("doc_type"),
                "dob": ocr_result.get("dob"),
                "gender": ocr_result.get("gender"),
                "issue_date": ocr_result.get("issue_date"),
                "address": ocr_result.get("address"),
                "expiry_date": ocr_result.get("expiry_date"),
                "nationality": ocr_result.get("nationality"),
                "mrz_no": ocr_result.get("mrz_no")
            },

            "ocr_confidence": ocr_result.get(
                "ocr_confidence",
                0.0
            )
        }


    except HTTPException:
        # Don't perform any additional DB operation.
        raise


    except Exception as e:

        # Rollback in case something happened after DB interaction.
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=f"Failed to process document: {str(e)}"
        )



@router.post("/register")
async def register_document_on_blockchain(
    data: BlockchainRegisterRequest,
    db: Session = Depends(get_db)
):
    try:

        blockchain_document = (
            db.query(BlockchainDocument)
            .filter(
                BlockchainDocument.doc_number == data.doc_number
            )
            .first()
        )

        if not blockchain_document:
            raise HTTPException(
                status_code=404,
                detail="Document not found in blockchain document registry"
            )


        document_hash, canonical_string = generate_document_hash(
            doc_type=data.doc_type,
            doc_number=data.doc_number,
            full_name=data.full_name,
            dob=data.dob,
            gender=data.gender,
            nationality=data.nationality
        )


        if data.doc_number:
            blockchain_document.doc_number = data.doc_number

        blockchain_document.canonical_string = canonical_string


        result = register_document(
            document_id=str(blockchain_document.id),
            document_hash=document_hash
        )



        blockchain_document.transaction_hash = (
            result["transaction_hash"]
        )


        db.commit()
        db.refresh(blockchain_document)


        return {
            "success": True,
            "document_id": blockchain_document.id,
            "canonical_string": canonical_string,
            "document_hash": document_hash,
            "transaction_hash": result["transaction_hash"],
            "block_number": result["block_number"],
            "contract_address": result["contract_address"],
            "verify_link": f"https://sepolia.etherscan.io/address/{result["contract_address"]}"
        }


    except HTTPException:
        db.rollback()
        raise


    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.post("/check")
async def check_document_on_blockchain(
    data: BlockchainRegisterRequest,
    db: Session = Depends(get_db)
):

    try:
        blockchain_document = (
                db.query(BlockchainDocument)
                .filter(
                    BlockchainDocument.doc_number == data.doc_number
                )
                .first()
            )
        document_hash, canonical_string = generate_document_hash(
            doc_type=data.doc_type,
            doc_number=data.doc_number,
            full_name=data.full_name,
            dob=data.dob,
            gender=data.gender,
            nationality=data.nationality
        )

        result = verify_document(
            document_id=str(blockchain_document.id),
            document_hash=document_hash
        )

        return {
            "document_id": blockchain_document.id,
            "result": result,
            "transaction_link" : f"https://sepolia.etherscan.io/tx/{blockchain_document.transaction_hash}"
        }


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


def build_blockchain_data(blockchain_data):
    data_list = []

    for data in blockchain_data:
        data_list.append(
            {
                "blockchain_document_id": data.id,
                "doc_number": data.doc_number,
                "canonical_string": data.canonical_string,
                "transaction_hash": data.transaction_hash,
                "transaction_link": f"https://sepolia.etherscan.io/tx/{data.transaction_hash}"
            }
        )

    return data_list

@router.get("/get-all")
def get_all_data(
    db: Session = Depends(get_db)
):
    try:
        blockchain_data = db.query(BlockchainDocument).order_by(BlockchainDocument.created_at.desc()).all()
        return build_blockchain_data(blockchain_data)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/doc-image/{doc_id}")
async def get_person_image(
    doc_id: int,
    db: Session = Depends(get_db)
):
    document = (
        db.query(BlockchainDocument)
        .filter(BlockchainDocument.id == doc_id)
        .first()
    )

    if not document or not document.person_image:
        raise HTTPException(
            status_code=404,
            detail="doc image not found"
        )

    return Response(
        content=document.original_document_image,
        media_type="image/jpeg"
    )