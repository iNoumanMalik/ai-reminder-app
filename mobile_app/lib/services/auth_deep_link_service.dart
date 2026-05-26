import 'dart:async';

import 'package:app_links/app_links.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../screens/reset_password_screen.dart';
import 'auth_service.dart';
import 'profile_provider.dart';

/// Handles `aireminder://verify-email` and `aireminder://reset-password` links.
class AuthDeepLinkService {
  AuthDeepLinkService._();

  static final AppLinks _appLinks = AppLinks();
  static StreamSubscription<Uri>? _subscription;
  static GlobalKey<NavigatorState>? _navigatorKey;

  static Future<void> initialize(GlobalKey<NavigatorState> navigatorKey) async {
    _navigatorKey = navigatorKey;
    final initial = await _appLinks.getInitialLink();
    if (initial != null) {
      await _handleUri(initial);
    }
    await _subscription?.cancel();
    _subscription = _appLinks.uriLinkStream.listen(
      _handleUri,
      onError: (Object e) => debugPrint('AuthDeepLink error: $e'),
    );
  }

  static Future<void> dispose() async {
    await _subscription?.cancel();
    _subscription = null;
    _navigatorKey = null;
  }

  static Future<void> _handleUri(Uri uri) async {
    if (uri.scheme != 'aireminder') return;
    final token = uri.queryParameters['token']?.trim();
    if (token == null || token.isEmpty) return;

    final nav = _navigatorKey?.currentState;
    if (nav == null) return;

    if (uri.host == 'reset-password') {
      nav.push(
        MaterialPageRoute<void>(
          builder: (_) => ResetPasswordScreen(initialToken: token),
        ),
      );
      return;
    }

    if (uri.host == 'verify-email') {
      final err = await AuthService.verifyEmail(token);
      final context = nav.context;
      if (!context.mounted) return;
      if (err == null) {
        try {
          await context.read<ProfileProvider>().fetchProfile();
        } catch (_) {}
      }
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            err ?? 'Email verified. You are all set!',
          ),
          backgroundColor: err != null
              ? Theme.of(context).colorScheme.error
              : null,
        ),
      );
    }
  }
}
