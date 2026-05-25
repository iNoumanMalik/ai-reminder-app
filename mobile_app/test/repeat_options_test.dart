import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_app/utils/repeat_options.dart';

void main() {
  test('normalizeRepeatValue maps aliases', () {
    expect(normalizeRepeatValue('every day'), 'daily');
    expect(normalizeRepeatValue('bogus'), isNull);
  });

  test('repeatScheduleSuffix shows label', () {
    expect(repeatScheduleSuffix('daily'), ' · Daily');
    expect(repeatScheduleSuffix(null), isNull);
  });
}
