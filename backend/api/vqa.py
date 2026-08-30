from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path

from backend.tools.vqa import ask_vqa

router = APIRouter()


class VQARequest(BaseModel):
    filename: str
    question: str


@router.post("/vqa")
async def visual_question_answering(request: VQARequest):

    image_path = Path("outputs/uploads") / request.filename

    if not image_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Image not found"
        )

    result = ask_vqa(
        str(image_path),
        request.question
    )

    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail=result["error"]
        )

    return result