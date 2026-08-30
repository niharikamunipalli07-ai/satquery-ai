from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path

from backend.api.upload import upload_image
from backend.tools.vqa import ask_vqa


# ==========================================
# Create FastAPI application
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
# Home
# ==========================================

@app.get("/")
def home():
    frontend_file = Path("frontend/index.html")

    if frontend_file.exists():
        return FileResponse(frontend_file)

    return {
        "message": "Welcome to SatQuery AI",
        "status": "Backend is running"
    }


# ==========================================
# Health Check
# ==========================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ==========================================
# Image Upload
# ==========================================

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    return await upload_image(file)


# ==========================================
# VQA Request Model
# ==========================================

class VQARequest(BaseModel):
    filename: str
    question: str


# ==========================================
# Main AI Query Endpoint
# ==========================================

@app.post("/vqa")
async def vqa(request: VQARequest):

    # ======================================
    # Find uploaded image
    # ======================================

    image_path = Path("outputs/uploads") / request.filename

    if not image_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Image not found"
        )

    # ======================================
    # STEP 1: QUERY PLANNER
    # ======================================

    from backend.tools.query_planner import classify_query

    question_lower = request.question.lower()

    visual_words = [
        "visible",
        "see",
        "shown",
        "image",
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

    # ======================================
    # IMPORTANT:
    # Check ANALYSIS first
    # ======================================

    if any(word in question_lower for word in analysis_words):

        planner_result = {
            "success": True,
            "category": "ANALYSIS",
            "reason": "The question asks for deeper image analysis."
        }

    elif any(word in question_lower for word in geo_words):

        planner_result = {
            "success": True,
            "category": "GEO",
            "reason": "The question asks for geographic information."
        }

    elif any(word in question_lower for word in visual_words):

        planner_result = {
            "success": True,
            "category": "VQA",
            "reason": "The question asks about visually observable features."
        }

    else:

        planner_result = classify_query(
            request.question
        )

    # ======================================
    # Check planner result
    # ======================================

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
    ).upper()


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

        if not result.get(
            "success",
            False
        ):

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

        if not geo_result.get(
            "success",
            False
        ):

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
            "answer": geo_result.get(
                "answer",
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
    # Unknown category
    # ======================================

    return {
        "success": False,
        "category": category,
        "error": "Unknown query category"
    }


# ==========================================
# Serve Frontend Static Files
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