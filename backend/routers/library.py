from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from .. import models, schemas, database, auth, security

router = APIRouter(
    prefix="/library",
    tags=["library"]
)

# --- Books Endpoints ---

@router.get("/books", response_model=List[schemas.BookResponse])
def get_books(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    query = db.query(models.Book)
    if current_user.school_id:
        query = query.filter(models.Book.school_id == current_user.school_id)
        
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (models.Book.title.ilike(search_filter)) | 
            (models.Book.author.ilike(search_filter)) |
            (models.Book.isbn.ilike(search_filter))
        )
        
    return query.offset(skip).limit(limit).all()

@router.post("/books", response_model=schemas.BookResponse)
def create_book(
    book: schemas.BookCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # If user is school admin, assign school_id automatically
    school_id = current_user.school_id
    if not school_id and book.school_id:
        # Allow Super Admin to set school_id
        school_id = book.school_id
        
    new_book = models.Book(
        **book.model_dump(exclude={"school_id"}), 
        school_id=school_id,
        available_quantity=book.quantity # Initially available = quantity
    )
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book

@router.put("/books/{book_id}", response_model=schemas.BookResponse)
def update_book(
    book_id: int,
    book_update: schemas.BookCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    query = db.query(models.Book).filter(models.Book.id == book_id)
    if current_user.school_id:
        query = query.filter(models.Book.school_id == current_user.school_id)
        
    db_book = query.first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
        
    # Logic to adjust available quantity if total quantity changes?
    # For MVP, simple update. Complex logic requires checking active loans.
    # Let's assume quantity change adjustment is manual or basic
    quantity_diff = book_update.quantity - db_book.quantity
    
    db_book.title = book_update.title
    db_book.author = book_update.author
    db_book.isbn = book_update.isbn
    db_book.category = book_update.category
    db_book.location = book_update.location
    db_book.quantity = book_update.quantity
    db_book.available_quantity += quantity_diff # Adjust available by the difference
    
    db.commit()
    db.refresh(db_book)
    return db_book

# --- Loan Endpoints ---

@router.get("/loans", response_model=List[schemas.LoanResponse])
def get_loans(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None, # 'active', 'overdue'
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    query = db.query(models.Loan).join(models.Book)
    
    if current_user.school_id:
        query = query.filter(models.Book.school_id == current_user.school_id)
        
    if status == "active":
        query = query.filter(models.Loan.status == models.LoanStatus.ACTIVE)
    elif status == "overdue":
        query = query.filter(models.Loan.status == models.LoanStatus.OVERDUE)
    elif status == "returned":
         query = query.filter(models.Loan.status == models.LoanStatus.RETURNED)
         
    loans = query.order_by(models.Loan.issue_date.desc()).offset(skip).limit(limit).all()
    
    # Enrich response with names manually since Pydantic relationship mapping can be tricky with limited schemas
    results = []
    for loan in loans:
        resp = schemas.LoanResponse.model_validate(loan)
        resp.book_title = loan.book.title
        resp.user_full_name = loan.user.full_name
        results.append(resp)
        
    return results

@router.post("/loans", response_model=schemas.LoanResponse)
def issue_book(
    loan: schemas.LoanCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # 1. Check Book Availability
    book = db.query(models.Book).filter(models.Book.id == loan.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
        
    if current_user.school_id and book.school_id != current_user.school_id:
         raise HTTPException(status_code=403, detail="Not authorized for this school")
         
    if book.available_quantity <= 0:
        raise HTTPException(status_code=400, detail="Book is currently unavailable")
        
    # 2. Check User validity (optional implementation)
    
    # 3. Create Loan
    new_loan = models.Loan(
        book_id=loan.book_id,
        user_id=loan.user_id,
        due_date=loan.due_date,
        notes=loan.notes,
        status=models.LoanStatus.ACTIVE
    )
    
    # 4. Decrease book Inventory
    book.available_quantity -= 1
    
    db.add(new_loan)
    db.commit()
    db.refresh(new_loan)
    
    # Enrich response
    resp = schemas.LoanResponse.model_validate(new_loan)
    resp.book_title = book.title
    borrower = db.query(models.User).filter(models.User.id == loan.user_id).first()
    resp.user_full_name = borrower.full_name if borrower else "Unknown"
    
    return resp

@router.put("/loans/{loan_id}/return", response_model=schemas.LoanResponse)
def return_book(
    loan_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    loan = db.query(models.Loan).filter(models.Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
        
    if loan.status == models.LoanStatus.RETURNED:
        raise HTTPException(status_code=400, detail="Book already returned")
        
    # Update Loan
    loan.status = models.LoanStatus.RETURNED
    loan.return_date = datetime.now()
    
    # Increase Inventory
    book = db.query(models.Book).filter(models.Book.id == loan.book_id).first()
    if book:
        book.available_quantity += 1
        
    db.commit()
    db.refresh(loan)
    
    resp = schemas.LoanResponse.model_validate(loan)
    if book: resp.book_title = book.title
    resp.user_full_name = loan.user.full_name
    
    return resp
