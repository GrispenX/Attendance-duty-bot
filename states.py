from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from dataclasses import dataclass
from datetime import datetime



def StrToDate(date_str: str):
    date_str = date_str.strip()
    try:
        return datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError:
        return None



class State:
    async def OnEnter(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        pass

    async def OnMessage(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        pass



@dataclass
class Home(State):
    async def OnEnter(self, update, context):
        await update.message.reply_text(
            "Привіт!\nЯк я можу допомогти?",
            reply_markup=ReplyKeyboardMarkup([
                ["Фото чергування", "Історія чергувань"],
                ["Моя відвідуваність", "Адмін панель"]
            ], resize_keyboard=True, one_time_keyboard=True)
        )

    async def OnMessage(self, update, context):
        text = update.message.text
        
        if text:
            if text == "Фото чергування":
                return DutyPhoto()

            if text == "Історія чергувань":
                return DutyHistoryFrom()
            
            if text == "Моя відвідуваність":
                return MyAttendanceFrom()
            
            if text == "Адмін панель":
                return Admin()
            
        await update.message.reply_text("Моя твоя не поніма")



@dataclass
class DutyPhoto(State):
    async def OnEnter(self, update, context):
        await update.message.reply_text(
            "Надішли мені фото чергування",
            reply_markup=ReplyKeyboardMarkup([
                ["Назад"]
            ], resize_keyboard=True, one_time_keyboard=True)
        )

    async def OnMessage(self, update, context):
        text = update.message.text
        photo = update.message.photo

        if photo:
            file = await context.bot.getFile(photo[-1].file_id)
            curr_date = datetime.now().strftime("%d.%m.%Y")
            await file.download_to_drive(f"{curr_date}.jpg")
            await update.message.reply_text("Фото збережено!")
            return Home()

        elif text == "Назад":
            return Home()
        
        await update.message.reply_text("Я не експерт, але це не схоже на фото. Спробуй ще раз")



@dataclass
class DutyHistoryFrom(State):
    async def OnEnter(self, update, context):
        await update.message.reply_text(
            "Надішли дату з якої почати формувати історію чергувань\nФормат дати: ДД.ММ.РРРР",
            reply_markup=ReplyKeyboardMarkup([
                ["Назад"]
            ], resize_keyboard=True, one_time_keyboard=True)
        )

    async def OnMessage(self, update, context):
        text = update.message.text

        if text:
            if text == "Назад":
                return Home()

            date = StrToDate(text)
            if date:
                return DutyHistoryTo(date)
            
        await update.message.reply_text("Хмм... Нажаль, я не розумію дату яку ти надіслав, вона точно правильна? Спробуй ще раз\nФормат дати: ДД.ММ.РРРР")



@dataclass
class DutyHistoryTo(State):
    from_date: datetime
    async def OnEnter(self, update, context):
        await update.message.reply_text(
            "Чудово!\nТепер наділши дату до якої формувати історію чергувань\nФормат дати: ДД.ММ.РРРР",
            reply_markup=ReplyKeyboardMarkup([
                ["Назад"]
            ], resize_keyboard=True, one_time_keyboard=True)
        )

    async def OnMessage(self, update, context):
        text = update.message.text

        if text:
            if text == "Назад":
                return Home()
            
            to_date = StrToDate(text)
            if to_date:
                await update.message.reply_text(f"*Історія чергувань з {self.from_date} до {to_date}*")
                return Home()
            
        await update.message.reply_text("Хмм... Нажаль, я не розумію дату яку ти надіслав, вона точно правильна? Спробуй ще раз\nФормат дати: ДД.ММ.РРРР")



@dataclass
class MyAttendanceFrom(State):
    async def OnEnter(self, update, context):
        await update.message.reply_text(
            "Надішли дату з якої почати формувати твою відвідуваність\nФормат дати: ДД.ММ.РРРР",
            reply_markup=ReplyKeyboardMarkup([
                ["Назад"]
            ], resize_keyboard=True, one_time_keyboard=True)
        )

    async def OnMessage(self, update, context):
        text = update.message.text

        if text:
            if text == "Назад":
                return Home()
            
            from_date = StrToDate(text)
            if from_date:
                return MyAttendanceTo(from_date)
            
        await update.message.reply_text("Хмм... Нажаль, я не розумію дату яку ти надіслав, вона точно правильна? Спробуй ще раз\nФормат дати: ДД.ММ.РРРР")



@dataclass
class MyAttendanceTo(State):
    from_date: datetime
    
    async def OnEnter(self, update, context):
        await update.message.reply_text(
            "Надішли дату до якої формувати твою відвідуваність\nФормат дати: ДД.ММ.РРРР",
            reply_markup=ReplyKeyboardMarkup([
                ["Назад"]
            ], resize_keyboard=True, one_time_keyboard=True)
        )

    async def OnMessage(self, update, context):
        text = update.message.text

        if text:
            if text == "Назад":
                return Home()
            
            to_date = StrToDate(text)
            if to_date:
                await update.message.reply_text(f"*Відвідуваність з {self.from_date} до {to_date}")
                return Home()
            
        await update.message.reply_text("Хмм... Нажаль, я не розумію дату яку ти надіслав, вона точно правильна? Спробуй ще раз\nФормат дати: ДД.ММ.РРРР")

            


@dataclass
class Admin(State):
    async def OnEnter(self, update, context):
        await update.message.reply_text(
            "Єбать важний хуй бумажний\nВот твоя адмінка",
            reply_markup=ReplyKeyboardMarkup(
                [
                    ["Відвідуваність", "Чергування"],
                    ["Звіти відвідуваності"],
                    ["Дисципліни", "Юзери"],
                    ["Назад"]
                ],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )

    async def OnMessage(self, update, context):
        text = update.message.text

        if text:
            if text == "Відвідуваність":
                return Attendance()
            
            if text == "Чергування":
                return
            
            if text == "Звіти відвідуваності":
                return
            
            if text == "Юзери":
                return
            
            if text == "Назад":
                return Home()
            
        await update.message.reply_text("Моя твоя не поніма")



@dataclass
class Attendance(State):
    async def OnEnter(self, update, context):
        await update.message.reply_text(
            "Заповнення і редагування відвідування студентів\nВибери шо заповнювати",
            reply_markup=ReplyKeyboardMarkup(
                [
                    ["Група за пару", "Студент за пару"],
                    ["Студент за день", "Студент за період"],
                    ["Назад"]
                ],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )

    async def OnMessage(self, update, context):
        text = update.message.text

        if text:
            if text == "Група за пару":
                return
            
            if text == "Студент за пару":
                return
            
            if text == "Студент за день":
                return
            
            if text == "Студент за період":
                return
            
            if text == "Назад":
                return Admin()
            
        await update.message.reply_text("Моя твоя не поніма")
