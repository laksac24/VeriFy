from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import List
import os
import shutil
import uuid
from datetime import datetime
import zipfile
from pathlib import Path
import json

# Import your existing modules
from typing_extensions import Annotated
from typing import TypedDict
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
import base64
from dotenv import load_dotenv
from document_processor.doc_processor import DocumentProcessor
from similar_certificates.similarity import similarity_checker
from certificate_detection.detector import CertificateDetector  
from ocr_checking.ocr import ocr_checker
from database import fetch_data
import copy
from PIL import Image
import io
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI(
    title="Certificate Validation API",
    description="API for validating certificates using AI-powered processing",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins, change to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories for storing files
RESULTS_DIR = "results"
os.makedirs(RESULTS_DIR, exist_ok=True)

# Mount static files for downloads
app.mount("/downloads", StaticFiles(directory=RESULTS_DIR), name="downloads")

# Store processing results
processing_results = {}

class State(TypedDict):
    messages: Annotated[list, add_messages]
    human: list
    ecerti: list
    rejected_certi: list
    accepted_certi: list
    ocr_texts: dict

certificate_detector = CertificateDetector()
llm = ChatGroq(model="openai/gpt-oss-120b")
image_llm = ChatGroq(model="meta-llama/llama-4-maverick-17b-128e-instruct")

def resize_image_for_api(image_path, max_size=(1024, 1024), quality=85):
    """Resize and compress image to reduce file size for API calls"""
    with Image.open(image_path) as img:
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        buffer.seek(0)
        return buffer.getvalue()

def certificate_type_llm(state: State):
    """Process documents and classify certificates - Updated to work with your existing code"""
    print("Step 1: Processing documents and converting to PNG...")
    processor = DocumentProcessor()
    processed_image_path = processor.process_documents()
    
    processed_folder = "./processed_certificates"
    if not os.path.exists(processed_folder):
        error_msg = "Processed certificates folder not found."
        state["messages"].append({"role": "assistant", "content": error_msg})
        return state
    
    png_files = [f for f in os.listdir(processed_folder) if f.lower().endswith('.png')]
    
    if not png_files:
        error_msg = "No processed PNG files found."
        state["messages"].append({"role": "assistant", "content": error_msg})
        return state
    
    print(f"Found {len(png_files)} processed certificate(s) to classify")
    
    print("Step 2: Classifying all certificates...")
    classified_human = []
    classified_ecerti = []
    
    for png_file in png_files:
        image_path = os.path.join(processed_folder, png_file)
        
        print(f"Classifying: {png_file}")
        
        try:
            compressed_image_data = resize_image_for_api(image_path)
            img_b64 = base64.b64encode(compressed_image_data).decode("utf-8")
            
            if len(img_b64) > 4_000_000:
                print(f"Warning: {png_file} is still large after compression")
                compressed_image_data = resize_image_for_api(image_path, max_size=(512, 512), quality=60)
                img_b64 = base64.b64encode(compressed_image_data).decode("utf-8")
            
            # Use LLM classification for all images
            prompt = [
                {"role": "system", "content": "You are an assistant that classifies certificate type. Don't give me any extra information, just tell me whether the certificate is ecertificate or normal human clicked image of the certificate"},
                {"role": "user", "content": [
                    {"type": "text", "text": "Classify this certificate:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                ]}
            ]

            response = image_llm.invoke(prompt)
            classification = response.content
            
            if("ecertificate" in classification.lower()):
                classified_ecerti.append(png_file)
                print(f"Certificate {png_file} classified as e-certificate")
            else:
                classified_human.append(png_file)
                print(f"Certificate {png_file} classified as human-clicked")
            
            state["messages"].append({
                "role": "assistant", 
                "content": f"Certificate: {png_file} | Classification: {classification}"
            })
            
        except Exception as e:
            error_msg = f"Error processing {png_file}: {str(e)}"
            print(error_msg)
            state["messages"].append({
                "role": "assistant", 
                "content": error_msg
            })
            continue
    
    # Step 3: Perform object detection on human-clicked images
    print("Step 3: Performing object detection on human-clicked images...")
    final_human_certificates = []
    
    for human_cert in classified_human:
        image_path = os.path.join(processed_folder, human_cert)
        
        print(f"Processing {human_cert} for object detection...")
        
        cropped_paths = certificate_detector.detect_and_crop_certificates(
            image_path=image_path,
            output_folder=processed_folder
        )
        
        if cropped_paths:
            print(f"Object detection successful for {human_cert}, found {len(cropped_paths)} certificates")
            
            original_path = os.path.join(processed_folder, human_cert)
            if os.path.exists(original_path):
                os.remove(original_path)
                print(f"Removed original file: {human_cert}")
            
            # Extract just filenames from full paths
            final_human_certificates.extend([os.path.basename(path) for path in cropped_paths])
        else:
            print(f"No certificates detected in {human_cert}, keeping original")
            final_human_certificates.append(human_cert)
    
    state["human"] = final_human_certificates
    state["ecerti"] = classified_ecerti
    
    print(f"Final classification - Human: {len(final_human_certificates)}, E-certificates: {len(classified_ecerti)}")
    print(f"Human certificates: {final_human_certificates}")
    print(f"E-certificates: {classified_ecerti}")
    
    return state

def similarity_checking_llm(state: State):
    """Updated similarity checker to work with your existing code"""
    try:
        similarity_checker(state)
        return state
    except Exception as e:
        print(f"Error in similarity checking: {e}")
        # If similarity check fails, move all to rejected for safety
        state["rejected_certi"].extend(state["human"] + state["ecerti"])
        state["human"] = []
        state["ecerti"] = []
        return state

def ocr_llm(state: State):
    """Updated OCR function to work with your existing code"""
    try:
        ocr_checker(state)
        return state
    except Exception as e:
        print(f"Error in OCR processing: {e}")
        # Initialize empty OCR texts if OCR fails
        state["ocr_texts"] = {}
        return state

def validation_llm(state: State):
    """Validate certificates against database"""
    for certi, ocr_text in state["ocr_texts"].items():
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an assistant that extracts structured fields from OCR text of certificates.
            Return only valid JSON with fields: EnrollmentNo, Name, Course, CGPA"""),
            ("user", f"OCR Text: {ocr_text}")
        ])
        
        chain = prompt | llm
        response = chain.invoke({})
        try:
            ocr_data = json.loads(response.content)  
        except:
            ocr_data = {"EnrollmentNo": None, "Name": None, "Course": None, "CGPA": None}

        enrollmentNo = ocr_data.get("EnrollmentNo")
        db_record = fetch_data(str(enrollmentNo)) if enrollmentNo else None
        
        if db_record:
            db_record_copy = copy.deepcopy(db_record)
            if "_id" in db_record_copy:
                db_record_copy["_id"] = str(db_record_copy["_id"])
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a checking AI. Check whether the data in the certificate 
                and the data in database are same or not. If same then return true, else return false. 
                Have strict checking for key sections like enrollment number, but you can be slightly 
                lenient for names and other non-important sections."""),
                ("user", "database data: {db_record_copy}, certificate data: {ocr_data}")
            ])
            
            chain = prompt | llm
            output = chain.invoke({
                "db_record_copy": json.dumps(db_record_copy),
                "ocr_data": json.dumps(ocr_data)
            })
            text = output.content.lower()
            
            if "true" in text:
                if certi not in state["accepted_certi"]:
                    state["accepted_certi"].append(certi)
                if certi in state["rejected_certi"]:
                    state["rejected_certi"].remove(certi)
            else:
                if certi in state["accepted_certi"]:
                    state["accepted_certi"].remove(certi)
                if certi not in state["rejected_certi"]:
                    state["rejected_certi"].append(certi)
        else:
            if certi in state["accepted_certi"]:
                state["accepted_certi"].remove(certi)
            if certi not in state["rejected_certi"]:
                state["rejected_certi"].append(certi)
    
    return state

def selector_llm(state: State):
    """Move certificates to appropriate folders"""
    curr_path = "./processed_certificates"
    accepted_path = "./accepted_certificates"
    rejected_path = "./rejected_certificates"

    os.makedirs(accepted_path, exist_ok=True)
    os.makedirs(rejected_path, exist_ok=True)

    for certi in state["accepted_certi"]:
        src = os.path.join(curr_path, certi)
        dst = os.path.join(accepted_path, certi)
        if os.path.exists(src):
            with Image.open(src) as img:
                img.save(dst, 'PNG')

    for certi in state["rejected_certi"]:
        src = os.path.join(curr_path, certi)
        dst = os.path.join(rejected_path, certi)
        if os.path.exists(src):
            with Image.open(src) as img:
                img.save(dst, 'PNG')

    return state

def clean_directories():
    """Clean up directories before processing"""
    directories_to_clean = [
        "./certificates",
        "./processed_certificates",
        "./accepted_certificates", 
        "./rejected_certificates"
    ]
    
    for directory in directories_to_clean:
        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.makedirs(directory, exist_ok=True)

def process_certificates_pipeline(session_id: str, file_data: List[dict]):
    """Main processing pipeline"""
    try:
        # Clean directories first
        clean_directories()
        
        # Save files to certificates folder (where DocumentProcessor expects them)
        certificates_dir = "./certificates"
        for file_info in file_data:
            file_path = os.path.join(certificates_dir, file_info["filename"])
            with open(file_path, "wb") as buffer:
                buffer.write(file_info["content"])
        
        print(f"[{session_id}] Saved {len(file_data)} files to certificates directory")
        
        # Initialize state
        state = {
            "messages": [],
            "ecerti": [],
            "human": [],
            "rejected_certi": [],
            "accepted_certi": [],
            "ocr_texts": {}
        }
        
        # Build and execute the processing graph
        graph_builder = StateGraph(State)
        
        graph_builder.add_node("certificate_type_node", certificate_type_llm)
        graph_builder.add_node("similarity_checking_node", similarity_checking_llm)
        graph_builder.add_node("ocr_node", ocr_llm)
        graph_builder.add_node("validation_node", validation_llm)
        graph_builder.add_node("selector_node", selector_llm)
        
        graph_builder.add_edge(START, "certificate_type_node")
        graph_builder.add_edge("certificate_type_node", "similarity_checking_node")
        graph_builder.add_edge("similarity_checking_node", "ocr_node")
        graph_builder.add_edge("ocr_node", "validation_node")
        graph_builder.add_edge("validation_node", "selector_node")
        graph_builder.add_edge("selector_node", END)
        
        graph = graph_builder.compile()
        
        print(f"[{session_id}] Starting processing pipeline...")
        
        # Execute the pipeline
        processing_results[session_id]["status"] = "processing"
        processing_results[session_id]["step"] = "Document Processing & Classification"
        
        final_state = graph.invoke(state)
        
        # Create ZIP files for download
        accepted_zip_path = create_zip_file("./accepted_certificates", f"accepted_certificates_{session_id}.zip")
        rejected_zip_path = create_zip_file("./rejected_certificates", f"rejected_certificates_{session_id}.zip")
        
        # Update final results
        processing_results[session_id].update({
            "status": "completed",
            "step": "Completed",
            "accepted_count": len(final_state["accepted_certi"]),
            "rejected_count": len(final_state["rejected_certi"]),
            "accepted_certificates": final_state["accepted_certi"],
            "rejected_certificates": final_state["rejected_certi"],
            "accepted_download_url": f"/downloads/accepted_certificates_{session_id}.zip" if accepted_zip_path else None,
            "rejected_download_url": f"/downloads/rejected_certificates_{session_id}.zip" if rejected_zip_path else None,
            "ocr_texts": final_state["ocr_texts"]
        })
        
        print(f"[{session_id}] Processing completed successfully!")
        print(f"[{session_id}] Accepted: {len(final_state['accepted_certi'])}")
        print(f"[{session_id}] Rejected: {len(final_state['rejected_certi'])}")
        
    except Exception as e:
        print(f"[{session_id}] Error in processing: {str(e)}")
        processing_results[session_id].update({
            "status": "failed",
            "error": str(e),
            "step": "Error occurred"
        })

def create_zip_file(source_dir: str, zip_filename: str) -> str:
    """Create a ZIP file from a directory"""
    if not os.path.exists(source_dir) or not os.listdir(source_dir):
        return None
    
    zip_path = os.path.join(RESULTS_DIR, zip_filename)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arcname)
    
    return zip_path

@app.post("/upload-certificates/")
async def upload_certificates(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    """Upload multiple certificate files for processing"""
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="No files uploaded")
    
    # Validate file types and read file contents
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx'}
    file_data = []
    
    for file in files:
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not supported: {file.filename}. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Read file content immediately while the file is still open
        try:
            content = await file.read()
            file_data.append({
                "filename": file.filename,
                "content": content
            })
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading file {file.filename}: {str(e)}")
    
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    
    # Initialize processing result
    processing_results[session_id] = {
        "session_id": session_id,
        "status": "queued",
        "step": "Initializing",
        "uploaded_files": [file_info["filename"] for file_info in file_data],
        "upload_time": datetime.now().isoformat(),
        "accepted_count": 0,
        "rejected_count": 0
    }
    
    # Start background processing
    background_tasks.add_task(process_certificates_pipeline, session_id, file_data)
    
    return {
        "session_id": session_id,
        "message": f"Successfully queued {len(files)} files for processing",
        "status_url": f"/status/{session_id}",
        "uploaded_files": [file_info["filename"] for file_info in file_data]
    }

@app.get("/status/{session_id}")
async def get_processing_status(session_id: str):
    """Get the processing status for a session"""
    if session_id not in processing_results:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return processing_results[session_id]

@app.get("/results/{session_id}")
async def get_results(session_id: str):
    """Get detailed results for a completed session"""
    if session_id not in processing_results:
        raise HTTPException(status_code=404, detail="Session not found")
    
    result = processing_results[session_id]
    
    if result["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Processing not completed. Current status: {result['status']}")
    
    return {
        "session_id": session_id,
        "summary": {
            "total_files": len(result["uploaded_files"]),
            "accepted_count": result["accepted_count"],
            "rejected_count": result["rejected_count"]
        },
        "accepted_certificates": result["accepted_certificates"],
        "rejected_certificates": result["rejected_certificates"],
        "download_links": {
            "accepted": result.get("accepted_download_url"),
            "rejected": result.get("rejected_download_url")
        },
        "processing_details": {
            "upload_time": result["upload_time"],
            "ocr_texts": result.get("ocr_texts", {})
        }
    }

@app.get("/download/{session_id}/{file_type}")
async def download_results(session_id: str, file_type: str):
    """Download ZIP file of accepted or rejected certificates"""
    if session_id not in processing_results:
        raise HTTPException(status_code=404, detail="Session not found")
    
    result = processing_results[session_id]
    
    if result["status"] != "completed":
        raise HTTPException(status_code=400, detail="Processing not completed")
    
    if file_type == "accepted":
        download_url = result.get("accepted_download_url")
        filename = f"accepted_certificates_{session_id}.zip"
    elif file_type == "rejected":
        download_url = result.get("rejected_download_url")
        filename = f"rejected_certificates_{session_id}.zip"
    else:
        raise HTTPException(status_code=400, detail="Invalid file type. Use 'accepted' or 'rejected'")
    
    if not download_url:
        raise HTTPException(status_code=404, detail=f"No {file_type} certificates found")
    
    file_path = os.path.join(RESULTS_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/zip'
    )

@app.get("/sessions")
async def list_sessions():
    """List all processing sessions"""
    return {
        "sessions": [
            {
                "session_id": session_id,
                "status": details["status"],
                "upload_time": details["upload_time"],
                "file_count": len(details["uploaded_files"]),
                "accepted_count": details.get("accepted_count", 0),
                "rejected_count": details.get("rejected_count", 0)
            }
            for session_id, details in processing_results.items()
        ]
    }

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and its files"""
    if session_id not in processing_results:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Remove ZIP files
    accepted_zip = f"accepted_certificates_{session_id}.zip"
    rejected_zip = f"rejected_certificates_{session_id}.zip"
    
    for zip_file in [accepted_zip, rejected_zip]:
        zip_path = os.path.join(RESULTS_DIR, zip_file)
        if os.path.exists(zip_path):
            os.remove(zip_path)
    
    # Remove from processing results
    del processing_results[session_id]
    
    return {"message": f"Session {session_id} deleted successfully"}

@app.get("/")
async def root():
    """API information"""
    return {
        "message": "Certificate Validation API",
        "version": "1.0.0",
        "description": "Upload certificates for AI-powered validation and verification",
        "endpoints": {
            "upload": "/upload-certificates/",
            "status": "/status/{session_id}",
            "results": "/results/{session_id}",
            "download": "/download/{session_id}/{file_type}",
            "sessions": "/sessions"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)