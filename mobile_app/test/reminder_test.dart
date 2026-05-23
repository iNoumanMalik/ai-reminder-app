import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_app/models/reminder.dart';

void main() {
  test('displayTask title-cases each word', () {
    final reminder = Reminder(
      id: '1',
      task: 'take medicine',
      datetime: DateTime(2026, 5, 23, 21),
      status: 'pending',
    );

    expect(reminder.displayTask, 'Take Medicine');
  });

  test('toTitleCaseWords handles extra spaces', () {
    expect(toTitleCaseWords('  call   mom  '), 'Call Mom');
  });
}
