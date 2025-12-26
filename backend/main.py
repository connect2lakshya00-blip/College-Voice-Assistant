from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import re
import os
import secrets
from datetime import datetime

app = FastAPI(title="EduConnect API", version="3.0")

# CORS (allow frontend requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Serve Index (Catch-all for root)
@app.get("/")
async def read_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

# Serve Admin
@app.get("/admin")
async def read_admin():
    return FileResponse(os.path.join(FRONTEND_DIR, "admin.html"))

# Mount Static Files (CSS, JS, Images)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# Load JSON database
BASE = os.path.dirname(__file__)
DATA_FILE = os.path.join(BASE, "student_data.json")

def load_data():
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

DATA = load_data()


# =============================================
# PYDANTIC MODELS
# =============================================

class UserQuery(BaseModel):
    text: str
    user: str = "lakshya sharma"

class StudentBasic(BaseModel):
    name: str
    email: str
    phone: str
    course: str
    year: str
    semester: str
    section: str
    roll_no: str
    dob: str
    address: str
    cgpa: float = 0.0

class AttendanceUpdate(BaseModel):
    student_key: str
    subject: str
    present: int
    total: int

class GradeUpdate(BaseModel):
    student_key: str
    subject: str
    grade: str
    marks: int
    credits: int

class ExamUpdate(BaseModel):
    student_key: str
    subject: str
    date: str
    time: str
    venue: str
    exam_type: str
    days_left: int

class FeeUpdate(BaseModel):
    student_key: str
    total_fee: int
    paid: int
    due_date: str

class NoticeCreate(BaseModel):
    title: str
    content: str
    notice_type: str  # urgent, warning, info
    author: str

class CourseCreate(BaseModel):
    code: str
    name: str
    credits: int
    professor: str
    schedule: str

class LibraryBookAdd(BaseModel):
    student_key: str
    title: str
    author: str
    issue_date: str
    due_date: str

class MenuAdd(BaseModel):
    item: str
    price: int
    category: str

class OrderStatusUpdate(BaseModel):
    student_key: str
    order_id: str
    status: str


class PlacementCreate(BaseModel):
    company: str
    role: str
    ctc: str
    date: str
    deadline: str
    eligibility: str

class EventCreate(BaseModel):
    name: str
    organizer: str
    date: str
    venue: str
    description: str

class AppointmentBook(BaseModel):
    student_key: str
    professor_name: str
    date: str
    time: str
    purpose: str

class CafeteriaOrder(BaseModel):
    student_key: str
    items: List[str]
    total_amount: int

class AdminLogin(BaseModel):
    username: str
    password: str


# =============================================
# ADMIN AUTHENTICATION
# =============================================

# Admin credentials (In production, use hashed passwords and proper auth)
ADMIN_CREDENTIALS = {
    "admin": "admin123"
}

# Active sessions (in-memory, for demo purposes)
admin_sessions = {}

@app.post("/api/admin/login")
def admin_login(credentials: AdminLogin):
    """Admin login endpoint"""
    if credentials.username in ADMIN_CREDENTIALS:
        if ADMIN_CREDENTIALS[credentials.username] == credentials.password:
            # Generate a simple session token
            token = secrets.token_hex(16)
            admin_sessions[token] = {
                "username": credentials.username,
                "login_time": datetime.now().isoformat()
            }
            return {
                "success": True,
                "message": "Login successful",
                "token": token,
                "username": credentials.username
            }
    
    raise HTTPException(status_code=401, detail="Invalid username or password")


@app.post("/api/admin/logout")
def admin_logout(token: str = ""):
    """Admin logout endpoint"""
    if token in admin_sessions:
        del admin_sessions[token]
    return {"success": True, "message": "Logged out successfully"}


@app.get("/api/admin/verify")
def verify_admin(token: str = ""):
    """Verify admin session"""
    if token in admin_sessions:
        return {"valid": True, "username": admin_sessions[token]["username"]}
    return {"valid": False}


# =============================================
# TEACHER ADMIN ENDPOINTS
# =============================================

# --- STUDENTS CRUD ---

@app.get("/api/admin/students")
def get_all_students():
    """Get list of all students"""
    students = []
    for key, student in DATA["students"].items():
        students.append({
            "key": key,
            "name": student["name"],
            "roll_no": student["roll_no"],
            "email": student["email"],
            "course": student["course"],
            "year": student["year"],
            "cgpa": student["cgpa"],
            "attendance": student["attendance"]["overall_percent"]
        })
    return {"students": students, "total": len(students)}


@app.get("/api/admin/student/{student_key}")
def get_student(student_key: str):
    """Get complete details of a student"""
    key = student_key.lower()
    if key not in DATA["students"]:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"student": DATA["students"][key], "key": key}


@app.post("/api/admin/student")
def create_student(student: StudentBasic):
    """Add a new student"""
    key = student.name.lower()
    if key in DATA["students"]:
        raise HTTPException(status_code=400, detail="Student already exists")
    
    # Create complete student record
    DATA["students"][key] = {
        "id": f"CSE{datetime.now().strftime('%Y')}A{len(DATA['students'])+1:02d}",
        "name": student.name,
        "email": student.email,
        "phone": student.phone,
        "course": student.course,
        "year": student.year,
        "semester": student.semester,
        "section": student.section,
        "roll_no": student.roll_no,
        "dob": student.dob,
        "address": student.address,
        "cgpa": student.cgpa,
        "attendance": {
            "overall_percent": 0,
            "total_classes": 0,
            "present": 0,
            "absent": 0,
            "subjects": {}
        },
        "grades": {
            "current_semester": {},
            "sgpa": 0.0,
            "cgpa": student.cgpa,
            "total_credits": 0,
            "earned_credits": 0
        },
        "exams": [],
        "library": {
            "books_borrowed": [],
            "total_borrowed": 0,
            "total_fine": 0,
            "max_books": 5
        },
        "fees": {
            "total_fee": 0,
            "paid": 0,
            "pending": 0,
            "due_date": "",
            "payment_history": [],
            "breakdown": {}
        },
        "courses": []
    }
    
    save_data(DATA)
    return {"message": f"Student {student.name} added successfully", "key": key}


@app.put("/api/admin/student/{student_key}")
def update_student(student_key: str, student: StudentBasic):
    """Update student basic info"""
    key = student_key.lower()
    if key not in DATA["students"]:
        raise HTTPException(status_code=404, detail="Student not found")
    
    DATA["students"][key].update({
        "name": student.name,
        "email": student.email,
        "phone": student.phone,
        "course": student.course,
        "year": student.year,
        "semester": student.semester,
        "section": student.section,
        "roll_no": student.roll_no,
        "dob": student.dob,
        "address": student.address,
        "cgpa": student.cgpa
    })
    
    save_data(DATA)
    return {"message": f"Student {student.name} updated successfully"}


@app.delete("/api/admin/student/{student_key}")
def delete_student(student_key: str):
    """Delete a student"""
    key = student_key.lower()
    if key not in DATA["students"]:
        raise HTTPException(status_code=404, detail="Student not found")
    
    name = DATA["students"][key]["name"]
    del DATA["students"][key]
    save_data(DATA)
    return {"message": f"Student {name} deleted successfully"}


# --- ATTENDANCE ---

@app.post("/api/admin/attendance")
def update_attendance(att: AttendanceUpdate):
    """Update student attendance for a subject"""
    key = att.student_key.lower()
    if key not in DATA["students"]:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student = DATA["students"][key]
    percent = round((att.present / att.total) * 100) if att.total > 0 else 0
    
    student["attendance"]["subjects"][att.subject] = {
        "present": att.present,
        "total": att.total,
        "percent": percent
    }
    
    # Recalculate overall
    subjects = student["attendance"]["subjects"]
    total_present = sum(s["present"] for s in subjects.values())
    total_classes = sum(s["total"] for s in subjects.values())
    
    student["attendance"]["present"] = total_present
    student["attendance"]["total_classes"] = total_classes
    student["attendance"]["absent"] = total_classes - total_present
    student["attendance"]["overall_percent"] = round((total_present / total_classes) * 100) if total_classes > 0 else 0
    
    save_data(DATA)
    return {"message": f"Attendance updated for {att.subject}"}


@app.delete("/api/admin/attendance/{student_key}/{subject}")
def delete_attendance(student_key: str, subject: str):
    """Delete attendance for a subject"""
    key = student_key.lower()
    if key not in DATA["students"]:
        raise HTTPException(status_code=404, detail="Student not found")
    
    if subject in DATA["students"][key]["attendance"]["subjects"]:
        del DATA["students"][key]["attendance"]["subjects"][subject]
        save_data(DATA)
    
    return {"message": f"Attendance deleted for {subject}"}


# --- GRADES ---

@app.post("/api/admin/grade")
def update_grade(grade: GradeUpdate):
    """Add/Update student grade for a subject"""
    key = grade.student_key.lower()
    if key not in DATA["students"]:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student = DATA["students"][key]
    student["grades"]["current_semester"][grade.subject] = {
        "grade": grade.grade,
        "marks": grade.marks,
        "credits": grade.credits
    }
    
    # Recalculate SGPA (simplified)
    grades_map = {"A+": 10, "A": 9, "A-": 8.5, "B+": 8, "B": 7, "B-": 6.5, "C+": 6, "C": 5, "D": 4, "F": 0}
    total_points = 0
    total_credits = 0
    
    for subj, data in student["grades"]["current_semester"].items():
        gp = grades_map.get(data["grade"], 0)
        total_points += gp * data["credits"]
        total_credits += data["credits"]
    
    student["grades"]["sgpa"] = round(total_points / total_credits, 2) if total_credits > 0 else 0
    student["grades"]["earned_credits"] = total_credits
    
    save_data(DATA)
    return {"message": f"Grade updated for {grade.subject}"}


@app.delete("/api/admin/grade/{student_key}/{subject}")
def delete_grade(student_key: str, subject: str):
    """Delete grade for a subject"""
    key = student_key.lower()
    if key not in DATA["students"]:
        raise HTTPException(status_code=404, detail="Student not found")
    
    if subject in DATA["students"][key]["grades"]["current_semester"]:
        del DATA["students"][key]["grades"]["current_semester"][subject]
        save_data(DATA)
    
    return {"message": f"Grade deleted for {subject}"}


# --- EXAMS ---

@app.post("/api/admin/exam")
def add_exam(exam: ExamUpdate):
    """Add exam for a student"""
    key = exam.student_key.lower()
    if key not in DATA["students"]:
        raise HTTPException(status_code=404, detail="Student not found")
    
    DATA["students"][key]["exams"].append({
        "subject": exam.subject,
        "date": exam.date,
        "time": exam.time,
        "venue": exam.venue,
        "type": exam.exam_type,
        "days_left": exam.days_left
    })
    
    save_data(DATA)
    return {"message": f"Exam added for {exam.subject}"}


@app.delete("/api/admin/exam/{student_key}/{subject}")
def delete_exam(student_key: str, subject: str):
    """Delete exam for a subject"""
    key = student_key.lower()
    if key not in DATA["students"]:
        raise HTTPException(status_code=404, detail="Student not found")
    
    DATA["students"][key]["exams"] = [e for e in DATA["students"][key]["exams"] if e["subject"] != subject]
    save_data(DATA)
    return {"message": f"Exam deleted for {subject}"}


# --- FEES ---

@app.post("/api/admin/fees")
def update_fees(fee: FeeUpdate):
    """Update student fees"""
    key = fee.student_key.lower()
    if key not in DATA["students"]:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student = DATA["students"][key]
    student["fees"]["total_fee"] = fee.total_fee
    student["fees"]["paid"] = fee.paid
    student["fees"]["pending"] = fee.total_fee - fee.paid
    student["fees"]["due_date"] = fee.due_date
    
    save_data(DATA)
    return {"message": "Fees updated successfully"}


@app.post("/api/admin/fees/payment/{student_key}")
def add_payment(student_key: str, amount: int, mode: str = "Online"):
    """Record a fee payment"""
    key = student_key.lower()
    if key not in DATA["students"]:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student = DATA["students"][key]
    student["fees"]["paid"] += amount
    student["fees"]["pending"] = student["fees"]["total_fee"] - student["fees"]["paid"]
    student["fees"]["payment_history"].append({
        "date": datetime.now().strftime("%d %b %Y"),
        "amount": amount,
        "mode": mode,
        "receipt": f"REC{len(student['fees']['payment_history'])+1:03d}"
    })
    
    save_data(DATA)
    return {"message": f"Payment of ₹{amount} recorded"}


# --- LIBRARY ---

@app.post("/api/admin/library/book")
def add_library_book(book: LibraryBookAdd):
    """Add a borrowed book for student"""
    key = book.student_key.lower()
    if key not in DATA["students"]:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student = DATA["students"][key]
    student["library"]["books_borrowed"].append({
        "title": book.title,
        "author": book.author,
        "issue_date": book.issue_date,
        "due_date": book.due_date,
        "fine": 0,
        "status": "Active"
    })
    student["library"]["total_borrowed"] = len(student["library"]["books_borrowed"])
    
    save_data(DATA)
    return {"message": f"Book '{book.title}' added"}


@app.delete("/api/admin/library/book/{student_key}/{title}")
def return_book(student_key: str, title: str):
    """Return a book"""
    key = student_key.lower()
    if key not in DATA["students"]:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student = DATA["students"][key]
    student["library"]["books_borrowed"] = [b for b in student["library"]["books_borrowed"] if b["title"] != title]
    student["library"]["total_borrowed"] = len(student["library"]["books_borrowed"])
    
    save_data(DATA)
    return {"message": f"Book '{title}' returned"}


# --- COURSES ---

@app.post("/api/admin/course/{student_key}")
def add_course_to_student(student_key: str, course: CourseCreate):
    """Add a course to student"""
    key = student_key.lower()
    if key not in DATA["students"]:
        raise HTTPException(status_code=404, detail="Student not found")
    
    DATA["students"][key]["courses"].append({
        "code": course.code,
        "name": course.name,
        "credits": course.credits,
        "professor": course.professor,
        "schedule": course.schedule
    })
    
    save_data(DATA)
    return {"message": f"Course {course.name} added"}


@app.delete("/api/admin/course/{student_key}/{course_code}")
def remove_course(student_key: str, course_code: str):
    """Remove a course from student"""
    key = student_key.lower()
    if key not in DATA["students"]:
        raise HTTPException(status_code=404, detail="Student not found")
    
    DATA["students"][key]["courses"] = [c for c in DATA["students"][key]["courses"] if c["code"] != course_code]
    save_data(DATA)
    return {"message": f"Course {course_code} removed"}


# --- NOTICES ---

@app.get("/api/admin/notices")
def get_notices():
    """Get all notices"""
    return {"notices": DATA["notices"]}


@app.post("/api/admin/notice")
def create_notice(notice: NoticeCreate):
    """Create a new notice"""
    new_notice = {
        "id": len(DATA["notices"]) + 1,
        "title": notice.title,
        "content": notice.content,
        "type": notice.notice_type,
        "date": datetime.now().strftime("%d %b %Y"),
        "author": notice.author,
        "time_ago": "Just now"
    }
    DATA["notices"].insert(0, new_notice)
    save_data(DATA)
    return {"message": "Notice created", "notice": new_notice}


@app.delete("/api/admin/notice/{notice_id}")
def delete_notice(notice_id: int):
    """Delete a notice"""
    DATA["notices"] = [n for n in DATA["notices"] if n["id"] != notice_id]
    save_data(DATA)
    return {"message": "Notice deleted"}


# --- TIMETABLE ---

@app.get("/api/admin/timetable")
def get_timetable():
    """Get full timetable"""
    return {"timetable": DATA["timetable"]}


# =============================================
# CAFETERIA ADMIN
# =============================================

@app.get("/api/admin/cafeteria/orders")
def get_all_orders():
    """Get all orders from all students"""
    all_orders = []
    for key, student in DATA["students"].items():
        if "cafeteria_orders" in student:
            for order in student["cafeteria_orders"]:
                order_with_user = order.copy()
                order_with_user["student_name"] = student["name"]
                order_with_user["student_key"] = key
                all_orders.append(order_with_user)
    
    # Sort by date/time (newest first) - simplified
    return {"orders": all_orders}

@app.post("/api/admin/cafeteria/order/status")
def update_order_status(update: OrderStatusUpdate):
    """Update order status"""
    key = update.student_key.lower()
    if key not in DATA["students"]:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student = DATA["students"][key]
    if "cafeteria_orders" in student:
        for order in student["cafeteria_orders"]:
            if order["id"] == update.order_id:
                order["status"] = update.status
                save_data(DATA)
                return {"message": "Order status updated"}
                
    raise HTTPException(status_code=404, detail="Order not found")

@app.post("/api/admin/cafeteria/menu")
def add_menu_item(item: MenuAdd):
    """Add a new item to menu"""
    if "cafeteria" not in DATA:
        DATA["cafeteria"] = {"menu": []}
    
    new_id = len(DATA["cafeteria"]["menu"]) + 1
    new_item = {
        "id": new_id,
        "item": item.item,
        "price": item.price,
        "category": item.category
    }
    DATA["cafeteria"]["menu"].append(new_item)
    save_data(DATA)
    return {"message": "Menu item added", "item": new_item}

@app.delete("/api/admin/cafeteria/menu/{item_id}")
def delete_menu_item(item_id: int):
    """Delete a menu item"""
    if "cafeteria" in DATA and "menu" in DATA["cafeteria"]:
        DATA["cafeteria"]["menu"] = [i for i in DATA["cafeteria"]["menu"] if i["id"] != item_id]
        save_data(DATA)
    return {"message": "Menu item deleted"}


@app.post("/api/admin/timetable/{day}")
def add_class(day: str, time: str, course: str, room: str, professor: str, class_type: str = "Lecture"):
    """Add a class to timetable"""
    day = day.lower()
    if day not in DATA["timetable"]:
        DATA["timetable"][day] = []
    
    DATA["timetable"][day].append({
        "time": time,
        "course": course,
        "room": room,
        "professor": professor,
        "type": class_type
    })
    
    save_data(DATA)
    return {"message": f"Class added to {day}"}


# =============================================
# NEW FEATURE ENDPOINTS
# =============================================

@app.get("/api/placements")
def get_placements():
    return {"placements": DATA.get("placements", [])}

@app.get("/api/events")
def get_events():
    return {"events": DATA.get("events", [])}

@app.get("/api/faculty")
def get_faculty():
    return {"faculty": DATA.get("faculty", [])}

@app.get("/api/cafeteria")
def get_cafeteria():
    return {"menu": DATA.get("cafeteria", {}).get("menu", [])}

@app.get("/api/orders")
def get_my_orders(student_key: str = "lakshya sharma"):
    key = student_key.lower()
    if key in DATA["students"]:
        return {"orders": DATA["students"][key].get("cafeteria_orders", [])}
    return {"orders": []}

@app.post("/api/appointment")
def book_appointment(appt: AppointmentBook):
    key = appt.student_key.lower()
    if key not in DATA["students"]:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # In a real app, we would check professor availability here
    new_appt = {
        "professor": appt.professor_name,
        "date": appt.date,
        "time": appt.time,
        "purpose": appt.purpose,
        "status": "Pending Approval"
    }
    
    student = DATA["students"][key]
    if "faculty_appointments" not in student:
        student["faculty_appointments"] = []
    
    student["faculty_appointments"].append(new_appt)
    save_data(DATA)
    return {"message": "Appointment request sent", "appointment": new_appt}

@app.post("/api/order")
def place_order(order: CafeteriaOrder):
    key = order.student_key.lower()
    if key not in DATA["students"]:
        raise HTTPException(status_code=404, detail="Student not found")
    
    new_order = {
        "id": f"ORD{datetime.now().strftime('%M%S')}",
        "items": order.items,
        "total": order.total_amount,
        "status": "Preparing",
        "date": datetime.now().strftime("%d %b %Y")
    }
    
    student = DATA["students"][key]
    if "cafeteria_orders" not in student:
        student["cafeteria_orders"] = []
        
    student["cafeteria_orders"].insert(0, new_order)
    save_data(DATA)
    return {"message": "Order placed successfully", "order": new_order}


# =============================================
# STUDENT VOICE API (Original)
# =============================================

def detect_intent(text: str):
    """Detect user intent from the query text."""
    t = text.lower()
    
    if any(word in t for word in ["attendance", "present", "absent"]):
        return "attendance"
    if any(word in t for word in ["timetable", "schedule", "class today", "classes today", "today's class"]):
        return "timetable"
    if any(word in t for word in ["exam", "test", "examination", "mid-sem", "end-sem"]):
        return "exams"
    if any(word in t for word in ["grade", "result", "marks", "cgpa", "sgpa", "gpa", "score"]):
        return "grades"
    if any(word in t for word in ["library", "book", "borrow", "due", "fine"]):
        return "library"
    if any(word in t for word in ["fee", "payment", "pay", "dues", "tuition"]):
        return "fees"
    if any(word in t for word in ["notice", "announcement", "news", "update", "circular"]):
        return "notices"
    if any(word in t for word in ["course", "subject", "credit", "professor", "teacher"]):
        return "courses"
    if any(word in t for word in ["profile", "my info", "my details", "about me", "student info"]):
        return "profile"
    if any(word in t for word in ["help", "what can you", "how to", "assist"]):
        return "help"
    if any(word in t for word in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]):
        return "greet"
    
    # New Intents
    if any(word in t for word in ["placement", "job", "internship", "recruit", "company", "package", "ctc"]):
        return "placements"
    if any(word in t for word in ["event", "club", "workshop", "fest", "seminar", "hackathon", "activity"]):
        return "events"
    if any(word in t for word in ["faculty", "professor", "teacher", "appointment", "cabin", "meet sir", "meet ma'am"]):
        return "faculty"
    if any(word in t for word in ["cafeteria", "canteen", "food", "menu", "order", "eat", "lunch", "snack"]):
        return "cafeteria"
    if any(word in t for word in ["predict cgpa", "calculate cgpa", "target cgpa", "gpa calculator"]):
        return "cgpa_calc"
    
    return "unknown"


def get_day_from_text(text: str):
    """Extract day name from text."""
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    t = text.lower()
    
    if "today" in t:
        return datetime.now().strftime("%A").lower()
    if "tomorrow" in t:
        day_index = datetime.now().weekday()
        return days[(day_index + 1) % 7]
    
    for day in days:
        if day in t:
            return day
    
    return datetime.now().strftime("%A").lower()


@app.post("/api/voice")
def process(query: UserQuery):
    """Process user query and return appropriate response."""
    global DATA
    DATA = load_data()  # Reload to get latest data
    
    text = query.text.lower()
    intent = detect_intent(text)
    user_key = query.user.lower()
    
    student = DATA["students"].get(user_key)
    if not student:
        return {"reply": f"Sorry, I couldn't find data for {query.user}. Please check your credentials."}
    
    if intent == "attendance":
        att = student["attendance"]
        overall = att["overall_percent"]
        present = att["present"]
        absent = att["absent"]
        total = att["total_classes"]
        
        subjects = att["subjects"]
        subject_details = [f"{subj}: {data['percent']}%" for subj, data in subjects.items()]
        
        reply = f"📊 Your overall attendance is {overall}%.\n"
        reply += f"Classes attended: {present}/{total} (Absent: {absent})\n\n"
        reply += "Subject-wise breakdown:\n" + "\n".join(f"• {s}" for s in subject_details)
        
        if overall < 75:
            reply += "\n\n⚠️ Warning: Your attendance is below 75%. Please attend more classes!"
        elif overall >= 90:
            reply += "\n\n🌟 Excellent attendance! Keep it up!"
        
        return {"reply": reply}
    
    if intent == "timetable":
        day = get_day_from_text(text)
        timetable = DATA["timetable"]
        
        if day not in timetable:
            return {"reply": f"📅 No classes scheduled for {day.capitalize()}."}
        
        classes = timetable[day]
        reply = f"📅 Timetable for {day.capitalize()}:\n\n"
        
        for c in classes:
            reply += f"🕐 {c['time']} - {c['course']}\n"
            reply += f"   📍 {c['room']} | 👨‍🏫 {c['professor']} | 📚 {c['type']}\n\n"
        
        return {"reply": reply.strip()}
    
    if intent == "exams":
        exams = student["exams"]
        if not exams:
            return {"reply": "📝 No upcoming exams scheduled."}
        
        reply = "📝 Upcoming Examinations:\n\n"
        for exam in exams:
            reply += f"📌 {exam['subject']} ({exam['type']})\n"
            reply += f"   📅 {exam['date']} at {exam['time']}\n"
            reply += f"   📍 Venue: {exam['venue']}\n"
            reply += f"   ⏳ {exam['days_left']} days left\n\n"
        
        return {"reply": reply.strip()}
    
    if intent == "grades":
        grades = student["grades"]
        current = grades["current_semester"]
        
        reply = f"🎓 Academic Performance:\n\n"
        reply += f"📊 CGPA: {grades['cgpa']} | SGPA: {grades['sgpa']}\n"
        reply += f"📚 Credits: {grades['earned_credits']}/{grades['total_credits']}\n\n"
        reply += "Current Semester Grades:\n"
        
        for subject, data in current.items():
            reply += f"• {subject}: {data['grade']} ({data['marks']} marks)\n"
        
        return {"reply": reply.strip()}
    
    if intent == "library":
        library = student["library"]
        books = library["books_borrowed"]
        
        reply = f"📚 Library Status:\n\n"
        reply += f"Books borrowed: {library['total_borrowed']}/{library['max_books']}\n"
        
        if library["total_fine"] > 0:
            reply += f"⚠️ Outstanding fine: ₹{library['total_fine']}\n"
        
        reply += "\nBorrowed Books:\n"
        for book in books:
            status_emoji = "🔴" if book["status"] == "Overdue" else "🟡" if book["status"] == "Due Soon" else "🟢"
            reply += f"\n{status_emoji} {book['title']}\n"
            reply += f"   Author: {book['author']}\n"
            reply += f"   Due: {book['due_date']} ({book['status']})\n"
        
        return {"reply": reply.strip()}
    
    if intent == "fees":
        fees = student["fees"]
        reply = f"💰 Fee Details:\n\n"
        reply += f"Total Fee: ₹{fees['total_fee']:,}\n"
        reply += f"✅ Paid: ₹{fees['paid']:,}\n"
        reply += f"⏳ Pending: ₹{fees['pending']:,}\n"
        reply += f"📅 Due Date: {fees['due_date']}\n"
        
        return {"reply": reply.strip()}
    
    if intent == "notices":
        notices = DATA["notices"]
        reply = "📢 Latest Notices:\n\n"
        
        for notice in notices[:5]:
            type_emoji = "🔴" if notice["type"] == "urgent" else "🟡" if notice["type"] == "warning" else "🔵"
            reply += f"{type_emoji} {notice['title']}\n"
            reply += f"   📍 {notice['author']} • {notice['time_ago']}\n\n"
        
        return {"reply": reply.strip()}
    
    if intent == "courses":
        courses = student["courses"]
        reply = "📖 Enrolled Courses:\n\n"
        
        for course in courses:
            reply += f"📚 {course['code']}: {course['name']}\n"
            reply += f"   👨‍🏫 {course['professor']} | 📊 {course['credits']} credits\n\n"
        
        return {"reply": reply.strip()}
    
    if intent == "profile":
        reply = f"👤 Student Profile:\n\n"
        reply += f"📛 Name: {student['name']}\n"
        reply += f"🆔 Roll No: {student['roll_no']}\n"
        reply += f"📧 Email: {student['email']}\n"
        reply += f"📱 Phone: {student['phone']}\n"
        reply += f"🎓 Course: {student['course']}\n"
        reply += f"📅 Year: {student['year']} ({student['semester']})\n"
        reply += f"📊 CGPA: {student['cgpa']}"
        
        return {"reply": reply}
    
    if intent == "help":
        reply = "🤖 I can help you with:\n\n"
        reply += "📊 Attendance | 📅 Timetable | 📝 Exams\n"
        reply += "🎓 Grades | 📚 Library | 💰 Fees\n"
        reply += "📢 Notices | 📖 Courses | 👤 Profile"
        
        return {"reply": reply}
    
    if intent == "greet":
        hour = datetime.now().hour
        greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"
        return {"reply": f"{greeting}, {student['name']}! 👋 How can I help you today?"}

    # --- NEW FEATURE HANDLERS ---

    if intent == "placements":
        placements = DATA.get("placements", [])
        reply = "💼 Placement Updates:\n\n"
        for p in placements:
            reply += f"🏢 {p['company']} ({p['type']})\n"
            reply += f"   💰 CTC: {p['ctc']} | Role: {p['roles'][0]}\n"
            reply += f"   📅 Date: {p['date']}\n\n"
        return {"reply": reply.strip()}

    if intent == "events":
        events = DATA.get("events", [])
        reply = "🎭 Upcoming Campus Events:\n\n"
        for e in events:
            reply += f"🎪 {e['name']}\n"
            reply += f"   📅 {e['date']} @ {e['venue']}\n"
            reply += f"   ℹ️ {e['description']}\n\n"
        return {"reply": reply.strip()}

    if intent == "faculty":
        faculty = DATA.get("faculty", [])
        reply = "👨‍🏫 Faculty Directory:\n\n"
        for f in faculty:
            reply += f"👤 {f['name']} ({f['designation']})\n"
            reply += f"   📍 {f['cabin']} | 📧 {f['email']}\n\n"
        
        reply += "You can ask me to 'Book an appointment' if needed!"
        return {"reply": reply.strip()}

    if intent == "cafeteria":
        menu = DATA.get("cafeteria", {}).get("menu", [])
        reply = "🍔 Cafeteria Menu:\n\n"
        for item in menu:
            reply += f"• {item['item']} - ₹{item['price']}\n"
        
        reply += "\nSay 'Order [Item Name]' to place an order!"
        return {"reply": reply.strip()}

    if intent == "cgpa_calc":
        return {"reply": "🔢 To calculate your target CGPA, please use the 'CGPA Predictor' tool in the dashboard menu. It allows you to simulate your future grades!"}

    return {"reply": "I didn't understand. Try asking about attendance, timetable, exams, fees, library, placements, events, faculty, or cafeteria!"}


# Duplicate root endpoint removed to allow frontend serving



@app.get("/api/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
