from fastapi import FastAPI, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime
import models, schemas
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return FileResponse("templates/index.html")

@app.post("/api/tickets")
def create_ticket(ticket: schemas.TicketCreate, db: Session = Depends(get_db)):
    count = db.query(models.Ticket).count() + 1
    ticket_id = f"TKT-{count:03d}"

    new_ticket = models.Ticket(
        ticket_id=ticket_id,
        customer_name=ticket.customer_name,
        customer_email=ticket.customer_email,
        subject=ticket.subject,
        description=ticket.description,
        status="Open",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return new_ticket

@app.get("/api/tickets")
def get_tickets(search: str = "", status: str = "", db: Session = Depends(get_db)):
    query = db.query(models.Ticket)

    if search:
        query = query.filter(
            models.Ticket.ticket_id.contains(search) |
            models.Ticket.customer_name.contains(search) |
            models.Ticket.customer_email.contains(search) |
            models.Ticket.subject.contains(search) |
            models.Ticket.description.contains(search)
        )

    if status:
        query = query.filter(models.Ticket.status == status)

    return query.all()

@app.get("/api/tickets/{ticket_id}")
def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(models.Ticket).filter(models.Ticket.ticket_id == ticket_id).first()

    if not ticket:
        return {"error": "Ticket not found"}

    return ticket

@app.delete("/api/tickets/{ticket_id}")
def delete_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(models.Ticket).filter(models.Ticket.ticket_id == ticket_id).first()

    if not ticket:
        return {"error": "Ticket not found"}

    db.delete(ticket)
    db.commit()

    return {"message": "Ticket deleted"}

@app.put("/api/tickets/{ticket_id}")
def update_ticket(ticket_id: str, data: schemas.TicketUpdate, db: Session = Depends(get_db)):
    ticket = db.query(models.Ticket).filter(models.Ticket.ticket_id == ticket_id).first()

    if not ticket:
        return {"error": "Ticket not found"}

    ticket.status = data.status
    ticket.updated_at = datetime.utcnow()
    db.commit()

    return {"success": True, "updated_at": ticket.updated_at}