import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

class SpeakardoIcons {
  static const String addCircleBold = 'assets/icons/solar-add-circle-bold.svg';
  static const String addCircleLinear = 'assets/icons/solar-add-circle-linear.svg';
  static const String alarmAddBold = 'assets/icons/solar-alarm-add-bold.svg';
  static const String arrowRightLinear =
      'assets/icons/solar-alt-arrow-right-linear.svg';
  static const String boltCircleBold = 'assets/icons/solar-bolt-circle-bold.svg';
  static const String calendarBold = 'assets/icons/solar-calendar-bold.svg';
  static const String calendarDateLinear =
      'assets/icons/solar-calendar-date-linear.svg';
  static const String calendarLinear = 'assets/icons/solar-calendar-linear.svg';
  static const String calendarMinimalisticLinear =
      'assets/icons/solar-calendar-minimalistic-linear.svg';
  static const String chatDotsBold =
      'assets/icons/solar-chat-round-dots-bold.svg';
  static const String chatLineLinear =
      'assets/icons/solar-chat-round-line-linear.svg';
  static const String checkCircleBold =
      'assets/icons/solar-check-circle-bold.svg';
  static const String checkReadBold = 'assets/icons/solar-check-read-bold.svg';
  static const String checkReadLinear =
      'assets/icons/solar-check-read-linear.svg';
  static const String cupFirstBold = 'assets/icons/solar-cup-first-bold.svg';
  static const String documentTextLinear =
      'assets/icons/solar-document-text-linear.svg';
  static const String dumbbellBold = 'assets/icons/solar-dumbbell-bold.svg';
  static const String filterLinear = 'assets/icons/solar-filter-linear.svg';
  static const String folderPathConnectBold =
      'assets/icons/solar-folder-path-connect-bold.svg';
  static const String hamburgerMenuLinear =
      'assets/icons/solar-hamburger-menu-linear.svg';
  static const String historyBold = 'assets/icons/solar-history-bold.svg';
  static const String lightbulbBold = 'assets/icons/solar-lightbulb-bold.svg';
  static const String magnifierLinear = 'assets/icons/solar-magnifer-linear.svg';
  static const String menuDotsBold = 'assets/icons/solar-menu-dots-bold.svg';
  static const String microphoneBold =
      'assets/icons/solar-microphone-3-bold.svg';
  static const String paperclipLinear = 'assets/icons/solar-paperclip-linear.svg';
  static const String phoneCallingLinear =
      'assets/icons/solar-phone-calling-linear.svg';
  static const String settingsLinear = 'assets/icons/solar-settings-linear.svg';
  static const String shieldCheckBold =
      'assets/icons/solar-shield-check-bold.svg';
  static const String userSpeakBold =
      'assets/icons/solar-user-speak-bold.svg';
  static const String brain = 'assets/icons/mdi-brain.svg';
}

class SpeakardoSvgIcon extends StatelessWidget {
  const SpeakardoSvgIcon(
    this.asset, {
    super.key,
    this.size = 24,
    this.color,
  });

  final String asset;
  final double size;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final resolvedColor = color ?? IconTheme.of(context).color;
    return SvgPicture.asset(
      asset,
      width: size,
      height: size,
      colorFilter: resolvedColor == null
          ? null
          : ColorFilter.mode(resolvedColor, BlendMode.srcIn),
    );
  }
}
