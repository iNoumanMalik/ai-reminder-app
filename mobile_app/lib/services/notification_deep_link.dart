import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Opens a specific reminder in the Reminders tab (from notification tap / FCM).
class NotificationDeepLink {
  NotificationDeepLink._();

  static const _prefsKey = 'pending_open_reminder_id';

  static String? _pendingReminderId;

  /// Set from [MainScreen] when the reminders list is ready to navigate.
  static void Function(String reminderId)? onOpenReminder;

  static bool get hasPending =>
      _pendingReminderId != null && _pendingReminderId!.isNotEmpty;

  static String? get pendingReminderId => _pendingReminderId;

  /// Load a reminder id written from a background notification isolate.
  static Future<void> loadFromDisk() async {
    final prefs = await SharedPreferences.getInstance();
    final id = prefs.getString(_prefsKey)?.trim();
    if (id != null && id.isNotEmpty) {
      _pendingReminderId = id;
      debugPrint('NotificationDeepLink: loaded from disk reminder_id=$id');
    }
  }

  /// Persist only (for background isolate); main isolate reads on resume.
  static Future<void> persistForLaunch(String reminderId) async {
    final id = reminderId.trim();
    if (id.isEmpty) return;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefsKey, id);
    debugPrint('NotificationDeepLink: persisted for launch reminder_id=$id');
  }

  /// Store id for cold start before [MainScreen] exists (no navigation yet).
  static Future<void> storePending(String reminderId) async {
    final id = reminderId.trim();
    if (id.isEmpty) return;
    _pendingReminderId = id;
    await _persistToDisk(id);
    debugPrint('NotificationDeepLink: stored pending reminder_id=$id');
    _dispatch(id);
  }

  static void requestOpen(String reminderId) {
    final id = reminderId.trim();
    if (id.isEmpty) return;
    _pendingReminderId = id;
    unawaited(_persistToDisk(id));
    debugPrint('NotificationDeepLink: request open reminder_id=$id');
    _dispatch(id);
  }

  /// Call when [MainScreen] mounts or resumes so a pending id is handled.
  static Future<void> consumePending() async {
    await loadFromDisk();
    final id = _pendingReminderId;
    if (id == null || id.isEmpty) return;
    debugPrint('NotificationDeepLink: consume pending reminder_id=$id');
    _dispatch(id);
  }

  static void _dispatch(String id) {
    final handler = onOpenReminder;
    if (handler != null) {
      _pendingReminderId = null;
      unawaited(_clearDisk());
      handler(id);
    }
  }

  static Future<void> _persistToDisk(String id) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefsKey, id);
  }

  static Future<void> _clearDisk() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_prefsKey);
  }

  static Future<void> clear() async {
    _pendingReminderId = null;
    await _clearDisk();
  }
}
