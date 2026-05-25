import 'package:flutter/material.dart';
import '../models/reminder.dart';
import '../utils/reminder_grouping.dart';

class ReminderCard extends StatelessWidget {
  final Reminder reminder;
  final DateTime clock;
  final VoidCallback onComplete;
  final VoidCallback onEdit;
  final VoidCallback? onRepublish;
  final VoidCallback onDelete;

  const ReminderCard({
    super.key,
    required this.reminder,
    required this.clock,
    required this.onComplete,
    required this.onEdit,
    this.onRepublish,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final overdue = isReminderOverdue(reminder, clock);
    final scheduleLabel = formatReminderSchedule(reminder, clock);
    final completed = reminder.isCompleted;

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 6, horizontal: 16),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      elevation: 1,
      clipBehavior: Clip.antiAlias,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (overdue)
            Container(
              width: 4,
              color: theme.colorScheme.error,
            ),
          Padding(
            padding: const EdgeInsets.only(left: 4, top: 8, bottom: 8),
            child: _CompactIconButton(
              icon: completed
                  ? Icons.check_circle
                  : Icons.radio_button_unchecked,
              color: completed ? Colors.green : Colors.grey.shade600,
              tooltip: completed ? 'Completed' : 'Mark complete',
              onPressed: completed ? null : onComplete,
            ),
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(0, 12, 4, 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    reminder.displayTask,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w600,
                      decoration:
                          completed ? TextDecoration.lineThrough : null,
                      color: completed
                          ? theme.colorScheme.onSurface.withValues(alpha: 0.55)
                          : theme.colorScheme.onSurface,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    scheduleLabel,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: overdue
                          ? theme.colorScheme.error
                          : theme.colorScheme.onSurfaceVariant,
                      fontWeight: overdue ? FontWeight.w600 : null,
                    ),
                  ),
                  if (reminder.isRepeating) ...[
                    const SizedBox(height: 6),
                    _RepeatChip(label: reminder.repeatLabel ?? 'Repeats'),
                  ],
                ],
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.only(top: 4, right: 4, bottom: 4),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                _CompactIconButton(
                  icon: Icons.edit_outlined,
                  tooltip: 'Edit',
                  onPressed: onEdit,
                ),
                if (onRepublish != null)
                  _CompactIconButton(
                    icon: Icons.notifications_active_outlined,
                    tooltip: 'Republish',
                    onPressed: onRepublish,
                  ),
                _CompactIconButton(
                  icon: Icons.delete_outline,
                  color: Colors.redAccent,
                  tooltip: 'Delete',
                  onPressed: onDelete,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _RepeatChip extends StatelessWidget {
  const _RepeatChip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: theme.colorScheme.primaryContainer.withValues(alpha: 0.5),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.repeat,
            size: 12,
            color: theme.colorScheme.primary,
          ),
          const SizedBox(width: 4),
          Text(
            label,
            style: theme.textTheme.labelSmall?.copyWith(
              color: theme.colorScheme.primary,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

/// Tight tap target for card actions (avoids ListTile trailing gaps).
class _CompactIconButton extends StatelessWidget {
  const _CompactIconButton({
    required this.icon,
    required this.tooltip,
    this.onPressed,
    this.color,
  });

  final IconData icon;
  final String tooltip;
  final VoidCallback? onPressed;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 36,
      height: 36,
      child: IconButton(
        onPressed: onPressed,
        icon: Icon(icon, size: 20, color: color),
        tooltip: tooltip,
        padding: EdgeInsets.zero,
        constraints: const BoxConstraints(minWidth: 36, minHeight: 36),
        visualDensity: VisualDensity.compact,
        style: IconButton.styleFrom(
          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
        ),
      ),
    );
  }
}
