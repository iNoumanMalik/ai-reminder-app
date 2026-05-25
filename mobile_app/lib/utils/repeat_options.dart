/// Supported repeat rules (must match backend `repeat_schedule.py`).
class RepeatOption {
  const RepeatOption({
    required this.value,
    required this.label,
    required this.shortLabel,
    required this.hint,
  });

  /// `null` = one-time reminder.
  final String? value;
  final String label;
  final String shortLabel;
  final String hint;
}

const List<RepeatOption> kRepeatOptions = [
  RepeatOption(
    value: null,
    label: 'One time',
    shortLabel: 'One time',
    hint: 'Notifies once at the scheduled date and time',
  ),
  RepeatOption(
    value: 'daily',
    label: 'Daily',
    shortLabel: 'Daily',
    hint: 'Every day at the same time',
  ),
  RepeatOption(
    value: 'weekdays',
    label: 'Weekdays (Mon–Fri)',
    shortLabel: 'Weekdays',
    hint: 'Monday through Friday at the same time',
  ),
  RepeatOption(
    value: 'weekly',
    label: 'Weekly',
    shortLabel: 'Weekly',
    hint: 'Same day each week at the same time',
  ),
  RepeatOption(
    value: 'monthly',
    label: 'Monthly',
    shortLabel: 'Monthly',
    hint: 'Same date each month at the same time',
  ),
];

String? normalizeRepeatValue(String? raw) {
  if (raw == null) return null;
  final cleaned = raw.trim().toLowerCase();
  if (cleaned.isEmpty) return null;
  for (final opt in kRepeatOptions) {
    if (opt.value == cleaned) return cleaned;
  }
  const aliases = {
    'every day': 'daily',
    'each day': 'daily',
    'every week': 'weekly',
    'weekday': 'weekdays',
    'mon-fri': 'weekdays',
    'every month': 'monthly',
  };
  return aliases[cleaned];
}

String? repeatDisplayLabel(String? repeat) {
  final canonical = normalizeRepeatValue(repeat);
  if (canonical == null) return null;
  for (final opt in kRepeatOptions) {
    if (opt.value == canonical) return opt.shortLabel;
  }
  return null;
}

String? repeatScheduleSuffix(String? repeat) {
  final label = repeatDisplayLabel(repeat);
  if (label == null) return null;
  return ' · $label';
}
