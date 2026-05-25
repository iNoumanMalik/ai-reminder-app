import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/message.dart';
import '../services/chat_provider.dart';
import '../services/reminder_provider.dart';
import '../utils/repeat_options.dart';

class MessageBubble extends StatelessWidget {
  final Message message;

  const MessageBubble({
    super.key,
    required this.message,
  });

  @override
  Widget build(BuildContext context) {
    bool isUser = message.isUser;
    final pending = message.pendingReminder;
    final bool showConfirm = pending != null && pending['confirmable'] != false;
    final bool isEdit = pending?['edit_reminder_id'] != null;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0, horizontal: 16.0),
      child: Column(
        crossAxisAlignment: isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          Align(
            alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
            child: Container(
              decoration: BoxDecoration(
                color: isUser ? const Color(0xFF6750A4) : Colors.grey[200],
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(20),
                  topRight: const Radius.circular(20),
                  bottomLeft: isUser ? const Radius.circular(20) : const Radius.circular(0),
                  bottomRight: isUser ? const Radius.circular(0) : const Radius.circular(20),
                ),
              ),
              padding: const EdgeInsets.all(16),
              child: Text(
                message.text,
                style: TextStyle(
                  color: isUser ? Colors.white : Colors.black87,
                  fontSize: 16,
                ),
              ),
            ),
          ),
          if (showConfirm) ...[
            if (_pendingSummary(pending) != null)
              Padding(
                padding: const EdgeInsets.only(top: 6, left: 4),
                child: Text(
                  _pendingSummary(pending)!,
                  style: TextStyle(
                    fontSize: 13,
                    color: Colors.grey.shade700,
                  ),
                ),
              ),
            Padding(
              padding: const EdgeInsets.only(top: 8.0, left: 4.0),
              child: Row(
                children: [
                  ElevatedButton(
                    onPressed: () async {
                      final ok = await context
                          .read<ChatProvider>()
                          .confirmReminder(message.pendingReminder!);
                      if (ok && context.mounted) {
                        // Keep reminders list in sync after chat edit/create.
                        try {
                          // ignore: use_build_context_synchronously
                          await context.read<ReminderProvider>().fetchReminders();
                        } catch (_) {}
                      }
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF6750A4),
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(15),
                      ),
                    ),
                    child: Text(isEdit ? 'Yes, update' : 'Yes, remind me'),
                  ),
                  const SizedBox(width: 8),
                  TextButton(
                    onPressed: () {
                      context.read<ChatProvider>().rejectReminder(message.pendingReminder!);
                    },
                    child: const Text("No"),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  String? _pendingSummary(Map<String, dynamic>? draft) {
    if (draft == null) return null;
    final task = draft['task']?.toString();
    final date = draft['date']?.toString();
    final time = draft['time']?.toString();
    if (task == null || date == null || time == null) return null;
    final repeat = repeatDisplayLabel(draft['repeat']?.toString());
    final repeatPart = repeat != null ? ' · $repeat' : ' · One time';
    return '$task — $date $time$repeatPart';
  }
}

