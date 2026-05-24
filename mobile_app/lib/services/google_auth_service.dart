import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';
import 'package:google_sign_in/google_sign_in.dart';

import '../config/app_config.dart';

/// Signs in with Google via Firebase Auth and returns a Firebase ID token for the API.
class GoogleAuthService {
  GoogleAuthService._();

  static final GoogleSignIn _googleSignIn = GoogleSignIn.instance;
  static bool _initialized = false;

  static Future<void> _ensureInitialized() async {
    if (_initialized) return;
    await _googleSignIn.initialize(
      serverClientId:
          AppConfig.hasGoogleWebClientId ? AppConfig.googleWebClientId : null,
    );
    _initialized = true;
  }

  /// Returns Firebase ID token, or `null` if the user cancelled the picker.
  static Future<String?> signInAndGetIdToken() async {
    if (kIsWeb) {
      throw UnsupportedError('Google sign-in is not configured for web yet.');
    }
    if (defaultTargetPlatform == TargetPlatform.android &&
        !AppConfig.hasGoogleWebClientId) {
      throw StateError(
        'Set GOOGLE_WEB_CLIENT_ID (Firebase Web OAuth client ID). '
        'Run: flutter run --dart-define=GOOGLE_WEB_CLIENT_ID=YOUR_WEB_CLIENT_ID',
      );
    }

    await _ensureInitialized();

    final GoogleSignInAccount googleUser;
    try {
      googleUser = await _googleSignIn.authenticate();
    } on GoogleSignInException catch (e) {
      if (e.code == GoogleSignInExceptionCode.canceled) {
        return null;
      }
      rethrow;
    }
    final googleAuth = googleUser.authentication;
    final idToken = googleAuth.idToken;
    if (idToken == null || idToken.isEmpty) {
      throw StateError(
        'Google did not return an ID token. '
        'Check SHA-1 in Firebase and GOOGLE_WEB_CLIENT_ID on Android.',
      );
    }

    final credential = GoogleAuthProvider.credential(idToken: idToken);
    final userCredential =
        await FirebaseAuth.instance.signInWithCredential(credential);
    final firebaseIdToken = await userCredential.user?.getIdToken(true);
    if (firebaseIdToken == null || firebaseIdToken.isEmpty) {
      throw StateError('Firebase did not return an ID token.');
    }
    return firebaseIdToken;
  }

  static Future<void> signOut() async {
    await Future.wait([
      FirebaseAuth.instance.signOut(),
      _googleSignIn.signOut(),
    ]);
  }
}
