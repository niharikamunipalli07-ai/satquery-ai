from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

FRONTEND_DIR = BASE_DIR / "frontend"
UPLOAD_DIR = BASE_DIR / "outputs" / "uploads"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="SatQuery AI",
    description="Agentic Vision-Language Assistant for Remote Sensing",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================
# FRONTEND
# ============================================================

app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIR)),
    name="static"
)


# ============================================================
# HOME
# ============================================================

@app.get("/", include_in_schema=False)
async def home():

    return FileResponse(
        str(FRONTEND_DIR / "index.html")
    )


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "service": "SatQuery AI"
    }


# ============================================================
# REQUEST MODEL
# ============================================================

class VQARequest(BaseModel):

    filename: str
    question: str


# ============================================================
# UPLOAD IMAGE
# ============================================================

@app.post("/upload")
async def upload_image(
    file: UploadFile = File(...)
):

    # Check file type

    if not file.content_type:

        raise HTTPException(
            status_code=400,
            detail="File type could not be detected."
        )


    if not file.content_type.startswith("image/"):

        raise HTTPException(
            status_code=400,
            detail="Please upload an image file."
        )


    # Safe filename

    filename = Path(file.filename).name


    if not filename:

        raise HTTPException(
            status_code=400,
            detail="Invalid filename."
        )


    file_path = UPLOAD_DIR / filename


    # Save image

    try:

        contents = await file.read()

        with open(file_path, "wb") as f:

            f.write(contents)

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Could not save image: {str(e)}"
        )


    print(
        f"IMAGE UPLOADED: {filename}"
    )


    return {

        "success": True,

        "message":
            "Image uploaded successfully",

        "filename":
            filename

    }


# ============================================================
# VQA
# ============================================================

@app.post("/vqa")
async def vqa(
    request: VQARequest
):

    filename = request.filename

    question = request.question.strip()


    # ========================================================
    # VALIDATION
    # ========================================================

    if not filename:

        raise HTTPException(
            status_code=400,
            detail="Filename is required."
        )


    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question is required."
        )


    # ========================================================
    # SAFE IMAGE PATH
    # ========================================================

    safe_filename = Path(filename).name

    image_path = UPLOAD_DIR / safe_filename


    if not image_path.exists():

        raise HTTPException(
            status_code=404,
            detail="Uploaded image not found."
        )


    print("=" * 60)

    print("SATQUERY AI VQA REQUEST")

    print(
        "Image:",
        safe_filename
    )

    print(
        "Question:",
        question
    )

    print("=" * 60)


    # ========================================================
    # QUERY PLANNER
    # ========================================================

    category = "VQA"

    planner_reason = (
        "The question asks about visible "
        "features in the satellite image."
    )


    try:

        from backend.tools.query_planner import classify_query

        planner_result = classify_query(
            question
        )


        print(
            "PLANNER RESULT:",
            planner_result
        )


        if isinstance(
            planner_result,
            dict
        ):

            category = (

                planner_result.get(
                    "category"
                )

                or planner_result.get(
                    "type"
                )

                or planner_result.get(
                    "query_type"
                )

                or "VQA"

            )


            planner_reason = (

                planner_result.get(
                    "reason"
                )

                or planner_result.get(
                    "planner_reason"
                )

                or planner_result.get(
                    "explanation"
                )

                or planner_reason

            )


        elif isinstance(
            planner_result,
            str
        ):

            category = planner_result


    except Exception as e:

        print(
            "PLANNER ERROR:",
            str(e)
        )

        # IMPORTANT:
        # Planner failure should NOT stop VQA.

        category = "VQA"

        planner_reason = (
            "Visual question answering "
            "for satellite imagery."
        )


    # ========================================================
    # CALL VQA MODEL
    # ========================================================

    try:

        from backend.tools.vqa import ask_vqa

        vqa_result = ask_vqa(

            str(image_path),

            question

        )


        print(
            "VQA RESULT:",
            vqa_result
        )


    except Exception as e:

        print(
            "VQA EXCEPTION:",
            str(e)
        )

        raise HTTPException(

            status_code=500,

            detail=(
                "VQA processing failed: "
                + str(e)
            )

        )


    # ========================================================
    # CHECK VQA RESULT
    # ========================================================

    if not isinstance(
        vqa_result,
        dict
    ):

        answer = str(
            vqa_result
        )


    else:

        success = vqa_result.get(
            "success",
            False
        )


        # ----------------------------------------------------
        # VQA FAILED
        # ----------------------------------------------------

        if not success:

            error_message = (

                vqa_result.get(
                    "error"
                )

                or
                "VQA model failed."

            )


            print(
                "VQA FAILED:",
                error_message
            )


            raise HTTPException(

                status_code=502,

                detail=error_message

            )


        # ----------------------------------------------------
        # GET ACTUAL AI ANSWER
        # ----------------------------------------------------

        answer = (

            vqa_result.get(
                "answer"
            )

            or
            vqa_result.get(
                "content"
            )

            or
            vqa_result.get(
                "response"
            )

        )


        if not answer:

            answer = (
                "The AI did not return "
                "an answer."
            )


    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    final_response = {

        "success": True,

        "category": category,

        "planner_reason": planner_reason,

        "answer": answer,

        "filename": safe_filename

    }


    print("=" * 60)

    print(
        "FINAL SATQUERY RESPONSE:"
    )

    print(
        final_response
    )

    print("=" * 60)


    return final_response