from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from app.models.system import Session as SystemSession
from app.core.database import get_db
from app.models.verification import VerificationEntry
from app.schemas.history import HistoryResponse, HistoryItemResponse

router = APIRouter()


def build_history_response(verifications):
    data = []

    for verification in verifications:
        session = verification.session

        data.append(
            HistoryItemResponse(
                verification_id=verification.id,
                date_time_recorded=verification.date_time_recorded,
                document=verification.document,
                risks=verification.risk_entries,
                officer=verification.officer,
                session=session,
                system=session.system if session else None
            )
        )

    return HistoryResponse(
        total=len(data),
        data=data
    )


# @router.get("/history", response_model=HistoryResponse)
# async def get_history(
#     db: Session = Depends(get_db)
# ):
#     verifications = (
#         db.query(VerificationEntry)
#         .options(
#             joinedload(VerificationEntry.document),
#             joinedload(VerificationEntry.officer),
#             joinedload(VerificationEntry.risk_entries),
#             joinedload(VerificationEntry.session)
#             .joinedload("system")
#         )
#         .order_by(VerificationEntry.date_time_recorded.desc())
#         .all()
#     )

#     return build_history_response(verifications)


# @router.get("/history/officer/{officer_id}", response_model=HistoryResponse)
# async def get_officer_history(
#     officer_id: int,
#     db: Session = Depends(get_db)
# ):
#     verifications = (
#         db.query(VerificationEntry)
#         .options(
#             joinedload(VerificationEntry.document),
#             joinedload(VerificationEntry.officer),
#             joinedload(VerificationEntry.risk_entries),
#             joinedload(VerificationEntry.session)
#             .joinedload("system")
#         )
#         .filter(
#             VerificationEntry.officer_id == officer_id
#         )
#         .order_by(VerificationEntry.date_time_recorded.desc())
#         .all()
#     )

#     return build_history_response(verifications)

@router.get("/history", response_model=HistoryResponse)
async def get_history(
    officer_id: int | None = Query(None),
    db: Session = Depends(get_db)
):
    query = (
        db.query(VerificationEntry)
        .options(
            joinedload(VerificationEntry.document),
            joinedload(VerificationEntry.officer),
            joinedload(VerificationEntry.risk_entries),
            joinedload(VerificationEntry.session)
            .joinedload(SystemSession.system)
        )
    )

    if officer_id is not None:
        query = query.filter(
            VerificationEntry.officer_id == officer_id
        )

    verifications = (
        query
        .order_by(VerificationEntry.date_time_recorded.desc())
        .all()
    )

    return build_history_response(verifications)