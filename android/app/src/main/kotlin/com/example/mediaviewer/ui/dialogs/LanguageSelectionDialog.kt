package com.example.mediaviewer.ui.dialogs

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.RadioButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.mediaviewer.R
import com.example.mediaviewer.ui.theme.AccentBlue
import com.example.mediaviewer.ui.theme.DarkSurface
import com.example.mediaviewer.ui.theme.TextPrimary
import com.example.mediaviewer.ui.theme.TextSecondary
import com.example.mediaviewer.util.LanguageManager

@Composable
fun LanguageSelectionDialog(
    onDismiss: () -> Unit,
    onLanguageSelected: (String) -> Unit
) {
    val context = LocalContext.current
    val currentLang = LanguageManager.currentLanguageState.value

    val options = listOf(
        "system" to stringResource(R.string.lang_system),
        "tr" to "Türkçe 🇹🇷",
        "en" to "English 🇬🇧"
    )

    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = DarkSurface,
        shape = RoundedCornerShape(16.dp),
        title = {
            Text(
                text = stringResource(R.string.select_language),
                style = MaterialTheme.typography.titleMedium.copy(
                    fontWeight = FontWeight.Bold,
                    color = TextPrimary
                )
            )
        },
        text = {
            Column(modifier = Modifier.fillMaxWidth()) {
                options.forEach { (code, label) ->
                    val isSelected = currentLang == code
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable {
                                LanguageManager.setLanguage(context, code)
                                onLanguageSelected(code)
                                onDismiss()
                            }
                            .padding(vertical = 8.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        RadioButton(
                            selected = isSelected,
                            onClick = {
                                LanguageManager.setLanguage(context, code)
                                onLanguageSelected(code)
                                onDismiss()
                            },
                            colors = RadioButtonDefaults.colors(selectedColor = AccentBlue)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = label,
                            color = TextPrimary,
                            fontSize = 15.sp,
                            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal
                        )
                    }
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text(stringResource(R.string.close), color = TextSecondary)
            }
        }
    )
}
