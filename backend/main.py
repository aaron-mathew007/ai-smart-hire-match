from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import openai
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import os
from typing import List
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database models
class Resume(Base):
    __tablename__ = "resumes"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)

class JobDescription(Base):
    __tablename__ = "job_descriptions"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)

class MatchScore(Base):
    __tablename__ = "match_scores"
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer)
    job_id = Column(Integer)
    score = Column(Float)

Base.metadata.create_all(bind=engine)

# Pydantic models
class ResumeIn(BaseModel):
    content: str

class JobDescriptionIn(BaseModel):
    content: str

class MatchRequest(BaseModel):
    resume_id: int
    job_id: int

class MatchResponse(BaseModel):
    score: float

# FastAPI app
app = FastAPI()

# OpenAI API setup
openai.api_key = os.getenv("OPENAI_API_KEY")

# Helper function to get embeddings
def get_embedding(text: str) -> List[float]:
    response = openai.Embedding.create(input=text, model="text-embedding-ada-002")
    return response["data"][0]["embedding"]

# Endpoint to parse resume
@app.post("/parse-resume")
async def parse_resume(resume: UploadFile = File(...)):
    content = await resume.read()
    content_str = content.decode("utf-8")
    # Use OpenAI to extract key information
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Extract skills and experience from this resume: {content_str}",
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
    )
    parsed_data = response.choices[0].text
    # Save to database
    db = SessionLocal()
    try:
        new_resume = Resume(content=content_str)
        db.add(new_resume)
        db.commit()
        db.refresh(new_resume)
        return {"resume_id": new_resume.id, "parsed_data": parsed_data}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# Endpoint to analyze job description
@app.post("/analyze-jd")
async def analyze_jd(jd: UploadFile = File(...)):
    content = await jd.read()
    content_str = content.decode("utf-8")
    # Use OpenAI to extract key requirements
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Extract key requirements from this job description: {content_str}",
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
    )
    analyzed_data = response.choices[0].text
    # Save to database
    db = SessionLocal()
    try:
        new_jd = JobDescription(content=content_str)
        db.add(new_jd)
        db.commit()
        db.refresh(new_jd)
        return {"job_id": new_jd.id, "analyzed_data": analyzed_data}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# Endpoint to compute match score
@app.post("/match", response_model=MatchResponse)
async def compute_match(request: MatchRequest):
    db = SessionLocal()
    try:
        resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
        job = db.query(JobDescription).filter(JobDescription.id == request.job_id).first()
        if not resume or not job:
            raise HTTPException(status_code=404, detail="Resume or Job Description not found")
        
        # Get embeddings
        resume_emb = get_embedding(resume.content)
        job_emb = get_embedding(job.content)
        
        # Compute cosine similarity
        score = cosine_similarity([resume_emb], [job_emb])[0][0]
        
        # Save match score
        new_match = MatchScore(resume_id=request.resume_id, job_id=request.job_id, score=score)
        db.add(new_match)
        db.commit()
        db.refresh(new_match)
        
        return {"score": score}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
