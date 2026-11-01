package com.example.mediaviewer.util

import android.content.Context
import androidx.compose.runtime.State
import androidx.compose.runtime.mutableStateOf

enum class AppMode {
    SIMPLE,     // Basit Mod: Sadece görüntüleme (düzenleme araçları gizlenir)
    ADVANCED    // Gelişmiş Mod: Tüm düzenleme araçları aktif
}

object SettingsManager {
    private const val PREFS_NAME = "media_viewer_prefs"
    private const val KEY_APP_MODE = "app_display_mode"

    private val _appModeState = mutableStateOf(AppMode.ADVANCED)
    val appModeState: State<AppMode> = _appModeState

    fun init(context: Context) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val saved = prefs.getString(KEY_APP_MODE, AppMode.ADVANCED.name) ?: AppMode.ADVANCED.name
        _appModeState.value = try {
            AppMode.valueOf(saved)
        } catch (_: Exception) {
            AppMode.ADVANCED
        }
    }

    fun setAppMode(context: Context, mode: AppMode) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putString(KEY_APP_MODE, mode.name).apply()
        _appModeState.value = mode
    }

    val isEditingEnabled: Boolean
        get() = _appModeState.value == AppMode.ADVANCED
}
