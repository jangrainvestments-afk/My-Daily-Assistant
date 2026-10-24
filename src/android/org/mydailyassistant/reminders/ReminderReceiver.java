package org.mydailyassistant.reminders;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

public class ReminderReceiver extends BroadcastReceiver {
    private static final String CHANNEL_ID = "event_reminders";

    @Override
    public void onReceive(Context context, Intent intent) {
        String title = intent.getStringExtra("event_title");
        String label = intent.getStringExtra("reminder_label");
        long eventMillis = intent.getLongExtra("event_millis", 0L);
        if (title == null) title = "Upcoming event";
        if (label == null) label = "Reminder";
        if (eventMillis <= System.currentTimeMillis()) return;

        NotificationManager manager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager == null) return;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(CHANNEL_ID, "Event reminders",
                    NotificationManager.IMPORTANCE_HIGH);
            channel.setDescription("Alerts before your saved events");
            manager.createNotificationChannel(channel);
        }
        int eventId = intent.getIntExtra("event_id", 0);
        Intent launch = context.getPackageManager().getLaunchIntentForPackage(context.getPackageName());
        PendingIntent contentIntent = null;
        if (launch != null) {
            launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
            contentIntent = PendingIntent.getActivity(context, eventId, launch,
                    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        }
        Notification.Builder builder = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                ? new Notification.Builder(context, CHANNEL_ID)
                : new Notification.Builder(context);
        builder.setSmallIcon(android.R.drawable.ic_popup_reminder)
                .setContentTitle(label + " before: " + title)
                .setContentText("Your event is coming up. Open My Daily Assistant for details.")
                .setAutoCancel(true);
        if (contentIntent != null) builder.setContentIntent(contentIntent);
        int reminderIndex = "24 hours".equals(label) ? 1 : ("1 hour".equals(label) ? 2 : 3);
        manager.notify(eventId * 10 + reminderIndex, builder.build());
    }
}
