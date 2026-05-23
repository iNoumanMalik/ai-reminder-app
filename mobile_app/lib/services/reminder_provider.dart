import 'package:flutter/material.dart';
import '../models/reminder.dart';
import 'api_service.dart';

class ReminderProvider with ChangeNotifier {
  final ApiService _apiService = ApiService();
  List<Reminder> _reminders = [];
  bool _isLoading = false;

  List<Reminder> get reminders => _reminders;
  bool get isLoading => _isLoading;

  Future<void> fetchReminders() async {
    _isLoading = true;
    notifyListeners();

    try {
      final List<dynamic> data = await _apiService.getReminders();
      _reminders = data.map((json) => Reminder.fromJson(json)).toList();
      _reminders.sort((a, b) => a.datetime.compareTo(b.datetime));
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> completeReminder(String id) async {
    await _apiService.completeReminder(id);
    final index = _reminders.indexWhere((r) => r.id == id);
    if (index == -1) return;
    final reminder = _reminders[index];
    _reminders[index] = Reminder(
      id: reminder.id,
      task: reminder.task,
      datetime: reminder.datetime,
      repeat: reminder.repeat,
      status: 'completed',
    );
    notifyListeners();
  }

  Future<void> deleteReminder(String id) async {
    await _apiService.deleteReminder(id);
    _reminders.removeWhere((r) => r.id == id);
    notifyListeners();
  }
}
