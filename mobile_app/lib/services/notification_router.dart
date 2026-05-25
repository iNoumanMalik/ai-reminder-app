import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

import 'notification_action_handler.dart';
import 'notification_deep_link.dart';
import 'reminder_notification_service.dart';

const _knownActions = {
  NotificationActionHandler.actionDone,
  NotificationActionHandler.actionSnooze5,
  NotificationActionHandler.actionSnooze10,
  NotificationActionHandler.actionSnooze30,
};

/// Routes local notification taps: body tap → deep link; action → Done/Snooze.
class NotificationRouter {
  NotificationRouter._();

  static bool isBodyTap(NotificationResponse response) {
    final actionId = response.actionId;
    if (actionId == null || actionId.isEmpty) return true;
    return !_knownActions.contains(actionId);
  }

  /// Cold start: actions run immediately; body tap only stores pending for MainScreen.
  static Future<void> handleLaunchResponse(NotificationResponse response) async {
    final reminderId =
        ReminderNotificationService.reminderIdFromPayload(response.payload);
    if (reminderId == null || reminderId.isEmpty) {
      debugPrint('NotificationRouter: launch missing reminder_id');
      return;
    }

    if (isBodyTap(response)) {
      debugPrint('NotificationRouter: launch body tap reminder_id=$reminderId');
      await NotificationDeepLink.storePending(reminderId);
      return;
    }

    await NotificationActionHandler.processAction(
      actionId: response.actionId,
      reminderId: reminderId,
    );
  }

  static Future<void> handleResponse(NotificationResponse response) async {
    final reminderId =
        ReminderNotificationService.reminderIdFromPayload(response.payload);
    if (reminderId == null || reminderId.isEmpty) {
      debugPrint('NotificationRouter: missing reminder_id in payload');
      return;
    }

    if (isBodyTap(response)) {
      debugPrint('NotificationRouter: tap open reminder_id=$reminderId');
      NotificationDeepLink.requestOpen(reminderId);
      return;
    }

    await NotificationActionHandler.processAction(
      actionId: response.actionId,
      reminderId: reminderId,
    );
  }

  static void handleFcmData(Map<String, dynamic> data) {
    if (data['type'] != 'reminder_due' && data['reminder_id'] == null) {
      return;
    }
    final reminderId = data['reminder_id']?.toString();
    if (reminderId == null || reminderId.isEmpty) return;
    debugPrint('NotificationRouter: FCM open reminder_id=$reminderId');
    NotificationDeepLink.requestOpen(reminderId);
  }
}
