package com.resumeplus.jeycode

import android.content.Context
import android.content.Intent
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import me.leolin.shortcutbadger.ShortcutBadger

class MainActivity: FlutterActivity() {
    private val CHANNEL = "resume_plus/badge"

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "isSupported" -> {
                    result.success(true)
                }
                "setBadge" -> {
                    val count = call.argument<Int>("count") ?: 0
                    try {
                        if (count > 0) {
                            ShortcutBadger.applyCount(applicationContext, count)
                        } else {
                            ShortcutBadger.removeCount(applicationContext)
                        }
                        result.success(true)
                    } catch (e: Exception) {
                        // Fallback: utiliser le badge via lanceur natif
                        try {
                            val intent = Intent("android.intent.action.BADGE_COUNT_UPDATE")
                            intent.putExtra("badge_count", count)
                            intent.putExtra("badge_count_package_name", packageName)
                            intent.putExtra("badge_count_class_name", packageManager.getLaunchIntentForPackage(packageName)?.component?.className ?: "")
                            sendBroadcast(intent)
                            result.success(true)
                        } catch (e2: Exception) {
                            result.error("BADGE_ERROR", "Impossible de definir le badge", e2.message)
                        }
                    }
                }
                "removeBadge" -> {
                    try {
                        ShortcutBadger.removeCount(applicationContext)
                    } catch (_: Exception) {}
                    result.success(true)
                }
                else -> result.notImplemented()
            }
        }
    }
}
