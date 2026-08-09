import 'package:flutter/material.dart';

import '../services/auth_service.dart';
import '../widgets/app_chrome.dart';
import 'reset_password_screen.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _email = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final email = _email.text.trim();
    if (email.isEmpty) {
      setState(() => _error = 'Enter your email address.');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    final err = await AuthService.forgotPassword(email);
    if (!mounted) return;
    setState(() {
      _busy = false;
      _error = err;
    });
    if (err == null && mounted) {
      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => ResetPasswordScreen(email: email),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return SpeakardoScaffold(
      appBar: AppBar(
        title: const Text(
          'Forgot password',
          style: TextStyle(
            color: AppChrome.ink,
            fontWeight: FontWeight.w800,
          ),
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
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text(
                    'Enter the email for your account. We will send a '
                    '6-digit code to enter here in the app.',
                    style: TextStyle(
                      color: AppChrome.ink,
                      fontSize: 14,
                      height: 1.4,
                    ),
                  ),
                  const SizedBox(height: 20),
                  TextField(
                    controller: _email,
                    keyboardType: TextInputType.emailAddress,
                    autocorrect: false,
                    enabled: !_busy,
                    decoration: AppChrome.inputDecoration(
                      label: 'Email',
                      prefixIcon: const Icon(
                        Icons.email_outlined,
                        color: AppChrome.muted,
                      ),
                    ),
                  ),
                  if (_error != null) ...[
                    const SizedBox(height: 12),
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
                    onPressed: _busy ? null : _submit,
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
                        : const Text('Send code'),
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
