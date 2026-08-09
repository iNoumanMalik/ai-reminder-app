import 'dart:ui';

import 'package:flutter/material.dart';
import 'speakardo_icons.dart';

class AppChrome {
  static const Color primary = Color(0xFF6366F1);
  static const Color accent = Color(0xFF14B8A6);
  static const Color ink = Color(0xFF111827);
  static const Color muted = Color(0xFF64748B);
  static const Color surface = Color(0xFFF8FAFC);
  static const Color line = Color(0xFFE2E8F0);

  static BoxDecoration backgroundDecoration() {
    return const BoxDecoration(
      gradient: RadialGradient(
        center: Alignment.topRight,
        radius: 1.2,
        colors: [
          Color(0xFFEFF6FF),
          Color(0xFFF8FAFC),
          Color(0xFFF7F7F4),
        ],
        stops: [0, 0.55, 1],
      ),
    );
  }

  static ButtonStyle primaryButtonStyle() {
    return FilledButton.styleFrom(
      backgroundColor: primary,
      foregroundColor: Colors.white,
      padding: const EdgeInsets.symmetric(vertical: 15, horizontal: 18),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
    );
  }

  static InputDecoration inputDecoration({
    required String label,
    String? hint,
    String? helperText,
    Widget? prefixIcon,
  }) {
    return InputDecoration(
      labelText: label,
      hintText: hint,
      helperText: helperText,
      prefixIcon: prefixIcon,
      filled: true,
      fillColor: Colors.white.withValues(alpha: 0.72),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(18),
        borderSide: const BorderSide(color: line),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(18),
        borderSide: BorderSide(color: line.withValues(alpha: 0.8)),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(18),
        borderSide: const BorderSide(color: primary, width: 1.5),
      ),
    );
  }
}

class SpeakardoScaffold extends StatelessWidget {
  const SpeakardoScaffold({
    super.key,
    required this.child,
    this.safeArea = true,
    this.bottomNavigationBar,
    this.appBar,
  });

  final Widget child;
  final bool safeArea;
  final Widget? bottomNavigationBar;
  final PreferredSizeWidget? appBar;

  @override
  Widget build(BuildContext context) {
    final content = Container(
      decoration: AppChrome.backgroundDecoration(),
      child: Stack(
        children: [
          const Positioned.fill(child: _GridBackdrop()),
          if (safeArea) SafeArea(child: child) else child,
        ],
      ),
    );

    return Scaffold(
      extendBody: true,
      backgroundColor: AppChrome.surface,
      appBar: appBar,
      body: content,
      bottomNavigationBar: bottomNavigationBar,
    );
  }
}

class _GridBackdrop extends StatelessWidget {
  const _GridBackdrop();

  @override
  Widget build(BuildContext context) {
    return CustomPaint(painter: _GridPainter());
  }
}

class _GridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = AppChrome.line.withValues(alpha: 0.35)
      ..strokeWidth = 0.7;
    const step = 32.0;
    for (double x = 0; x <= size.width; x += step) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), paint);
    }
    for (double y = 0; y <= size.height; y += step) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class GlassPanel extends StatelessWidget {
  const GlassPanel({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(16),
    this.borderRadius = 24,
    this.color,
    this.gradient,
    this.borderColor,
    this.borderWidth = 1.0,
    this.margin,
  });

  final Widget child;
  final EdgeInsetsGeometry padding;
  final double borderRadius;
  final Color? color;
  final Gradient? gradient;
  final Color? borderColor;
  final double borderWidth;
  final EdgeInsetsGeometry? margin;

  @override
  Widget build(BuildContext context) {
    final radius = BorderRadius.circular(borderRadius);
    return Container(
      margin: margin,
      child: ClipRRect(
        borderRadius: radius,
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 18, sigmaY: 18),
          child: Container(
            padding: padding,
            decoration: BoxDecoration(
              color: gradient == null
                  ? (color ?? Colors.white.withValues(alpha: 0.68))
                  : null,
              gradient: gradient,
              borderRadius: radius,
              border: Border.all(
                color: borderColor ?? Colors.white.withValues(alpha: 0.78),
                width: borderWidth,
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.04),
                  blurRadius: 24,
                  offset: const Offset(0, 12),
                ),
              ],
            ),
            child: child,
          ),
        ),
      ),
    );
  }
}

class AppLogoMark extends StatelessWidget {
  const AppLogoMark({super.key, this.size = 42});

  final double size;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: Colors.white,
        border: Border.all(color: AppChrome.primary.withValues(alpha: 0.12)),
        boxShadow: [
          BoxShadow(
            color: AppChrome.primary.withValues(alpha: 0.14),
            blurRadius: 18,
          ),
        ],
      ),
      child: Center(
        child: Container(
          width: size * 0.52,
          height: size * 0.52,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                AppChrome.primary.withValues(alpha: 0.45),
                Colors.white,
                AppChrome.accent.withValues(alpha: 0.4),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class SpeakardoTopBar extends StatelessWidget {
  const SpeakardoTopBar({
    super.key,
    required this.title,
    this.subtitle,
    this.subtitleWidget,
    this.leading,
    this.trailing,
    this.padding = const EdgeInsets.fromLTRB(20, 16, 20, 12),
  });

  final String title;
  final String? subtitle;
  final Widget? subtitleWidget;
  final Widget? leading;
  final Widget? trailing;
  final EdgeInsetsGeometry padding;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: padding,
      child: Row(
        children: [
          leading ?? const AppLogoMark(),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: AppChrome.ink,
                    fontSize: 22,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                if (subtitleWidget != null) ...[
                  const SizedBox(height: 4),
                  subtitleWidget!,
                ] else if (subtitle != null) ...[
                  const SizedBox(height: 3),
                  Text(
                    subtitle!,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: AppChrome.muted,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ],
            ),
          ),
          if (trailing != null) trailing!,
        ],
      ),
    );
  }
}

class RevampedBottomNav extends StatelessWidget {
  const RevampedBottomNav({
    super.key,
    required this.currentIndex,
    required this.onTap,
  });

  final int currentIndex;
  final ValueChanged<int> onTap;

  static const _items = [
    _NavItem(
      'Chat',
      SpeakardoIcons.chatLineLinear,
      SpeakardoIcons.chatDotsBold,
    ),
    _NavItem(
      'Timeline',
      SpeakardoIcons.calendarLinear,
      SpeakardoIcons.calendarBold,
    ),
    _NavItem(
      'Mic',
      SpeakardoIcons.microphoneBold,
      SpeakardoIcons.microphoneBold,
    ),
    _NavItem('Memory', SpeakardoIcons.brain, SpeakardoIcons.brain),
    _NavItem(
      'System',
      SpeakardoIcons.settingsLinear,
      SpeakardoIcons.settingsLinear,
    ),
  ];

  @override
  Widget build(BuildContext context) {
    final isMicActive = currentIndex == 2;
    return Padding(
      padding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
      child: Stack(
        clipBehavior: Clip.none,
        alignment: Alignment.topCenter,
        children: [
          GlassPanel(
            borderRadius: 28,
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: List.generate(_items.length, (index) {
                if (index == 2) {
                  // Reserved for the floating mic button rendered above.
                  return const Expanded(child: SizedBox(height: 58));
                }
                final item = _items[index];
                final active = index == currentIndex;
                return Expanded(
                  child: InkWell(
                    borderRadius: BorderRadius.circular(22),
                    onTap: () => onTap(index),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 220),
                      curve: Curves.easeOutCubic,
                      height: 58,
                      decoration: BoxDecoration(
                        color: active
                            ? AppChrome.primary.withValues(alpha: 0.08)
                            : Colors.transparent,
                        borderRadius: BorderRadius.circular(22),
                      ),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          SpeakardoSvgIcon(
                            active ? item.activeIcon : item.icon,
                            size: 22,
                            color: active ? AppChrome.primary : AppChrome.muted,
                          ),
                          const SizedBox(height: 1),
                          Text(
                            item.label,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                              color: active ? AppChrome.primary : AppChrome.muted,
                              fontSize: 10,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              }),
            ),
          ),
          Positioned(
            top: -10,
            child: _MicButton(
              active: isMicActive,
              onTap: () => onTap(2),
            ),
          ),
        ],
      ),
    );
  }
}

class _MicButton extends StatelessWidget {
  const _MicButton({required this.active, required this.onTap});

  final bool active;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      shape: const CircleBorder(),
      child: InkWell(
        customBorder: const CircleBorder(),
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 220),
          width: 56,
          height: 56,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: AppChrome.primary,
            border: Border.all(color: Colors.white, width: 4),
            boxShadow: [
              BoxShadow(
                color: AppChrome.primary.withValues(alpha: active ? 0.4 : 0.26),
                blurRadius: 22,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: const Center(
            child: SpeakardoSvgIcon(
              SpeakardoIcons.microphoneBold,
              size: 19,
              color: Colors.white,
            ),
          ),
        ),
      ),
    );
  }
}

class _NavItem {
  const _NavItem(this.label, this.icon, this.activeIcon);

  final String label;
  final String icon;
  final String activeIcon;
}

/// Status text preceded by a continuously blinking dot, e.g. "● ACTIVE".
class BlinkingStatusLabel extends StatefulWidget {
  const BlinkingStatusLabel({
    super.key,
    required this.label,
    this.color = AppChrome.primary,
  });

  final String label;
  final Color color;

  @override
  State<BlinkingStatusLabel> createState() => _BlinkingStatusLabelState();
}

class _BlinkingStatusLabelState extends State<BlinkingStatusLabel>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 900),
  )..repeat(reverse: true);
  late final Animation<double> _opacity = Tween<double>(
    begin: 0.25,
    end: 1,
  ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeInOut));

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        FadeTransition(
          opacity: _opacity,
          child: Container(
            width: 7,
            height: 7,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: widget.color,
            ),
          ),
        ),
        const SizedBox(width: 6),
        Text(
          widget.label.toUpperCase(),
          style: TextStyle(
            color: widget.color,
            fontSize: 12,
            fontWeight: FontWeight.w800,
            letterSpacing: 0.4,
          ),
        ),
      ],
    );
  }
}
