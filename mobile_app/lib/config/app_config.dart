import 'dart:io';
import 'package:flutter/foundation.dart';

class AppConfig {
  static const String backendUrlAndroid = 'http://10.0.2.2:8000';
  static const String backendUrliOS = 'http://127.0.0.1:8000';
  static const String backendUrlProd = 'https://api.aireminder.app';

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
