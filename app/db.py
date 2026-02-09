import mariadb, os, sys
from datetime import datetime
from typing import Dict, List, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv(os.getenv("ENV_FILE", ".env"))



@dataclass
class User:
    id: int
    surname: str
    telegram_id: int
    roles: List[str]



@dataclass
class Subject:
    id: int
    name: str
    is_active: bool



@dataclass
class Lesson:
    id: int
    subject: Subject
    index: int
    date: datetime



@dataclass
class Attendance:
    user_id: int
    lesson_id: int
    status: str



@dataclass
class Duty:
    id: int
    date: datetime
    status: str
    dutiers: List[User]
    blob_id: int | None

@dataclass
class DutyPhoto:
    id: int
    duty_id: int
    user_id: int
    blob: bytearray



def get_conn() -> mariadb.Connection:
    try:
        conn = mariadb.connect(
            host=os.getenv("MARIADB_HOST"),
            port=int(os.getenv("MARIADB_PORT")),
            database=os.getenv("MARIADB_DATABASE"),
            user=os.getenv("MARIADB_USER"),
            password=os.getenv("MARIADB_PASSWORD")
        )
        return conn
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)



def get_user_by_id(id: int) -> User | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, surname, telegram_id FROM users WHERE id = ?",
                (id,)
            )
            user = cur.fetchone()
            cur.execute(
                "SELECT role FROM roles WHERE user_id = ?",
                (id,)
            )
            roles = cur.fetchall()
            return User(user[0], user[1], user[2], [role[0] for role in roles] if roles else []) if user else None

def get_users() -> List[User]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM users ORDER BY surname ASC"
            )
            users = cur.fetchall()
            return [get_user_by_id(user[0]) for user in users] if users else []

def get_user_by_telegram(telegram_id: int) -> User | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM users WHERE telegram_id = ?",
                (telegram_id,)
            )
            id = cur.fetchone()
            return get_user_by_id(id[0]) if id else None

def get_users_by_role(role: str) -> List[User]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT users.id FROM users JOIN roles ON roles.user_id = users.id WHERE roles.role = ? ORDER BY users.surname",
                (role,)
            )
            users = cur.fetchall()
            return [get_user_by_id(user[0]) for user in users] if users else []
        
def set_user_surname(user_id: int, surname: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET surname = ? WHERE id = ?",
                (surname, user_id)
            )
            conn.commit()

def add_role(user_id: int, role: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            user = get_user_by_id(user_id)
            if not user:
                return
            
            if role in user.roles:
                return
            
            cur.execute(
                "INSERT INTO roles (user_id, role) VALUES (?, ?)",
                (user_id, role)
            )
            conn.commit()

def remove_role(user_id: int, role: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM roles WHERE user_id = ? AND role = ?",
                (user_id, role)
            )
            conn.commit()

def add_user(surname: str, telegram_id: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            if get_user_by_telegram(telegram_id):
                return
            
            cur.execute(
                "INSERT INTO users (surname, telegram_id) VALUES (?, ?)",
                (surname, telegram_id)
            )
            conn.commit()



def get_subject_by_id(id: int) -> Subject | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, is_active FROM subjects WHERE id = ?",
                (id,)
            )
            subject = cur.fetchone()
            return Subject(subject[0], subject[1], subject[2]) if subject else None

def get_subjects() -> List[Subject]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM subjects"
            )
            subjects = cur.fetchall()
            return [get_subject_by_id(subject[0]) for subject in subjects] if subjects else []

def get_active_subjects() -> List[Subject]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM subjects WHERE is_active = true"
            )
            subjects = cur.fetchall()
            return [get_subject_by_id(subject[0]) for subject in subjects] if subjects else []
        
def add_subject(name: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO subjects (name) VALUES (?)",
                (name,)
            )
            conn.commit()

def set_subject_status(subject_id: int, is_active: bool):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE subjects SET is_active = ? WHERE id = ?",
                (is_active, subject_id)
            )
            conn.commit()

def set_subject_name(subject_id: int, name: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE subjects SET name = ? WHERE id = ?",
                (name, subject_id)
            )
            conn.commit()



def get_lesson_by_id(id: int) -> Lesson | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, subject_id, `index`, `date` FROM lessons WHERE id = ?",
                (id,)
            )
            lesson = cur.fetchone()
            return Lesson(lesson[0], get_subject_by_id(lesson[1]), lesson[2], lesson[3]) if lesson else None

def get_lessons() -> List[Lesson]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM lessons"
            )
            lessons = cur.fetchall()
            return [get_lesson_by_id(lesson[0]) for lesson in lessons] if lessons else []
        
def get_lessons_by_date(date: datetime) -> List[Lesson]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM lessons WHERE `date` = ? ORDER BY `index` ASC",
                (date,)
            )
            lessons = cur.fetchall()
            return [get_lesson_by_id(lesson[0]) for lesson in lessons] if lessons else []
        
def get_lesson_by_date_index(date: datetime, index: int) -> Lesson | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM lessons WHERE `date` = ? AND `index` = ?",
                (date, index)
            )
            lesson = cur.fetchone()
            return get_lesson_by_id(lesson[0]) if lesson else None

def add_lesson(subject_id: int, index: int, date: datetime):
    with get_conn() as conn:
        with conn.cursor() as cur:
            lesson = get_lesson_by_date_index(date, index)
            if lesson:
                cur.execute(
                    "UPDATE lessons SET subject_id = ? WHERE id = ?",
                    (subject_id, lesson.id)
                )
            else:
                cur.execute(
                    "INSERT INTO lessons (subject_id, `index`, `date`) VALUES (?, ?, ?)",
                    (subject_id, index, date)
                )
            conn.commit()



def get_lesson_attendance(lesson_id: int) -> List[Attendance]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT lesson_id, user_id, status FROM attendance WHERE lesson_id = ?",
                (lesson_id,)
            )
            attendance = cur.fetchall()
            return [Attendance(att[1], att[0], att[2]) for att in attendance] if attendance else []
        
def get_user_attendance(user_id: int) -> List[Attendance]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT lesson_id, user_id, status FROM attendance WHERE user_id = ?",
                (user_id,)
            )
            attendance = cur.fetchall()
            return [Attendance(att[1], att[0], att[2]) for att in attendance] if attendance else []

def get_user_on_lesson_attendance(user_id: int, lesson_id: int) -> Attendance | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT status FROM attendance WHERE lesson_id = ? AND user_id = ?",
                (lesson_id, user_id)
            )
            attendance = cur.fetchone()
            return Attendance(user_id, lesson_id, attendance[0]) if attendance else None

def set_attendance(lesson_id: int, user_id: int, status: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM attendance WHERE lesson_id = ? AND user_id = ?",
                (lesson_id, user_id)
            )
            att = cur.fetchone()
            if att:
                cur.execute(
                    "UPDATE attendance SET status = ? WHERE lesson_id = ? AND user_id = ?",
                    (status, lesson_id, user_id)
                )
            else:
                cur.execute(
                    "INSERT INTO attendance (lesson_id, user_id, status) VALUES (?, ?, ?)",
                    (lesson_id, user_id, status)
                )
            conn.commit()



def get_duty_by_id(id: int) -> Duty | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT duties.id, date, status, duty_photos.id FROM duties LEFT JOIN duty_photos ON duty_photos.duty_id = duties.id WHERE duties.id = ?",
                (id,)
            )
            duty = cur.fetchone()
            cur.execute(
                "SELECT user_id FROM duty_assignments WHERE duty_id = ?",
                (id,)
            )
            dutiers = cur.fetchall()
            return Duty(duty[0], duty[1], duty[2], [get_user_by_id(dutier[0]) for dutier in dutiers] if dutiers else [], duty[3]) if duty else None

def get_duty_by_date(date: datetime) -> Duty | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM duties WHERE `date` = ?",
                (date,)
            )
            duty = cur.fetchone()
            return get_duty_by_id(duty[0]) if duty else None

def add_duty(date: datetime):
    with get_conn() as conn:
        with conn.cursor() as cur:
            if get_duty_by_date(date):
                return
            
            cur.execute(
                "INSERT INTO duties (`date`, status) VALUES (?, 'undone')",
                (date,)
            )
            conn.commit()

def set_duty_status(duty_id: int, status: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE duties SET status = ? WHERE id = ?",
                (status, duty_id)
            )
            conn.commit()

def assign_to_duty(duty_id: int, user_id: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO duty_assignments (duty_id, user_id) VALUES (?, ?)",
                (duty_id, user_id)
            )
            conn.commit()

def unassign_to_duty(duty_id: int, user_id: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM duty_assignments WHERE duty_id = ? AND user_id = ?",
                (duty_id, user_id)
            )
            conn.commit()

def get_dutiers(duty_id: int) -> List[User]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id FROM duty_assignments WHERE duty_id = ?",
                (duty_id,)
            )
            dutiers = cur.fetchall()
            return [get_user_by_id(dutier[0]) for dutier in dutiers] if dutiers else []
        
def get_duty_order() -> List[User]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT users.id, users.surname, MAX(CASE WHEN duties.status = 'done' THEN duties.date END) AS last_duty\n" \
                "FROM users\n" \
                "JOIN roles ON roles.user_id = users.id AND roles.role = 'dutier'\n" \
                "JOIN attendance ON attendance.user_id = users.id AND attendance.status = 'present'\n" \
                "JOIN lessons ON lessons.id = attendance.lesson_id AND lessons.date = CURDATE() AND lessons.index = (\n" \
                "SELECT MAX(`index`) FROM lessons WHERE date = CURDATE()\n" \
                ")\n" \
                "LEFT JOIN duty_assignments ON duty_assignments.user_id = users.id\n" \
                "LEFT JOIN duties ON duties.id = duty_assignments.duty_id\n" \
                "GROUP BY users.id, users.surname\n" \
                "ORDER BY MAX(CASE WHEN duties.status = 'done' THEN duties.date END) IS NOT NULL, MAX(CASE WHEN duties.status = 'done' THEN duties.date END) ASC, users.surname ASC"
            )
            dutiers = cur.fetchall()
            return [get_user_by_id(dutier[0]) for dutier in dutiers] if dutiers else []

def add_duty_photo(duty_id: int, user_id: int, blob: bytearray):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO duty_photos (duty_id, user_id, photo) VALUES (?, ?, ?)",
                (duty_id, user_id, blob)
            )
            conn.commit()

def get_duty_photo(id: int) -> DutyPhoto | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, duty_id, user_id, photo FROM duty_photos WHERE id = ?",
                (id,)
            )
            photo = cur.fetchone()
            return DutyPhoto(photo[0], photo[1], photo[2], photo[3]) if photo else None
        


def add_group(telegram_id: int):
    if telegram_id in get_groups():
        return
    
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO groups (telegram_id) VALUES (?)",
                (telegram_id,)
            )
            conn.commit()

def remove_group(telegram_id: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM groups WHERE telegram_id = ?",
                (telegram_id,)
            )
            conn.commit()

def get_groups() -> List[int]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT telegram_id FROM groups"
            )
            groups = cur.fetchall()
            return [group[0] for group in groups] if groups else []