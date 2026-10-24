"""Bridge event CRUD operations to native Android reminder alarms.

Call schedule_event after an event is inserted or updated, and cancel_event
after an event is deleted. On non-Android platforms these functions are safe
no-ops, so desktop development does not require extra packages.
"""
from datetime import datetime
from kivy.utils import platform


def _native():
    if platform != "android":
        return None, None
    from jnius import autoclass
    activity = autoclass("org.kivy.android.PythonActivity").mActivity
    scheduler = autoclass("org.mydailyassistant.reminders.ReminderScheduler")
    return activity, scheduler


def request_notification_permission():
    """Ask Android 13+ for permission to display notifications."""
    if platform != "android":
        return
    try:
        from jnius import autoclass
        activity = autoclass("org.kivy.android.PythonActivity").mActivity
        version = autoclass("android.os.Build$VERSION")
        if version.SDK_INT >= 33:
            activity.requestPermissions(
                ["android.permission.POST_NOTIFICATIONS"], 4107
            )
    except Exception as exc:
        print("Notification permission request failed:", exc)


def schedule_event(event_id, title, event_date, event_time):
    """Replace all pending alerts for this event using its current date/time."""
    try:
        activity, scheduler = _native()
        if activity is None:
            return
        event_dt = datetime.strptime(
            f"{event_date} {event_time}", "%Y-%m-%d %H:%M"
        )
        event_millis = int(event_dt.timestamp() * 1000)
        scheduler.schedule(activity, int(event_id), str(title), event_millis)
    except Exception as exc:
        print("Could not schedule event reminders:", exc)


def cancel_event(event_id):
    """Cancel all pending alerts and stored metadata for a deleted event."""
    try:
        activity, scheduler = _native()
        if activity is not None:
            scheduler.cancel(activity, int(event_id))
    except Exception as exc:
        print("Could not cancel event reminders:", exc)
