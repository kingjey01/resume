import 'package:flutter/material.dart';

/// Widget pour afficher une icône avec un badge (compteur)
/// Similaire au badge des notifications
class BadgeIcon extends StatelessWidget {
  final IconData icon;
  final int badgeCount;
  final Color? badgeColor;
  final Color? badgeTextColor;
  final double badgeSize;

  const BadgeIcon({
    super.key,
    required this.icon,
    required this.badgeCount,
    this.badgeColor,
    this.badgeTextColor,
    this.badgeSize = 20,
  });

  @override
  Widget build(BuildContext context) {
    return Stack(
      clipBehavior: Clip.none,
      children: [
        Icon(icon),
        if (badgeCount > 0)
          Positioned(
            top: -8,
            right: -8,
            child: Container(
              width: badgeSize,
              height: badgeSize,
              decoration: BoxDecoration(
                color: badgeColor ?? Colors.red,
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.2),
                    blurRadius: 4,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Center(
                child: Text(
                  badgeCount > 99 ? '99+' : badgeCount.toString(),
                  style: TextStyle(
                    color: badgeTextColor ?? Colors.white,
                    fontSize: badgeSize * 0.5,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
          ),
      ],
    );
  }
}
