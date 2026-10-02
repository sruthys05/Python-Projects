from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket import Ticket
from app.schemas.ticket import TicketCreate
from app.services.routing_service import route_ticket


def create_ticket(db: Session, ticket_data: TicketCreate) -> Ticket:
    classification = route_ticket(f"{ticket_data.title}\n{ticket_data.description}")
    ticket = Ticket(
        title=ticket_data.title,
        description=ticket_data.description,
        category=classification["category"],
        priority=classification["priority"],
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def list_tickets(db: Session, limit: int = 100, offset: int = 0) -> list[Ticket]:
    statement = select(Ticket).order_by(Ticket.created_at.desc()).offset(offset).limit(limit)
    return list(db.scalars(statement))


def get_ticket(db: Session, ticket_id: int) -> Ticket | None:
    return db.get(Ticket, ticket_id)
