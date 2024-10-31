import requests
from fastapi import FastAPI, HTTPException, Request, Form, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from typing import Optional
from datetime import datetime, timezone, timedelta

# db helper in database.py
from database import SessionLocal, Paper
# doi helper 
from doi import fetch_paper_details, create_paper

app = FastAPI()

# Mount static directory for CSS and JS files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# db session for storage
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Homepage
@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    db: Session = Depends(get_db),
    sort_by: Optional[str] = Query("votes", enum=["published", "votes"]),
    page: int = Query(1, ge=1),
    range: int = Query(14, ge=1)
):
    today = datetime.now(timezone.utc)
    # Calculate the interval length in days based on the selected range
    end_date = today - timedelta(days=(page - 1) * range)
    start_date = end_date - timedelta(days=range)

    # Query papers within the specified date range and sort order
    query = db.query(Paper).filter(Paper.published >= start_date, Paper.published < end_date)
    if sort_by == "votes":
        query = query.order_by(Paper.votes.desc())
    else:
        query = query.order_by(Paper.published.desc())
    
    papers = query.all()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "papers": papers,
        "page": page,
        "range": range,
        "sort_by": sort_by,
        "start_date": start_date,
        "end_date": end_date,
    })

# Endpoint to add a paper by DOI
@app.post("/add-paper/")
async def add_paper(doi: str = Form(...), added_by: str = Form(...), db: Session = Depends(get_db)):
    paper_details = fetch_paper_details(doi)

    # Check if paper already exists in the database
    if db.query(Paper).filter(Paper.doi == paper_details['doi']).first():
        raise HTTPException(status_code=400, detail="Paper already exists.")

    paper = create_paper(paper_details, added_by)
    db.add(paper)
    db.commit()
    return {"message": "Paper added successfully.", "paper": paper}

# Endpoint to upvote a paper
@app.post("/upvote/")
async def upvote_paper(doi: str = Form(...), db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.doi == doi).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")
    paper.votes += 1
    db.commit()
    return {"message": "Vote recorded successfully.", "votes": paper.votes}

# Report page, simple UI to get top x paper between two dates
@app.get("/report/", response_class=HTMLResponse)
async def report_page(request: Request):
    # Render the report page with date selection form
    return templates.TemplateResponse("report.html", {"request": request})

# Endpoint to gather papers for a report
@app.post("/report/", response_class=HTMLResponse)
async def generate_report(
    request: Request,
    start_date: str = Form(...),
    end_date: str = Form(...),
    x: int = Form(3),
    db: Session = Depends(get_db)
):
    # Parse start and end dates
    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # Include the end date fully
    except ValueError:
        return templates.TemplateResponse("report.html", {"request": request, "error": "Invalid date format"})

    # Query top `x` papers within date range ordered by votes
    papers = (
        db.query(Paper)
        .filter(Paper.created_at >= start_date, Paper.created_at < end_date)
        .order_by(Paper.votes.desc())
        .limit(x)
        .all()
    )

    return templates.TemplateResponse("report.html", {
        "request": request,
        "papers": papers,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "x": x
    })
