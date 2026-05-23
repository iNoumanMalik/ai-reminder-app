import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_provider.dart';
import '../services/reminder_provider.dart';
import '../widgets/reminder_card.dart';

class RemindersScreen extends StatefulWidget {
  const RemindersScreen({Key? key}) : super(key: key);

  @override
  State<RemindersScreen> createState() => _RemindersScreenState();
}

class _RemindersScreenState extends State<RemindersScreen> {
  void _showError(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Theme.of(context).colorScheme.error,
      ),
    );
  }

  Future<void> _loadReminders() async {
    try {
      await context.read<ReminderProvider>().fetchReminders();
    } catch (_) {
      _showError('Could not load reminders. Pull to refresh to try again.');
    }
  }

  Future<void> _completeReminder(String id) async {
    try {
      await context.read<ReminderProvider>().completeReminder(id);
    } catch (_) {
      _showError('Could not update reminder. Please try again.');
    }
  }

  Future<void> _deleteReminder(String id) async {
    try {
      await context.read<ReminderProvider>().deleteReminder(id);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Reminder deleted')),
      );
    } catch (_) {
      _showError('Could not delete reminder. Please try again.');
    }
  }

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadReminders());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Reminders'),
        centerTitle: true,
        actions: [
          IconButton(
            tooltip: 'Sign out',
            icon: const Icon(Icons.logout),
            onPressed: () => context.read<AuthProvider>().logout(),
          ),
        ],
      ),
      body: Consumer<ReminderProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading && provider.reminders.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }

          if (provider.reminders.isEmpty) {
            return const Center(
              child: Text(
                "No reminders yet.\nTry chat to create one!",
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.grey, fontSize: 16),
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: _loadReminders,
            child: ListView.builder(
              itemCount: provider.reminders.length,
              itemBuilder: (context, index) {
                final reminder = provider.reminders[index];
                return ReminderCard(
                  reminder: reminder,
                  onComplete: () => _completeReminder(reminder.id),
                  onDelete: () => _deleteReminder(reminder.id),
                );
              },
            ),
          );
        },
      ),
    );
  }
}
