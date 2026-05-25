import 'package:intl/intl.dart';

import '../utils/repeat_options.dart';

class Reminder {
  final String id;
  final String task;
  final DateTime datetime;
  final String? repeat;
  final String status;

  Reminder({
    required this.id,
    required this.task,
    required this.datetime,
    this.repeat,
    required this.status,
  });

  factory Reminder.fromJson(Map<String, dynamic> json) {
    final utc = DateTime.parse(json['datetime']);
    return Reminder(
      id: json['id'],
      task: json['task'],
      datetime: utc.toLocal(),
      repeat: json['repeat'],
      status: json['status'],
    );
  }

  String get formattedDate => DateFormat('yyyy-MM-dd').format(datetime);
  String get formattedTime => DateFormat('HH:mm').format(datetime);
  bool get isCompleted => status == 'completed';

  bool get isRepeating => normalizeRepeatValue(repeat) != null;

  String? get repeatLabel => repeatDisplayLabel(repeat);

  bool get canRepublish =>
      status == 'completed' ||
      status == 'triggered' ||
      status == 'failed';

  /// Title-cased task for display in the reminders list.
  String get displayTask => toTitleCaseWords(task);
}

String toTitleCaseWords(String text) {
  if (text.isEmpty) return text;

  return text
      .split(RegExp(r'\s+'))
      .where((word) => word.isNotEmpty)
      .map(
        (word) =>
            '${word[0].toUpperCase()}${word.substring(1).toLowerCase()}',
      )
      .join(' ');
}
