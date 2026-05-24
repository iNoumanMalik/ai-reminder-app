import 'dart:io';
import 'package:flutter/foundation.dart';

class AppConfig {
  static const String backendUrlAndroid = 'http://10.0.2.2:8000';
  static const String backendUrliOS = 'http://127.0.0.1:8000';
  static const String backendUrlProd = 'https://api.aireminder.app';

  /// Firebase Console → Project settings → Web app → OAuth 2.0 client ID.
  /// Required on Android for a valid Google ID token. Pass at build/run time:
  /// `flutter run --dart-define=GOOGLE_WEB_CLIENT_ID=123456789-xxx.apps.googleusercontent.com`
  static const String googleWebClientId = String.fromEnvironment(
    'GOOGLE_WEB_CLIENT_ID',
    defaultValue: '',
  );

  static bool get hasGoogleWebClientId => googleWebClientId.trim().isNotEmpty;

  static String get baseUrl {
    if (kReleaseMode) {
      return backendUrlProd;
    }
    if (Platform.isAndroid) {
      return backendUrlAndroid;
    } else if (Platform.isIOS) {
      return backendUrliOS;
    }
    return backendUrliOS; // Default
  }
}
