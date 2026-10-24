package org.mydailyassistant.reminders;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;
import java.util.HashSet;
import java.util.Set;

public final class ReminderScheduler {
    private static final String PREFS = "mydailyassistant_reminders";
    private static final long DAY = 24L * 60L * 60L * 1000L;
    private static final long HOUR = 60L * 60L * 1000L;
    private static final long HALF_HOUR = 30L * 60L * 1000L;

    private ReminderScheduler() {}

    public static void schedule(Context context, int eventId, String title, long eventMillis) {
        cancelAlarms(context, eventId);
        SharedPreferences prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        prefs.edit().putString("event_" + eventId + "_title", title)
                .putLong("event_" + eventId + "_time", eventMillis).apply();
        long[] offsets = new long[]{DAY, HOUR, HALF_HOUR};
        String[] labels = new String[]{"24 hours", "1 hour", "30 minutes"};
        long now = System.currentTimeMillis();
        AlarmManager alarms = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (alarms == null) return;
        for (int i = 0; i < offsets.length; i++) {
            long triggerAt = eventMillis - offsets[i];
            if (triggerAt <= now) continue;
            int requestCode = eventId * 10 + (i + 1);
            Intent intent = new Intent(context, ReminderReceiver.class);
            intent.putExtra("event_id", eventId);
            intent.putExtra("event_title", title);
            intent.putExtra("reminder_label", labels[i]);
            intent.putExtra("event_millis", eventMillis);
            PendingIntent pending = PendingIntent.getBroadcast(context, requestCode, intent,
                    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S
                    && alarms.canScheduleExactAlarms()) {
                alarms.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, triggerAt, pending);
            } else if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                // Fallback when exact-alarm special access has not been granted.
                alarms.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, triggerAt, pending);
            } else {
                alarms.set(AlarmManager.RTC_WAKEUP, triggerAt, pending);
            }
        }
    }

    public static void cancel(Context context, int eventId) {
        cancelAlarms(context, eventId);
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
                .remove("event_" + eventId + "_title")
                .remove("event_" + eventId + "_time").apply();
    }

    private static void cancelAlarms(Context context, int eventId) {
        AlarmManager alarms = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (alarms == null) return;
        for (int i = 1; i <= 3; i++) {
            Intent intent = new Intent(context, ReminderReceiver.class);
            PendingIntent pending = PendingIntent.getBroadcast(context, eventId * 10 + i, intent,
                    PendingIntent.FLAG_NO_CREATE | PendingIntent.FLAG_IMMUTABLE);
            if (pending != null) {
                alarms.cancel(pending);
                pending.cancel();
            }
        }
    }

    public static boolean canUseExactAlarms(Context context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) return true;
        AlarmManager alarms = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        return alarms != null && alarms.canScheduleExactAlarms();
    }

    public static void openExactAlarmSettings(Context context) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && !canUseExactAlarms(context)) {
            Intent settings = new Intent(android.provider.Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM);
            settings.setData(android.net.Uri.parse("package:" + context.getPackageName()));
            settings.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            context.startActivity(settings);
        }
    }

    public static void rescheduleAll(Context context) {
        SharedPreferences prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        Set<String> keys = new HashSet<>(prefs.getAll().keySet());
        for (String key : keys) {
            if (!key.startsWith("event_") || !key.endsWith("_title")) continue;
            try {
                int id = Integer.parseInt(key.substring(6, key.length() - 6));
                String title = prefs.getString(key, "Event");
                long time = prefs.getLong("event_" + id + "_time", 0L);
                if (time > System.currentTimeMillis()) schedule(context, id, title, time);
                else cancel(context, id);
            } catch (Exception ignored) { }
        }
    }
}
