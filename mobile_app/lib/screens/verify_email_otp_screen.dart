import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/auth_provider.dart';
import '../services/profile_provider.dart';
import '../widgets/app_chrome.dart';
import '../widgets/otp_input.dart';

/// In-app email verification: always sends a fresh code on open (safe —
/// requesting a new code invalidates any prior one), then lets the user
/// type it in without ever leaving the app.
class VerifyEmailOtpScreen extends StatefulWidget {
  const VerifyEmailOtpScreen({super.key});

  @override
  State<VerifyEmailOtpScreen> createState() => _VerifyEmailOtpScreenState();
}

class _VerifyEmailOtpScreenState extends State<VerifyEmailOtpScreen> {
  final _otpController = OtpInputController();
  String _code = '';
  bool _busy = false;
  bool _sending = false;
  bool _verified = false;
  String? _error;
  Timer? _cooldownTimer;
  int _cooldownSeconds = 0;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _sendCode());
  }

  @override
  void dispose() {
    _cooldownTimer?.cancel();
    super.dispose();
  }

  void _startCooldown() {
    _cooldownTimer?.cancel();
    setState(() => _cooldownSeconds = 45);
    _cooldownTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) {
        timer.cancel();
        return;
      }
      setState(() {
        _cooldownSeconds -= 1;
        if (_cooldownSeconds <= 0) {
          timer.cancel();
        }
      });
    });
  }

  Future<void> _sendCode({bool announce = false}) async {
    setState(() {
      _sending = true;
      _error = null;
    });
    final err = await context.read<AuthProvider>().resendVerificationEmail();
    if (!mounted) return;
    setState(() => _sending = false);
    if (err != null) {
      setState(() => _error = err);
      return;
    }
    _startCooldown();
    if (announce) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('A new code was sent to your email.')),
      );
    }
  }

  Future<void> _submit(String code) async {
    if (code.length < 6 || _busy) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    final err = await context.read<AuthProvider>().verifyEmailWithCode(code);
    if (!mounted) return;
    setState(() => _busy = false);
    if (err != null) {
      setState(() => _error = err);
      _otpController.clear();
      _code = '';
      return;
    }
    await context.read<ProfileProvider>().fetchProfile();
    if (!mounted) return;
    setState(() => _verified = true);
  }

  @override
  Widget build(BuildContext context) {
    return SpeakardoScaffold(
      appBar: AppBar(
        title: const Text(
          'Verify email',
          style: TextStyle(color: AppChrome.ink, fontWeight: FontWeight.w800),
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: AppChrome.ink),
      ),
      child: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 400),
            child: GlassPanel(
              borderRadius: 28,
              padding: const EdgeInsets.all(28),
              child: _verified
                  ? Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        const Icon(
                          Icons.check_circle_outline,
                          size: 64,
                          color: AppChrome.accent,
                        ),
                        const SizedBox(height: 20),
                        const Text(
                          'Email verified',
                          style: TextStyle(
                            color: AppChrome.ink,
                            fontSize: 20,
                            fontWeight: FontWeight.w900,
                          ),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 12),
                        const Text(
                          'Your email address is confirmed.',
                          style: TextStyle(
                            color: AppChrome.muted,
                            fontSize: 14,
                            height: 1.4,
                          ),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 24),
                        FilledButton(
                          onPressed: () => Navigator.of(context).pop(),
                          style: AppChrome.primaryButtonStyle(),
                          child: const Text('Continue'),
                        ),
                      ],
                    )
                  : Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Text(
                          _sending
                              ? 'Sending a code to your email...'
                              : 'We sent a 6-digit code to your email. '
                                    'Enter it below to verify your address.',
                          style: const TextStyle(
                            color: AppChrome.ink,
                            fontSize: 14,
                            height: 1.4,
                          ),
                        ),
                        const SizedBox(height: 20),
                        OtpInput(
                          controller: _otpController,
                          enabled: !_busy && !_sending,
                          onChanged: (value) => _code = value,
                          onCompleted: _submit,
                        ),
                        Align(
                          alignment: Alignment.centerRight,
                          child: TextButton(
                            onPressed:
                                (_sending || _cooldownSeconds > 0)
                                ? null
                                : () => _sendCode(announce: true),
                            child: Text(
                              _cooldownSeconds > 0
                                  ? 'Resend code (0:${_cooldownSeconds.toString().padLeft(2, '0')})'
                                  : 'Resend code',
                            ),
                          ),
                        ),
                        if (_error != null) ...[
                          const SizedBox(height: 4),
                          Text(
                            _error!,
                            style: TextStyle(
                              color: Theme.of(context).colorScheme.error,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                        const SizedBox(height: 20),
                        FilledButton(
                          onPressed: _busy ? null : () => _submit(_code),
                          style: AppChrome.primaryButtonStyle(),
                          child: _busy
                              ? const SizedBox(
                                  height: 22,
                                  width: 22,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: Colors.white,
                                  ),
                                )
                              : const Text('Verify'),
                        ),
                      ],
                    ),
            ),
          ),
        ),
      ),
    );
  }
}
