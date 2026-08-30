from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path

from backend.api.upload import upload_image
from backend.tools.vqa import ask_vqa


# ==========================================
# CREATE FASTAPI APPLICATION
# ==========================================

app = FastAPI(
    title="SatQuery AI",
    description="Agentic Vision-Language Assistant for Remote Sensing",
    version="1.0.0"
)


# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# HOME
# ==========================================

@app.get("/")
def home():
    return {
        "message": "Welcome to SatQuery AI",
        "status": "Backend is running"
    }


# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ==========================================
# IMAGE UPLOAD
# ==========================================

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    return await upload_image(file)


# ==========================================
# VQA REQUEST MODEL
# ==========================================

class VQARequest(BaseModel):
    filename: str
    question: str


# ==========================================
# MAIN AI QUERY ENDPOINT
# ==========================================

@app.post("/vqa")
async def vqa(request: VQARequest):

    # --------------------------------------
    # Find uploaded image
    # --------------------------------------

    image_path = Path("outputs/uploads") / request.filename

    if not image_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Image not found"
        )


    # --------------------------------------
    # STEP 1: QUERY PLANNER
    # --------------------------------------

    from backend.tools.query_planner import classify_query

    question_lower = request.question.lower()


    # --------------------------------------
    # Keywords
    # --------------------------------------

    visual_words = [
        "visible",
        "see",
        "shown",
        "buildings",
        "building",
        "roads",
        "road",
        "vegetation",
        "green areas",
        "stadium",
        "sports facilities",
        "objects",
        "describe"
    ]

    geo_words = [
        "latitude",
        "longitude",
        "coordinates",
        "gps",
        "geolocation",
        "geographic coordinates",
        "location",
        "city",
        "country",
        "address"
    ]

    analysis_words = [
        "analyze",
        "analysis",
        "urban development",
        "land-use",
        "land use",
        "change detection",
        "risk assessment",
        "pattern"
    ]


    # --------------------------------------
    # ROUTE QUESTION
    # --------------------------------------

    if any(word in question_lower for word in visual_words):

        planner_result = {
            "success": True,
            "category": "VQA",
            "reason": "The question asks about visually observable features."
        }

    elif any(word in question_lower for word in geo_words):

        planner_result = {
            "success": True,
            "category": "GEO",
            "reason": "The question asks for geographic information."
        }

    elif any(word in question_lower for word in analysis_words):

        planner_result = {
            "success": True,
            "category": "ANALYSIS",
            "reason": "The question asks for deeper image analysis."
        }

    else:

        planner_result = classify_query(
            request.question
        )


    # --------------------------------------
    # Check planner
    # --------------------------------------

    if not planner_result.get("success", False):

        raise HTTPException(
            status_code=500,
            detail=planner_result.get(
                "error",
                "Query planning failed"
            )
        )


    category = planner_result.get(
        "category",
        "VQA"
    )


    # ======================================
    # STEP 2: VQA AGENT
    # ======================================

    if category == "VQA":

        try:

            result = ask_vqa(
                str(image_path),
                request.question
            )

        except Exception as e:

            raise HTTPException(
                status_code=500,
                detail=str(e)
            )


        if not result.get("success", False):

            raise HTTPException(
                status_code=500,
                detail=result.get(
                    "error",
                    "VQA processing failed"
                )
            )


        return {
            "success": True,
            "category": "VQA",
            "planner_reason": planner_result.get(
                "reason",
                ""
            ),
            "answer": result.get(
                "answer",
                ""
            )
        }


    # ======================================
    # STEP 3: GEO AGENT
    # ======================================

    if category == "GEO":

        try:

            from backend.tools.geo_agent import (
                get_geo_information
            )

            geo_result = get_geo_information(
                str(image_path)
            )

        except Exception as e:

            raise HTTPException(
                status_code=500,
                detail=str(e)
            )


        if not geo_result.get("success", False):

            raise HTTPException(
                status_code=500,
                detail=geo_result.get(
                    "error",
                    "GEO analysis failed"
                )
            )


        return {
            "success": True,
            "category": "GEO",
            "planner_reason": planner_result.get(
                "reason",
                ""
            ),
            "geo_information": geo_result
        }


    # ======================================
    # STEP 4: ANALYSIS AGENT
    # ======================================

    if category == "ANALYSIS":

        try:

            from backend.tools.analysis_agent import (
                analyze_image
            )

            analysis_result = analyze_image(
                str(image_path),
                request.question
            )

        except Exception as e:

            raise HTTPException(
                status_code=500,
                detail=str(e)
            )


        if not analysis_result.get(
            "success",
            False
        ):

            raise HTTPException(
                status_code=500,
                detail=analysis_result.get(
                    "error",
                    "Analysis failed"
                )
            )


        return {
            "success": True,
            "category": "ANALYSIS",
            "planner_reason": planner_result.get(
                "reason",
                ""
            ),
            "answer": analysis_result.get(
                "answer",
                ""
            )
        }


    # ======================================
    # UNKNOWN CATEGORY
    # ======================================

    return {
        "success": False,
        "error": "Unknown query category"
    }


# ==========================================
# SERVE FRONTEND
# ==========================================

frontend_path = Path("frontend")

if frontend_path.exists():

    app.mount(
        "/frontend",
        StaticFiles(
            directory="frontend",
            html=True
        ),
        name="frontend"
    )