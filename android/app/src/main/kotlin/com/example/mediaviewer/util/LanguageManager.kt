package com.example.mediaviewer.util

import android.content.Context
import android.content.res.Configuration
import android.os.Build
import android.os.LocaleList
import androidx.compose.runtime.State
import androidx.compose.runtime.mutableStateOf
import java.util.Locale

object LanguageManager {
    private const val PREFS_NAME = "media_viewer_prefs"
    private const val KEY_LANGUAGE = "selected_language"

    private val _currentLanguageState = mutableStateOf("system")
    val currentLanguageState: State<String> = _currentLanguageState

    fun init(context: Context) {
        val saved = getSavedLanguage(context)
        _currentLanguageState.value = saved
    }

    fun getSavedLanguage(context: Context): String {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getString(KEY_LANGUAGE, "system") ?: "system"
    }

    fun setLanguage(context: Context, langCode: String) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putString(KEY_LANGUAGE, langCode).apply()
        _currentLanguageState.value = langCode
        applyLocale(context, langCode)
    }

    fun applyLocale(context: Context, langCode: String) {
        val locale = when (langCode) {
            "tr" -> Locale("tr", "TR")
            "en" -> Locale("en", "US")
            else -> Locale.getDefault()
        }
        Locale.setDefault(locale)

        val resources = context.resources
        val config = Configuration(resources.configuration)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            config.setLocales(LocaleList(locale))
        } else {
            config.setLocale(locale)
        }
        resources.updateConfiguration(config, resources.displayMetrics)
    }
}
