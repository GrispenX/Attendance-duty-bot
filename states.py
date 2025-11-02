from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import db, io

DATE_FORMAT = "Формат дати: ДД.ММ.РРРР"

def StrToDate(str: str):
    str = str.strip()
    try:
        return datetime.strptime(str, "%d.%m.%Y").date()
    except ValueError:
        return None



class State:
    async def on_enter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        pass

    async def on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        pass

    async def on_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        pass

    async def __send_message__(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message: str, markup: InlineKeyboardMarkup | None = None):
        if update.message:
            await update.message.reply_text(message, reply_markup=markup)
        elif update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=markup)



@dataclass
class Registration(State):
    async def on_enter(self, update, context):
        user = db.get_user_by_telegram(update.effective_user.id)
        if user:
            return AlreadyRegistered()
        
        await self.__send_message__(
            update, context,
            "Реєстрація\nНадішли своє прізвище"
        )
    
    async def on_message(self, update, context):
        text = update.message.text
        surname = text.capitalize()
        return RegistrationConfirm(surname)



@dataclass
class AlreadyRegistered(State):
    async def on_enter(self, update, context):
        await self.__send_message__(
            update, context,
            "Ви вже зареєструвались"
        )



@dataclass
class RegistrationConfirm(State):
    surname: str

    async def on_enter(self, update, context):
        await self.__send_message__(
            update, context,
            f"Реєстрація\nВаше прізвище '{self.surname}'?",
            InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Так", callback_data="Yes"),
                    InlineKeyboardButton("Ні", callback_data="No")
                ]
            ])
        )
    
    async def on_callback(self, update, context):
        data = update.callback_query.data
        await update.callback_query.answer()

        if data == "Yes":
            return RegistrationSuccess(self.surname)
        
        elif data == "No":
            return Registration()



@dataclass
class RegistrationSuccess(State):
    surname: str

    async def on_enter(self, update, context):
        db.add_user(self.surname, update.effective_user.id)
        await self.__send_message__(
            update, context,
            f"Ви успішно зареєструвались як '{self.surname}'\nОчікуйте підтвердження адміністратора"
        )



@dataclass
class HomeAccessDenied(State):
    async def on_enter(self, update, context):
        await self.__send_message__(
            update, context,
            "У вас немає доступу. Якщо ви думаєте що це помилка зверніться до адміністратора"
        )



@dataclass
class Home(State):
    async def on_enter(self, update, context):
        user = db.get_user_by_telegram(update.effective_user.id)
        if not user:
            return HomeAccessDenied()
        
        if not user.roles:
            return HomeAccessDenied()
        
        await self.__send_message__(
            update, context,
            "Привіт!\nЯк я можу допомогти?",
            markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Надіслати чергування", callback_data="SaveDutyPhoto"),
                    InlineKeyboardButton("Преглянути чергування", callback_data="GetDutyPhoto")
                ],
                [
                    InlineKeyboardButton("Моя відвідуваність", callback_data="MyAttendance"),
                    InlineKeyboardButton("Історія чергувань", callback_data="DutyHistory")
                ],
                [
                    InlineKeyboardButton("Адмін-панель", callback_data="Admin")
                ]
            ])
        )

    async def on_callback(self, update, context):
        data = update.callback_query.data
        await update.callback_query.answer()

        if data == "SaveDutyPhoto":
            return SaveDutyPhoto()
        
        elif data == "GetDutyPhoto":
            return GetDutyPhotoDate()
        
        elif data == "DutyHistory":
            return DutyHistoryFrom()
        
        elif data == "MyAttendance":
            return MyAttendanceFrom()
        
        elif data == "Admin":
            return Admin()



@dataclass
class SaveDutyPhoto(State):
    async def on_enter(self, update, context):
        duty = db.get_duty_by_date(datetime.now().date())
        if not duty:
            return NotADutierToday()
        
        if db.get_user_by_telegram(update.effective_user.id) not in duty.dutiers:
            return NotADutierToday()
        
        if duty.blob_id:
            return PhotoAlreadySaved()
        
        await self.__send_message__(update, context, "Надішли мені фото чергування")

    async def on_message(self, update, context):
        photo = update.message.photo
        if photo:
            duty = db.get_duty_by_date(datetime.now().date())
            file = await photo[-1].get_file()
            blob = await file.download_as_bytearray()
            db.add_duty_photo(duty.id, db.get_user_by_telegram(update.effective_user.id).id, bytes(blob))
            db.set_duty_status(duty.id, "done")
            return DutyPhotoSaved()



@dataclass
class NotADutierToday(State):
    async def on_enter(self, update, context):
        await self.__send_message__(
            update, context,
            "Ви сьогодні не чергуєте",
            InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="Back")]])
        )
    
    async def on_callback(self, update, context):
        data = update.callback_query.data
        await update.callback_query.answer()
        if data == "Back":
            return Home()



@dataclass
class PhotoAlreadySaved(State):
    async def on_enter(self, update, context):
        await self.__send_message__(
            update, context,
            "Фото чергування вже завантажено",
            InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="Back")]])
        )
    
    async def on_callback(self, update, context):
        data = update.callback_query.data
        await update.callback_query.answer()
        if data == "Back":
            return Home()



@dataclass
class DutyPhotoSaved(State):
    async def on_enter(self, update, context):
        await self.__send_message__(
            update, context,
            "Фото завантажено!",
            InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="Back")]])
        )
    
    async def on_callback(self, update, context):
        data = update.callback_query.data
        await update.callback_query.answer()
        if data == "Back":
            return Home()



@dataclass
class GetDutyPhotoDate(State):
    async def on_enter(self, update, context):
        await self.__send_message__(
            update, context,
            "Надішли дату за яку хочеш переглянути фото"
        )
    
    async def on_message(self, update, context):
        text = update.message.text
        if text:
            date = StrToDate(text)
            if date:
                duty = db.get_duty_by_date(date)
                if not duty:
                    return NoDuty()
                
                if not duty.blob_id:
                    return NoDutyPhoto()
                
                return GetDutyPhoto(duty.blob_id)



@dataclass
class GetDutyPhoto(State):
    blob_id: int

    async def on_enter(self, update, context):
        blob = db.get_duty_photo(self.blob_id)
        photo = io.BytesIO(blob.blob)
        await update.message.reply_photo(
            photo,
            caption=f"Фото завантажив: {db.get_user_by_id(blob.user_id).surname}\nГоловна - /home"
        )
                


@dataclass
class NoDuty(State):
    async def on_enter(self, update, context):
        await self.__send_message__(
            update, context,
            "Цього числа не було чергування",
            InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="Back")]])
        )
    
    async def on_callback(self, update, context):
        data = update.callback_query.data
        await update.callback_query.answer()
        if data == "Back":
            return Home()



@dataclass
class NoDutyPhoto(State):
    async def on_enter(self, update, context):
        await self.__send_message__(
            update, context,
            "Нажаль немає збереженого фото чергування",
            InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="Back")]])
        )
    
    async def on_callback(self, update, context):
        data = update.callback_query.data
        await update.callback_query.answer()
        if data == "Back":
            return Home()



@dataclass
class DutyHistoryFrom(State):
    async def on_enter(self, update, context):
        await self.__send_message__(update, context, "Надішли дату з якої почати формувати історію чергувань\nФормат дати: ДД.ММ.РРРР")

    async def on_message(self, update, context):
        text = update.message.text
        if text:
            from_date = StrToDate(text)
            if from_date:
                return DutyHistoryTo(from_date)



@dataclass
class DutyHistoryTo(State):
    from_date: datetime

    async def on_enter(self, update, context):
        await self.__send_message__(update, context, "Чудово!\nТепер наділши дату до якої формувати історію чергувань\nФормат дати: ДД.ММ.РРРР")

    async def on_message(self, update, context):
        text = update.message.text
        if text:
            to_date = StrToDate(text)
            if to_date:
                return MakeDutyHistory(self.from_date, to_date)



@dataclass
class MakeDutyHistory(State):
    from_date: datetime
    to_date: datetime

    async def on_enter(self, update, context):
        # DO THIS
        return Home()



@dataclass
class MyAttendanceFrom(State):
    async def on_enter(self, update, context):
        await self.__send_message__(update, context, "Надішли дату з якої почати формувати твою відвідуваність\nФормат дати: ДД.ММ.РРРР")

    async def on_message(self, update, context):
        text = update.message.text
        if text:
            from_date = StrToDate(text)
            if from_date:
                return MyAttendanceTo(from_date)



@dataclass
class MyAttendanceTo(State):
    from_date: datetime
    
    async def on_enter(self, update, context):
        await self.__send_message__(update, context, "Надішли дату до якої формувати твою відвідуваність\nФормат дати: ДД.ММ.РРРР")

    async def on_message(self, update, context):
        text = update.message.text
        if text:
            to_date = StrToDate(text)
            if to_date:
                return MakeMyAttendance(self.from_date, to_date)



@dataclass
class MakeMyAttendance(State):
    from_date: datetime
    to_date: datetime

    async def on_enter(self, update, context):
        # DO THIS
        return Home()



@dataclass
class AdminAccessDenied(State):
    async def on_enter(self, update, context):
        await self.__send_message__(
            update, context,
            "У вас немає прав адміністратора",
            InlineKeyboardMarkup([[InlineKeyboardButton("Головна", callback_data="Back")]])
        )

    async def on_callback(self, update, context):
        data = update.callback_query.data
        await update.callback_query.answer()
        if data == "Back":
            return Home()



@dataclass
class Admin(State):
    async def on_enter(self, update, context):
        user = db.get_user_by_telegram(update.effective_user.id)
        if not user:
            return AdminAccessDenied()
        
        if "admin" not in user.roles:
            return AdminAccessDenied()

        await self.__send_message__(
            update, context,
            "Єбать важний хуй бумажний\nВот твоя адмінка",
            markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Нова пара", callback_data="AddLesson"), InlineKeyboardButton("Чергування", callback_data="Duty")],
                [InlineKeyboardButton("Дисципліни", callback_data="Subjects"), InlineKeyboardButton("Юзери", callback_data="Users")],
                [InlineKeyboardButton("Звіти", callback_data="Reports"), InlineKeyboardButton("Пари", callback_data="Lessons")],
                [InlineKeyboardButton("Назад", callback_data="Back")]
            ])
        )

    async def on_callback(self, update, context):
        data = update.callback_query.data
        await update.callback_query.answer()

        if data == "AddLesson":
            return AddLessonDate()

        elif data == "Lessons":
            return LessonsDate()

        elif data == "Duty":
            return Duty()

        elif data == "Subjects":
            return Subjects()

        elif data == "Users":
            return Users()

        elif data == "Reports":
            return

        elif data == "Back":
            return Home()



@dataclass
class AddLessonDate(State):
    async def on_enter(self, update, context):
        await self.__send_message__(
            update, context,
            "Надішли дату",
            InlineKeyboardMarkup([[InlineKeyboardButton("Сьогодні", callback_data="Today")]])
        )

    async def on_message(self, update, context):
        text = update.message.text
        if text:
            date = StrToDate(text)
            if date:
                return AddLessonIndex(date)
    
    async def on_callback(self, update, context):
        data = update.callback_query.data
        await update.callback_query.answer()

        if data == "Today":
            return AddLessonIndex(datetime.now().date())



@dataclass
class AddLessonIndex(State):
    date: datetime

    async def on_enter(self, update, context):
        await self.__send_message__(
            update, context,
            "Вибери номер пари",
            InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("1", callback_data="1"),
                    InlineKeyboardButton("2", callback_data="2"),
                    InlineKeyboardButton("3", callback_data="3"),
                    InlineKeyboardButton("4", callback_data="4")
                ],
                [
                    InlineKeyboardButton("5", callback_data="5"),
                    InlineKeyboardButton("6", callback_data="6"),
                    InlineKeyboardButton("7", callback_data="7"),
                    InlineKeyboardButton("8", callback_data="8")
                ]
            ])
        )
    
    async def on_callback(self, update, context):
        data = update.callback_query.data
        await update.callback_query.answer()
        if data.isdigit():
            return AddLessonSubject(self.date, data)



@dataclass
class AddLessonSubject(State):
    date: datetime
    index: int

    async def on_enter(self, update, context):
        await self.__send_message__(
            update, context,
            "Вибери дисципліну",
            InlineKeyboardMarkup([[InlineKeyboardButton(subject.name, callback_data=subject.id)] for subject in db.get_active_subjects()])
        )
    
    async def on_callback(self, update, context):
        data = update.callback_query.data
        await update.callback_query.answer()
        if data.isdigit():
            if db.get_subject_by_id(data):
                db.add_lesson(data, self.index, self.date)
                lesson = db.get_lesson_by_date_index(self.date, self.index)
                for student in db.get_users_by_role("student"):
                    db.set_attendance(lesson.id, student.id, "present")
                return Attendance(db.get_lesson_by_date_index(self.date, self.index).id)



@dataclass
class LessonsDate(State):
    async def on_enter(self, update, context):
        await self.__send_message__(
            update, context,
            "Надішли дату"
        )

    async def on_message(self, update, context):
        text = update.message.text
        if text:
            date = StrToDate(text)
            if date:
                return Lessons(date)



@dataclass
class Lessons(State):
    date: datetime

    async def on_enter(self, update, context):
        lessons = db.get_lessons_by_date(self.date)
        await self.__send_message__(
            update, context,
            f"Пари за {self.date}",
            InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(f"{lesson.index}. {lesson.subject.name}", callback_data=lesson.id)
                    ] for lesson in lessons
                ]
                +
                [
                    [
                        InlineKeyboardButton("Назад", callback_data="Back")
                    ]
                ]
            )
        )
    
    async def on_callback(self, update, context):
        data = update.callback_query.data
        await update.callback_query.answer()

        if data == "Back":
            return Admin()

        elif data.isdigit():
            return Lesson(data)



@dataclass
class Lesson(State):
    lesson_id: int

    async def on_enter(self, update, context):
        lesson = db.get_lesson_by_id(self.lesson_id)
        await self.__send_message__(
            update, context,
            f"{lesson.date}, {lesson.index}. {lesson.subject.name}",
            InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Змінити дисципліну", callback_data="SetSubject"),
                        InlineKeyboardButton("Присутні", callback_data="Attendance")
                    ],
                    [
                        InlineKeyboardButton("Назад", callback_data="Back")
                    ]
                ]
            )
        )

    async def on_callback(self, update, context):
        data = update.callback_query.data
        await update.callback_query.answer()

        if data == "SetSubject":
            return LessonSetSubject(self.lesson_id)
        
        elif data == "Attendance":
            return Attendance(self.lesson_id)

        elif data == "Back":
            return Lessons(db.get_lesson_by_id(self.lesson_id).date)



@dataclass
class LessonSetSubject(State):
    lesson_id: int

    async def on_enter(self, update, context):
        await self.__send_message__(
            update, context,
            "Вибери дисципліну",
            InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(subject.name, callback_data=subject.id)
                    ] for subject in db.get_active_subjects()
                ]
            )
        )

    async def on_callback(self, update, context):
        data = update.callback_query.data
        await update.callback_query.answer()
        if data.isdigit():
            lesson = db.get_lesson_by_id(self.lesson_id)
            db.add_lesson(data, lesson.index, lesson.date)
            return Lesson(lesson.id)



@dataclass
class Attendance(State):
    lesson_id: int

    async def on_enter(self, update, context):
        lesson = db.get_lesson_by_id(self.lesson_id)
        await self.__send_message__(
            update, context,
            f"Присутні на {lesson.date}, {lesson.index}. {lesson.subject.name}",
            InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(f"{"🟢" if att.status == "present" else ("🔴" if att.status == "unpresent" else "🟡")} {db.get_user_by_id(att.user_id).surname}", callback_data=att.user_id)
                    ] for att in db.get_lesson_attendance(self.lesson_id)
                ]
                +
                [
                    [
                        InlineKeyboardButton("Назад", callback_data="Back")
                    ]
                ]
            )
        )
    
    async def on_callback(self, update, context):
        data = update.callback_query.data
        await update.callback_query.answer()
        
        if data == "Back":
            return Lesson(self.lesson_id)
        
        elif data.isdigit():
            att = db.get_user_on_lesson_attendance(data, self.lesson_id)
            if att.status == "present":
                db.set_attendance(att.lesson_id, att.user_id, "unpresent")
            elif att.status == "unpresent":
                db.set_attendance(att.lesson_id, att.user_id, "formal_present")
            else:
                db.set_attendance(att.lesson_id, att.user_id, "present")
            return Attendance(self.lesson_id)



@dataclass
class Duty(State):
    async def on_enter(self, update, context):
        await self.__send_message__(
            update, context,
            "Чергування\nВибери дію",
            InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Автовибір", callback_data="Auto"),
                    InlineKeyboardButton("Попередні", callback_data="PreviousDuties")
                ],
                [
                    InlineKeyboardButton("Назад", callback_data="Back")
                ]
            ])
        )

    async def on_callback(self, update, context):
        data = update.callback_query.data
        await update.callback_query.answer()

        if data == "Auto":
            return AutoDutyAmount()
        
        elif data == "PreviousDuties":
            return PreviousDuties()
        
        elif data == "Back":
            return Admin()



@dataclass
class AutoDutyAmount(State):
    async def on_enter(self, update, context):
        await self.__send_message__(
            update, context,
            "Вибери кількість чергових",
            InlineKeyboardMarkup([[InlineKeyboardButton(i, callback_data=i) for i in range(1, 5)]])
        )

    async def on_callback(self, update, context):
        data = update.callback_query.data
        await update.callback_query.answer()
        return AutoDutyChoose(int(data))



@dataclass
class AutoDutyChoose(State):
    dutiers_amount: int

    async def on_enter(self, update, context):
        dutiers_list = db.get_duty_order()
        self.dutiers_amount = min(self.dutiers_amount, len(dutiers_list))
        choosen_dutiers = [dutiers_list[i] for i in range(self.dutiers_amount)]
        return AutoDutyConfirm(choosen_dutiers)



@dataclass
class AutoDutyConfirm(State):
    dutiers: List[db.User]

    async def on_enter(self, update, context):
        await self.__send_message__(
            update, context,
            "\n".join(["Вибрані чергові:"] + [dutier.surname for dutier in self.dutiers]),
            InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Підтвердити", callback_data="Confirm"),
                    InlineKeyboardButton("Назад", callback_data="Back")
                ]
            ])
        )
    
    async def on_callback(self, update, context):
        data = update.callback_query.data
        await update.callback_query.answer()

        if data == "Confirm":
            return AutoDutyNotify(self.dutiers)
        
        if data == "Back":
            return Duty()



@dataclass
class AutoDutyNotify(State):
    dutiers: List[db.User]

    async def on_enter(self, update, context):
        # DO THIS
        return AutoDutySave(self.dutiers)



@dataclass
class AutoDutySave(State):
    dutiers: List[db.User]

    async def on_enter(self, update, context):
        db.add_duty(datetime.now().date())
        duty = db.get_duty_by_date(datetime.now().date())
        for dutier in self.dutiers:
            db.assign_to_duty(duty.id, dutier.id)
        return Home()



@dataclass
class PreviousDuties(State):
    async def on_enter(self, update, context):
        await self.__send_message__(
            update, context,
            "Надішли дату чергування"
        )

    async def on_message(self, update, context):
        text = update.message.text
        if text:
            date = StrToDate(text)
            if date:
                duty = db.get_duty_by_date(date)
                if duty:
                    return PreviousDuty(duty.id)



@dataclass
class PreviousDuty(State):
    duty_id: int

    async def on_enter(self, update, context):
        duty = db.get_duty_by_id(self.duty_id)
        await self.__send_message__(
            update, context,
            f"{duty.date} - {duty.status}",
            InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Статус", callback_data="Status"),
                        InlineKeyboardButton("Чергові", callback_data="Dutiers")
                    ],
                    [
                        InlineKeyboardButton("Назад", callback_data="Back")
                    ]
                ]
            )
        )
    
    async def on_callback(self, update, context):
        data = update.callback_query.data
        await update.callback_query.answer()

        if data == "Back":
            return Duty()
        
        elif data == "Status":
            duty = db.get_duty_by_id(self.duty_id)
            db.set_duty_status(duty.id, "done" if duty.status == "undone" else "undone")
            return PreviousDuty(self.duty_id)
        elif data == "Dutiers":
            return PreviousDutyDutiers(self.duty_id)



@dataclass
class PreviousDutyDutiers(State):
    duty_id: int

    async def on_enter(self, update, context):
        duty = db.get_duty_by_id(self.duty_id)
        await self.__send_message__(
            update, context,
            f"Чергові {duty.date} - {duty.status}",
            InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(f"{"🟢" if dutier in duty.dutiers else "🔴"} {dutier.surname}", callback_data=dutier.id)] for dutier in db.get_users_by_role("dutier")
                ]
                +
                [
                    [InlineKeyboardButton("Назад", callback_data="Back")]
                ]
            )
        )
    
    async def on_callback(self, update, context):
        data = update.callback_query.data
        await update.callback_query.answer()

        if data == "Back":
            return PreviousDuty(self.duty_id)
        
        elif data.isdigit():
            duty = db.get_duty_by_id(self.duty_id)
            if db.get_user_by_id(data) in duty.dutiers:
                db.unassign_to_duty(duty.id, data)
            else:
                db.assign_to_duty(duty.id, data)
            return PreviousDutyDutiers(duty.id)



@dataclass
class Reports(State):
    pass



@dataclass
class ReportLessonsFrom(State):
    pass



@dataclass
class ReportLessonsTo(State):
    pass



@dataclass
class ReportDaysFrom(State):
    pass



@dataclass
class ReportDaysTo(State):
    pass



@dataclass
class ReportSubjectFrom(State):
    pass



@dataclass
class ReportSubjectTo(State):
    pass



@dataclass
class ReportSubjectName(State):
    pass



@dataclass
class Subjects(State):
    async def on_enter(self, update, context):
        await self.__send_message__(
            update, context,
            "Дисципліни",
            InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(f"{"🟢" if subject.is_active else "🔴"} {subject.name}", callback_data=subject.id)] for subject in db.get_subjects()
                ]
                +
                [
                    [
                        InlineKeyboardButton("Додати", callback_data="Add"),
                        InlineKeyboardButton("Назад", callback_data="Back")
                    ]
                ]
            )
        )

    async def on_callback(self, update, context):
        data = update.callback_query.data
        await update.callback_query.answer()

        if data == "Back":
            return Admin()
        
        elif data == "Add":
            return SubjectsAddName()

        else:
            return Subject(data)



@dataclass
class SubjectsAddName(State):
    async def on_enter(self, update, context):
        await update.callback_query.edit_message_text("Введи назву дисципліни")

    async def on_message(self, update, context):
        text = update.message.text
        subjects = [subject.strip() for subject in text.split(",")]
        for subject in subjects:
            db.add_subject(subject)
        return Subjects()
        


@dataclass
class Subject(State):
    subject_id: int

    async def on_enter(self, update, context):
        subject = db.get_subject_by_id(self.subject_id)
        await self.__send_message__(
            update, context,
            f"Вибери дію для {subject.name}",
            InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("🟢" if subject.is_active else "🔴", callback_data="Status"),
                        InlineKeyboardButton("✏️", callback_data="Rename")
                    ],
                    [
                        InlineKeyboardButton("Назад", callback_data="Back")
                    ]
                ]
            )
        )
    
    async def on_callback(self, update, context):
        data = update.callback_query.data
        await update.callback_query.answer()
        subject = db.get_subject_by_id(self.subject_id)

        if data == "Status":
            db.set_subject_status(subject.id, not subject.is_active)
            return Subject(self.subject_id)
        
        elif data == "Rename":
            return SubjectRename(self.subject_id)
        
        elif data == "Back":
            return Subjects()



@dataclass
class SubjectRename(State):
    subject_id: int

    async def on_enter(self, update, context):
        subject = db.get_subject_by_id(self.subject_id)
        await self.__send_message__(
            update, context,
            f"Надішли нову назву для дисципліни {subject.name}"
        )

    async def on_message(self, update, context):
        text = update.message.text
        db.set_subject_name(self.subject_id, text)
        return Subject(self.subject_id)



@dataclass
class Users(State):
    async def on_enter(self, update, context):
        await self.__send_message__(
            update, context, 
            "Користувачі",
            InlineKeyboardMarkup(
                [[InlineKeyboardButton(f"{user.surname} - {user.telegram_id}", callback_data=user.id)] for user in db.get_users()]
                +
                [[InlineKeyboardButton("Назад", callback_data="Back")]]
            )
        )

    async def on_callback(self, update, context):
        data = update.callback_query.data
        await update.callback_query.answer()

        if data == "Back":
            return Admin()
        
        elif "superadmin" in db.get_user_by_id(data).roles and "superadmin" not in db.get_user_by_telegram(update.effective_user.id).roles:
            return Home()
        
        else:
            return User(data)



@dataclass
class User(State):
    user_id: int

    async def on_enter(self, update, context):
        user = db.get_user_by_id(self.user_id)
        await self.__send_message__(
            update, context,
            f"Вибери дію для {user.surname} - {user.telegram_id}",
            InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(("🟢" if "student" in user.roles else "🔴") + "Студент", callback_data="student"),
                    InlineKeyboardButton(("🟢" if "dutier" in user.roles else "🔴") + "Черговий", callback_data="dutier"),
                    InlineKeyboardButton(("🟢" if "admin" in user.roles else "🔴") + "Адмін", callback_data="admin")
                ],
                [
                    InlineKeyboardButton("Змінити прізвище", callback_data="ChangeSurname")
                ],
                [
                    InlineKeyboardButton("Назад", callback_data="Back")
                ]
            ])
        )
    
    async def on_callback(self, update, context):
        data = update.callback_query.data
        await update.callback_query.answer()

        if data == "Back":
            return Users()
        
        elif data == "ChangeSurname":
            return UserChangeSurname(self.user_id)
        
        elif data in ["student", "admin", "dutier"]:
            if data in db.get_user_by_id(self.user_id).roles:
                db.remove_role(self.user_id, data)
                return User(self.user_id)
            else:
                db.add_role(self.user_id, data)
                return User(self.user_id)



@dataclass
class UserChangeSurname(State):
    user_id: int
    
    async def on_enter(self, update, context):
        user = db.get_user_by_id(self.user_id)
        await self.__send_message__(
            update, context,
            f"Надішли нове ім'я користувача {user.surname} - {user.telegram_id}"
        )

    async def on_message(self, update, context):
        text = update.message.text
        surname = text.capitalize()
        db.set_user_surname(self.user_id, surname)
        return User(self.user_id)