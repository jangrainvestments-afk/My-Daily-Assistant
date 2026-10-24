import sqlite3
from pathlib import Path
from datetime import datetime

from kivy.app import App
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from reminder_bridge import request_notification_permission, schedule_event

DATABASE = Path(__file__).parent / "schedule.db"


def initialize_database():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                event_date TEXT NOT NULL,
                event_time TEXT NOT NULL,
                location TEXT DEFAULT ''
            )
        """)


class MyDailyAssistantApp(App):
    def build(self):
        global DATABASE
        if platform == "android":
            DATABASE = Path(self.user_data_dir) / "schedule.db"
        initialize_database()
        request_notification_permission()
        # Rebuild pending alerts from the saved event database whenever the app opens.
        with sqlite3.connect(DATABASE) as conn:
            saved_events = conn.execute(
                "SELECT id, title, event_date, event_time FROM events"
            ).fetchall()
        for event_id, title, event_date, event_time in saved_events:
            schedule_event(event_id, title, event_date, event_time)

        self.layout = BoxLayout(orientation="vertical", padding=20, spacing=12)
        self.heading = Label(text="My Daily Assistant", font_size=28, size_hint=(1, 0.2))
        self.layout.add_widget(self.heading)

        add_button = Button(text="Add Event", font_size=20)
        add_button.bind(on_press=self.add_event_form)
        self.layout.add_widget(add_button)

        view_button = Button(text="View Schedule", font_size=20)
        view_button.bind(on_press=self.view_schedule)
        self.layout.add_widget(view_button)

        self.status = Label(text="Your schedule, saved on this device.", font_size=14)
        self.layout.add_widget(self.status)
        return self.layout

    def add_event_form(self, instance):
        form = BoxLayout(orientation="vertical", padding=12, spacing=8)
        title = TextInput(hint_text="Event name", multiline=False)
        date = TextInput(hint_text="Date (YYYY-MM-DD)", multiline=False)
        time = TextInput(hint_text="Time (HH:MM, 24-hour)", multiline=False)
        location = TextInput(hint_text="Location (optional)", multiline=False)
        for field in (title, date, time, location):
            form.add_widget(field)

        save_button = Button(text="Save Event", size_hint=(1, 0.8))
        form.add_widget(save_button)
        popup = Popup(title="Add New Event", content=form, size_hint=(0.9, 0.85))

        def save_event(instance):
            if not title.text.strip():
                self.show_message("Please enter an event name.")
                return
            try:
                datetime.strptime(date.text.strip(), "%Y-%m-%d")
                datetime.strptime(time.text.strip(), "%H:%M")
            except ValueError:
                self.show_message("Check the date and time format.\nExample: 2026-10-25 and 14:30")
                return
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.execute("""
                    INSERT INTO events (title, event_date, event_time, location)
                    VALUES (?, ?, ?, ?)
                """, (title.text.strip(), date.text.strip(), time.text.strip(), location.text.strip()))
                event_id = cursor.lastrowid
            schedule_event(event_id, title.text.strip(), date.text.strip(), time.text.strip())
            popup.dismiss()
            self.status.text = "Event saved successfully!"
            self.show_message("Your event has been saved!")

        save_button.bind(on_press=save_event)
        popup.open()

    def view_schedule(self, instance):
        with sqlite3.connect(DATABASE) as conn:
            events = conn.execute("""
                SELECT title, event_date, event_time, location
                FROM events ORDER BY event_date, event_time
            """).fetchall()
        if not events:
            message = "No events yet. Tap Add Event to begin."
        else:
            message = "\n\n".join(
                f"{date} {time}\n{title}\n{location or 'Location not set'}"
                for title, date, time, location in events
            )
        content = BoxLayout(orientation="vertical", padding=12, spacing=10)
        event_label = Label(text=message, halign="left", valign="top")
        event_label.bind(size=lambda widget, size: setattr(widget, "text_size", (size[0], None)))
        content.add_widget(event_label)
        close_button = Button(text="Close", size_hint=(1, 0.2))
        content.add_widget(close_button)
        popup = Popup(title="Your Schedule", content=content, size_hint=(0.9, 0.8))
        close_button.bind(on_press=popup.dismiss)
        popup.open()

    def show_message(self, message):
        Popup(title="My Daily Assistant", content=Label(text=message), size_hint=(0.8, 0.35)).open()


if __name__ == "__main__":
    MyDailyAssistantApp().run()
