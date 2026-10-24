"""My Daily Assistant: dashboard, event CRUD and offline assistant."""
import sqlite3
from datetime import datetime
from pathlib import Path

from kivy.app import App
from kivy.metrics import dp
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from reminder_bridge import cancel_event, open_exact_alarm_settings, request_notification_permission, schedule_event

DATABASE = Path(__file__).parent / "schedule.db"
BG = (0.035, 0.065, 0.12, 1)
PANEL = (0.075, 0.12, 0.19, 1)
TEAL = (0.12, 0.78, 0.72, 1)
WHITE = (0.93, 0.96, 1, 1)
MUTED = (0.62, 0.69, 0.79, 1)
RED = (0.88, 0.28, 0.34, 1)


def label(text, size=14, color=WHITE, **kwargs):
    return Label(text=str(text), font_size=dp(size), color=color,
                 halign="left", valign="middle", **kwargs)


def button(text, callback, color=PANEL, height=46):
    item = Button(text=text, size_hint_y=None, height=dp(height),
                  background_normal="", background_color=color,
                  color=WHITE, font_size=dp(14))
    item.bind(on_release=callback)
    return item


def initialize_database():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL, event_date TEXT NOT NULL,
            event_time TEXT NOT NULL, location TEXT DEFAULT '')""")


class MyDailyAssistantApp(App):
    def build(self):
        global DATABASE
        if platform == "android":
            DATABASE = Path(self.user_data_dir) / "schedule.db"
        initialize_database()
        self.title = "My Daily Assistant"
        self.root_box = BoxLayout(orientation="vertical", padding=dp(16),
                                  spacing=dp(12))
        self.root_box.canvas.before.clear()
        with self.root_box.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(*BG)
            self._background = Rectangle(pos=self.root_box.pos, size=self.root_box.size)
        self.root_box.bind(pos=self._update_background, size=self._update_background)
        request_notification_permission()
        self.reschedule_saved_events()
        self.show_dashboard()
        return self.root_box

    def _update_background(self, widget, value):
        self._background.pos = widget.pos
        self._background.size = widget.size

    def on_resume(self):
        # Rebuild alarms after returning from Android notification/alarm settings.
        self.reschedule_saved_events()

    def events(self, upcoming_only=False):
        now = datetime.now()
        with sqlite3.connect(DATABASE) as conn:
            rows = conn.execute(
                "SELECT id,title,event_date,event_time,location FROM events "
                "ORDER BY event_date,event_time"
            ).fetchall()
        parsed = []
        for row in rows:
            try:
                when = datetime.strptime(row[2] + " " + row[3], "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            if not upcoming_only or when >= now:
                parsed.append((row, when))
        return parsed

    def reschedule_saved_events(self):
        for row, when in self.events():
            schedule_event(row[0], row[1], row[2], row[3])

    def clear(self):
        self.root_box.clear_widgets()

    def header(self, subtitle):
        head = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(78),
                         spacing=dp(3))
        head.add_widget(label("MY DAILY ASSISTANT", 12, TEAL))
        head.add_widget(label(subtitle, 23, WHITE))
        self.root_box.add_widget(head)

    def show_dashboard(self):
        self.clear()
        self.header("Your day, organised.")
        upcoming = self.events(upcoming_only=True)
        total = len(self.events())
        stats = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(92))
        for caption, value in (("UPCOMING", len(upcoming)), ("SAVED EVENTS", total)):
            tile = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(2))
            with tile.canvas.before:
                from kivy.graphics import Color, RoundedRectangle
                Color(*PANEL)
                tile._tile_bg = RoundedRectangle(pos=tile.pos, size=tile.size, radius=[dp(12)])
            tile.bind(pos=lambda w, p: setattr(w._tile_bg, "pos", p),
                      size=lambda w, s: setattr(w._tile_bg, "size", s))
            tile.add_widget(label(caption, 10, MUTED))
            tile.add_widget(label(value, 26, TEAL))
            stats.add_widget(tile)
        self.root_box.add_widget(stats)
        self.root_box.add_widget(button("+  Add an event", lambda *_: self.event_form(), TEAL))
        self.root_box.add_widget(button("Enable precise reminders", lambda *_: open_exact_alarm_settings()))
        self.root_box.add_widget(button("Ask your assistant", lambda *_: self.show_assistant()))
        self.root_box.add_widget(label("UP NEXT", 12, MUTED, size_hint_y=None, height=dp(24)))
        scroll = ScrollView()
        list_box = GridLayout(cols=1, spacing=dp(8), size_hint_y=None, padding=(0, 0, 0, dp(8)))
        list_box.bind(minimum_height=list_box.setter("height"))
        if not upcoming:
            list_box.add_widget(label("No upcoming events yet. Add one to get started.",
                                      14, MUTED, size_hint_y=None, height=dp(70)))
        for row, when in upcoming[:8]:
            card = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(4),
                             size_hint_y=None, height=dp(105))
            with card.canvas.before:
                from kivy.graphics import Color, RoundedRectangle
                Color(*PANEL)
                card._bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(10)])
            card.bind(pos=lambda w, p: setattr(w._bg, "pos", p),
                      size=lambda w, s: setattr(w._bg, "size", s))
            card.add_widget(label(row[1], 16, WHITE))
            card.add_widget(label(when.strftime("%a, %d %b · %H:%M"), 12, TEAL))
            card.add_widget(label(row[4] or "Location not set", 11, MUTED))
            actions = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(8))
            actions.add_widget(button("Edit / Postpone", lambda *_ , ev=row: self.event_form(ev), PANEL, 30))
            actions.add_widget(button("Delete", lambda *_ , eid=row[0], title=row[1]: self.confirm_delete(eid, title), RED, 30))
            card.add_widget(actions)
            list_box.add_widget(card)
        scroll.add_widget(list_box)
        self.root_box.add_widget(scroll)

    def event_form(self, event=None):
        editing = event is not None
        fields = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        title = TextInput(text=event[1] if editing else "", hint_text="Event name",
                          multiline=False, size_hint_y=None, height=dp(44))
        date = TextInput(text=event[2] if editing else datetime.now().strftime("%Y-%m-%d"),
                         hint_text="Date (YYYY-MM-DD)", multiline=False,
                         size_hint_y=None, height=dp(44))
        time = TextInput(text=event[3] if editing else "12:00", hint_text="Time (HH:MM, 24-hour)",
                         multiline=False, size_hint_y=None, height=dp(44))
        location = TextInput(text=event[4] if editing else "", hint_text="Location (optional)",
                             multiline=False, size_hint_y=None, height=dp(44))
        for field in (title, date, time, location):
            fields.add_widget(field)
        fields.add_widget(label("Editing the date or time automatically reschedules reminders.",
                                11, MUTED, size_hint_y=None, height=dp(36)))
        save = button("Save changes" if editing else "Save event", lambda *_: None, TEAL)
        fields.add_widget(save)
        popup = Popup(title="Edit / Postpone event" if editing else "New event",
                      content=fields, size_hint=(0.92, 0.82))

        def save_event(*_):
            name, d, t, place = title.text.strip(), date.text.strip(), time.text.strip(), location.text.strip()
            if not name:
                self.message("Please enter an event name.")
                return
            try:
                datetime.strptime(d, "%Y-%m-%d")
                datetime.strptime(t, "%H:%M")
                when = datetime.strptime(d + " " + t, "%Y-%m-%d %H:%M")
                if when <= datetime.now():
                    self.message("Please choose a future date and time.")
                    return
            except ValueError:
                self.message("Use date YYYY-MM-DD and time HH:MM.")
                return
            with sqlite3.connect(DATABASE) as conn:
                if editing:
                    conn.execute("UPDATE events SET title=?,event_date=?,event_time=?,location=? WHERE id=?",
                                 (name, d, t, place, event[0]))
                    event_id = event[0]
                else:
                    cur = conn.execute("INSERT INTO events(title,event_date,event_time,location) VALUES(?,?,?,?)",
                                       (name, d, t, place))
                    event_id = cur.lastrowid
            schedule_event(event_id, name, d, t)
            popup.dismiss()
            self.show_dashboard()
            self.message("Event saved; reminders updated.")

        save.unbind(on_release=save.callback) if hasattr(save, "callback") else None
        save.bind(on_release=save_event)
        popup.open()

    def confirm_delete(self, event_id, title):
        content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))
        content.add_widget(label('Delete "' + title + '"?', 15, WHITE))
        content.add_widget(button("Cancel", lambda *_: popup.dismiss()))
        popup = Popup(title="Confirm deletion", content=content, size_hint=(0.85, 0.35))
        def remove(*_):
            with sqlite3.connect(DATABASE) as conn:
                conn.execute("DELETE FROM events WHERE id=?", (event_id,))
            cancel_event(event_id)
            popup.dismiss()
            self.show_dashboard()
            self.message("Event and its pending reminders deleted.")
        content.add_widget(button("Delete event", remove, RED))
        popup.open()

    def show_assistant(self):
        self.clear()
        self.header("Ask your assistant")
        self.root_box.add_widget(label("Works offline for schedule questions.", 13, MUTED))
        self.chat_log = label("Try: “What’s next?”, “What do I have today?”, or “How many events?”",
                              14, WHITE, size_hint_y=1, valign="top")
        self.root_box.add_widget(self.chat_log)
        self.prompt = TextInput(hint_text="Ask about your schedule…", multiline=False,
                                size_hint_y=None, height=dp(48))
        self.root_box.add_widget(self.prompt)
        self.root_box.add_widget(button("Ask", self.answer_prompt, TEAL))
        self.root_box.add_widget(button("Back to dashboard", lambda *_: self.show_dashboard()))

    def answer_prompt(self, *_):
        query = self.prompt.text.strip().lower()
        events = self.events(upcoming_only=True)
        if any(word in query for word in ("today", "tonight")):
            today = datetime.now().date()
            selected = [(row, when) for row, when in events if when.date() == today]
            answer = self.format_events(selected) if selected else "No more events scheduled for today."
        elif any(word in query for word in ("next", "upcoming", "schedule", "event")):
            answer = self.format_events(events[:5]) if events else "You have no upcoming events."
        elif "how many" in query or "count" in query:
            answer = f"You have {len(events)} upcoming event(s)."
        elif "help" in query:
            answer = "Ask about today's events, your next event, upcoming schedule, or event count."
        else:
            answer = "I can answer schedule questions offline. Connected AI and voice are not enabled yet."
        self.chat_log.text = answer

    def format_events(self, events):
        if not events:
            return "No matching events."
        return "\n\n".join(f"{row[1]}\n{when.strftime('%d %b %Y · %H:%M')}\n{row[4] or 'Location not set'}"
                            for row, when in events)

    def message(self, text):
        popup = Popup(title="My Daily Assistant", content=label(text, 14, WHITE),
                      size_hint=(0.84, 0.32))
        popup.open()


if __name__ == "__main__":
    MyDailyAssistantApp().run()
