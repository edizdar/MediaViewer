package com.example.mediaviewer.util

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.Settings
import androidx.compose.runtime.State
import androidx.compose.runtime.mutableStateOf

enum class AppMode {
    SIMPLE,     // Basit Mod: Sadece görüntüleme (düzenleme araçları gizlenir)
    ADVANCED    // Gelişmiş Mod: Tüm düzenleme araçları aktif
}

object SettingsManager {
    private const val PREFS_NAME = "media_viewer_prefs"
    private const val KEY_APP_MODE = "app_display_mode"
    private const val KEY_CONFIRM_DELETE = "confirm_delete_enabled"

    private val _appModeState = mutableStateOf(AppMode.ADVANCED)
    val appModeState: State<AppMode> = _appModeState

    private val _confirmDeleteState = mutableStateOf(false)
    val confirmDeleteState: State<Boolean> = _confirmDeleteState

    fun init(context: Context) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val saved = prefs.getString(KEY_APP_MODE, AppMode.ADVANCED.name) ?: AppMode.ADVANCED.name
        _appModeState.value = try {
            AppMode.valueOf(saved)
        } catch (_: Exception) {
            AppMode.ADVANCED
        }
        _confirmDeleteState.value = prefs.getBoolean(KEY_CONFIRM_DELETE, false)
    }

    fun setAppMode(context: Context, mode: AppMode) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putString(KEY_APP_MODE, mode.name).apply()
        _appModeState.value = mode
    }

    fun setConfirmDelete(context: Context, enabled: Boolean) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putBoolean(KEY_CONFIRM_DELETE, enabled).apply()
        _confirmDeleteState.value = enabled
    }

    fun hasAllFilesAccess(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            Environment.isExternalStorageManager()
        } else {
            true
        }
    }

    fun openAllFilesAccessSettings(context: Context) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            try {
                val intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION).apply {
                    data = Uri.parse("package:${context.packageName}")
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                }
                context.startActivity(intent)
            } catch (_: Exception) {
                try {
                    val intent = Intent(Settings.ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION).apply {
                        addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    }
                    context.startActivity(intent)
                } catch (_: Exception) {}
            }
        }
    }

    val isEditingEnabled: Boolean
        get() = _appModeState.value == AppMode.ADVANCED
}
