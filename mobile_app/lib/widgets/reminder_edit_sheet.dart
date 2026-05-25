import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../models/reminder.dart';

/// Bottom sheet to edit or republish a reminder (task, date, time, repeat).
class ReminderEditSheet extends StatefulWidget {
  const ReminderEditSheet({
    super.key,
    required this.reminder,
    required this.title,
    required this.submitLabel,
    this.defaultToNextHour = false,
  });

  final Reminder reminder;
  final String title;
  final String submitLabel;

  /// When true (republish with past time), default schedule to next whole hour.
  final bool defaultToNextHour;

  static Future<Map<String, dynamic>?> show(
    BuildContext context, {
    required Reminder reminder,
    required String title,
    required String submitLabel,
    bool defaultToNextHour = false,
  }) {
    return showModalBottomSheet<Map<String, dynamic>>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.viewInsetsOf(context).bottom,
        ),
        child: ReminderEditSheet(
          reminder: reminder,
          title: title,
          submitLabel: submitLabel,
          defaultToNextHour: defaultToNextHour,
        ),
      ),
    );
  }

  @override
  State<ReminderEditSheet> createState() => _ReminderEditSheetState();
}

class _ReminderEditSheetState extends State<ReminderEditSheet> {
  late final TextEditingController _taskController;
  late final TextEditingController _repeatController;
  late DateTime _selectedLocal;
  String? _error;

  @override
  void initState() {
    super.initState();
    _taskController = TextEditingController(text: widget.reminder.task);
    _repeatController = TextEditingController(text: widget.reminder.repeat ?? '');
    _selectedLocal = widget.reminder.datetime;
    if (widget.defaultToNextHour) {
      final now = DateTime.now();
      _selectedLocal = DateTime(now.year, now.month, now.day, now.hour + 1);
    }
  }

  @override
  void dispose() {
    _taskController.dispose();
    _repeatController.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _selectedLocal,
      firstDate: DateTime.now().subtract(const Duration(days: 1)),
      lastDate: DateTime.now().add(const Duration(days: 365 * 2)),
    );
    if (picked != null) {
      setState(() {
        _selectedLocal = DateTime(
          picked.year,
          picked.month,
          picked.day,
          _selectedLocal.hour,
          _selectedLocal.minute,
        );
      });
    }
  }

  Future<void> _pickTime() async {
    final picked = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(_selectedLocal),
    );
    if (picked != null) {
      setState(() {
        _selectedLocal = DateTime(
          _selectedLocal.year,
          _selectedLocal.month,
          _selectedLocal.day,
          picked.hour,
          picked.minute,
        );
      });
    }
  }

  void _submit() {
    final task = _taskController.text.trim();
    if (task.isEmpty) {
      setState(() => _error = 'Enter what to remind you about.');
      return;
    }
    if (!_selectedLocal.isAfter(DateTime.now())) {
      setState(() => _error = 'Choose a date and time in the future.');
      return;
    }
    final repeat = _repeatController.text.trim();
    Navigator.pop(context, {
      'task': task,
      'datetime': _selectedLocal.toUtc().toIso8601String(),
      'repeat': repeat.isEmpty ? null : repeat,
    });
  }

  @override
  Widget build(BuildContext context) {
    final dateLabel = DateFormat.yMMMd().format(_selectedLocal);
    final timeLabel = DateFormat.jm().format(_selectedLocal);

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              widget.title,
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _taskController,
              decoration: const InputDecoration(
                labelText: 'Reminder',
                border: OutlineInputBorder(),
              ),
              textCapitalization: TextCapitalization.sentences,
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _pickDate,
                    icon: const Icon(Icons.calendar_today_outlined),
                    label: Text(dateLabel),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _pickTime,
                    icon: const Icon(Icons.schedule_outlined),
                    label: Text(timeLabel),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _repeatController,
              decoration: const InputDecoration(
                labelText: 'Repeat (optional)',
                hintText: 'e.g. daily, weekly',
                border: OutlineInputBorder(),
              ),
            ),
            if (_error != null) ...[
              const SizedBox(height: 8),
              Text(
                _error!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ],
            const SizedBox(height: 20),
            FilledButton(
              onPressed: _submit,
              child: Text(widget.submitLabel),
            ),
          ],
        ),
      ),
    );
  }
}
