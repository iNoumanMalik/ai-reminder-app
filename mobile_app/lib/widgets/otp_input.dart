import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'app_chrome.dart';

/// Lets a parent screen read the current code or clear all boxes (e.g.
/// after a failed verification attempt) without lifting box-level state up.
class OtpInputController {
  _OtpInputState? _state;

  void _attach(_OtpInputState state) => _state = state;

  void _detach(_OtpInputState state) {
    if (_state == state) _state = null;
  }

  String get text => _state?._currentValue ?? '';

  void clear() => _state?._clear();
}

/// A row of boxed single-digit fields for entering a numeric OTP code.
class OtpInput extends StatefulWidget {
  const OtpInput({
    super.key,
    this.length = 6,
    required this.onChanged,
    required this.onCompleted,
    this.controller,
    this.enabled = true,
    this.autofocus = true,
  });

  final int length;
  final ValueChanged<String> onChanged;
  final ValueChanged<String> onCompleted;
  final OtpInputController? controller;
  final bool enabled;
  final bool autofocus;

  @override
  State<OtpInput> createState() => _OtpInputState();
}

class _OtpInputState extends State<OtpInput> {
  late final List<TextEditingController> _controllers = List.generate(
    widget.length,
    (_) => TextEditingController(),
  );
  late final List<FocusNode> _focusNodes = List.generate(
    widget.length,
    (_) => FocusNode(),
  );
  bool _completedFired = false;

  @override
  void initState() {
    super.initState();
    widget.controller?._attach(this);
  }

  @override
  void dispose() {
    widget.controller?._detach(this);
    for (final controller in _controllers) {
      controller.dispose();
    }
    for (final node in _focusNodes) {
      node.dispose();
    }
    super.dispose();
  }

  String get _currentValue => _controllers.map((c) => c.text).join();

  void _clear() {
    for (final controller in _controllers) {
      controller.clear();
    }
    _completedFired = false;
    if (!mounted) return;
    setState(() {});
    _focusNodes.first.requestFocus();
  }

  void _notifyChanged() {
    final joined = _currentValue;
    widget.onChanged(joined);
    if (joined.length == widget.length) {
      if (!_completedFired) {
        _completedFired = true;
        widget.onCompleted(joined);
      }
    } else {
      _completedFired = false;
    }
  }

  void _handleChanged(int index, String rawValue) {
    final digits = rawValue.replaceAll(RegExp(r'\D'), '');
    if (digits.length > 1) {
      // Multi-digit arrival (paste of the full code): distribute starting
      // at this box instead of leaving the extra digits in one field.
      for (var i = 0; i < digits.length && index + i < widget.length; i++) {
        _controllers[index + i].text = digits[i];
      }
      final next = (index + digits.length).clamp(0, widget.length - 1);
      _focusNodes[next].requestFocus();
    } else {
      if (_controllers[index].text != digits) {
        _controllers[index].text = digits;
      }
      if (digits.isNotEmpty && index < widget.length - 1) {
        _focusNodes[index + 1].requestFocus();
      } else if (digits.isNotEmpty) {
        _focusNodes[index].unfocus();
      }
    }
    _notifyChanged();
  }

  void _handleBackspace(int index) {
    if (_controllers[index].text.isNotEmpty || index == 0) return;
    _focusNodes[index - 1].requestFocus();
    _controllers[index - 1].clear();
    _notifyChanged();
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: List.generate(widget.length, (index) {
        return SizedBox(
          width: 46,
          height: 56,
          child: Focus(
            onKeyEvent: (node, event) {
              if (event is KeyDownEvent &&
                  event.logicalKey == LogicalKeyboardKey.backspace) {
                _handleBackspace(index);
              }
              return KeyEventResult.ignored;
            },
            child: TextField(
              controller: _controllers[index],
              focusNode: _focusNodes[index],
              enabled: widget.enabled,
              autofocus: widget.autofocus && index == 0,
              textAlign: TextAlign.center,
              keyboardType: TextInputType.number,
              inputFormatters: [FilteringTextInputFormatter.digitsOnly],
              style: const TextStyle(
                color: AppChrome.ink,
                fontSize: 22,
                fontWeight: FontWeight.w800,
              ),
              decoration: InputDecoration(
                counterText: '',
                contentPadding: EdgeInsets.zero,
                filled: true,
                fillColor: Colors.white.withValues(alpha: 0.72),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: const BorderSide(color: AppChrome.line),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: BorderSide(
                    color: AppChrome.line.withValues(alpha: 0.8),
                  ),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: const BorderSide(
                    color: AppChrome.primary,
                    width: 1.5,
                  ),
                ),
              ),
              onChanged: (value) => _handleChanged(index, value),
            ),
          ),
        );
      }),
    );
  }
}
