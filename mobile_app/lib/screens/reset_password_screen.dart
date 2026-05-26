import 'package:flutter/material.dart';

import '../services/auth_service.dart';

class ResetPasswordScreen extends StatefulWidget {
  const ResetPasswordScreen({super.key, this.initialToken});

  final String? initialToken;

  @override
  State<ResetPasswordScreen> createState() => _ResetPasswordScreenState();
}

class _ResetPasswordScreenState extends State<ResetPasswordScreen> {
  late final TextEditingController _token;
  final _password = TextEditingController();
  final _confirm = TextEditingController();
  bool _busy = false;
  bool _done = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _token = TextEditingController(text: widget.initialToken ?? '');
  }

  @override
  void dispose() {
    _token.dispose();
    _password.dispose();
    _confirm.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final token = _token.text.trim();
    final password = _password.text;
    final confirm = _confirm.text;
    if (token.isEmpty) {
      setState(() => _error = 'Paste the reset token from your email link.');
      return;
    }
    if (password.length < 8) {
      setState(() => _error = 'Password must be at least 8 characters.');
      return;
    }
    if (password != confirm) {
      setState(() => _error = 'Passwords do not match.');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    final err = await AuthService.resetPassword(token, password);
    if (!mounted) return;
    setState(() {
      _busy = false;
      if (err != null) {
        _error = err;
      } else {
        _done = true;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Reset password')),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 400),
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: _done
                  ? Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Icon(
                          Icons.check_circle_outline,
                          size: 56,
                          color: Theme.of(context).colorScheme.primary,
                        ),
                        const SizedBox(height: 16),
                        Text(
                          'Password updated',
                          style: Theme.of(context).textTheme.titleLarge,
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 12),
                        const Text(
                          'You can sign in with your new password.',
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 24),
                        FilledButton(
                          onPressed: () => Navigator.popUntil(
                            context,
                            (route) => route.isFirst,
                          ),
                          child: const Text('Back to sign in'),
                        ),
                      ],
                    )
                  : ListView(
                      shrinkWrap: true,
                      children: [
                        const Text(
                          'Choose a new password. If you opened the email on '
                          'this device, the token may already be filled in.',
                        ),
                        const SizedBox(height: 16),
                        TextField(
                          controller: _token,
                          enabled: !_busy,
                          decoration: const InputDecoration(
                            labelText: 'Reset token',
                            border: OutlineInputBorder(),
                            helperText: 'From the password reset email link',
                          ),
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: _password,
                          obscureText: true,
                          enabled: !_busy,
                          decoration: const InputDecoration(
                            labelText: 'New password',
                            border: OutlineInputBorder(),
                            helperText: 'At least 8 characters',
                          ),
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: _confirm,
                          obscureText: true,
                          enabled: !_busy,
                          decoration: const InputDecoration(
                            labelText: 'Confirm password',
                            border: OutlineInputBorder(),
                          ),
                        ),
                        if (_error != null) ...[
                          const SizedBox(height: 12),
                          Text(
                            _error!,
                            style: TextStyle(
                              color: Theme.of(context).colorScheme.error,
                            ),
                          ),
                        ],
                        const SizedBox(height: 20),
                        FilledButton(
                          onPressed: _busy ? null : _submit,
                          child: _busy
                              ? const SizedBox(
                                  height: 22,
                                  width: 22,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                  ),
                                )
                              : const Text('Update password'),
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
