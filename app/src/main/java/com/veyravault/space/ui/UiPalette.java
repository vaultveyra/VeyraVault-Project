package com.veyravault.space.ui;

import android.content.Context;
import android.content.res.Configuration;
import android.graphics.Color;

/** Centralized semantic colors for programmatic screens in both light and dark themes. */
public final class UiPalette {
    private UiPalette() { }

    public static boolean isDark(Context context) {
        int night = context.getResources().getConfiguration().uiMode
                & Configuration.UI_MODE_NIGHT_MASK;
        return night == Configuration.UI_MODE_NIGHT_YES;
    }

    public static int page(Context context) {
        return color(context, 0xFFF3F5F9, 0xFF0B1220);
    }

    public static int surface(Context context) {
        return color(context, 0xFFFFFFFF, 0xFF1F2937);
    }

    public static int surfaceSecondary(Context context) {
        return color(context, 0xFFF3F4F6, 0xFF334155);
    }

    public static int textPrimary(Context context) {
        return color(context, 0xFF111827, 0xFFF9FAFB);
    }

    public static int textSecondary(Context context) {
        return color(context, 0xFF4B5563, 0xFFCBD5E1);
    }

    public static int muted(Context context) {
        return color(context, 0xFF6B7280, 0xFF94A3B8);
    }

    public static int accent(Context context) {
        return color(context, 0xFF2563EB, 0xFF93C5FD);
    }

    public static int accentSurface(Context context) {
        return color(context, 0xFFDBEAFE, 0xFF1E3A5F);
    }

    public static int success(Context context) {
        return color(context, 0xFF15803D, 0xFF86EFAC);
    }

    public static int successSurface(Context context) {
        return color(context, 0xFFD1FAE5, 0xFF064E3B);
    }

    public static int warning(Context context) {
        return color(context, 0xFFB45309, 0xFFFCD34D);
    }

    public static int error(Context context) {
        return color(context, 0xFFB91C1C, 0xFFFCA5A5);
    }

    public static int border(Context context) {
        return color(context, 0xFFE5E7EB, 0xFF334155);
    }

    /** Maps legacy UI hex values onto semantic colors while retaining unknown status colors. */
    public static int fromLegacyHex(Context context, String value) {
        if (value == null) return textPrimary(context);
        switch (value.toUpperCase(java.util.Locale.ROOT)) {
            case "#FFFFFF": return surface(context);
            case "#F3F5F9":
            case "#F4F6FB": return page(context);
            case "#F3F4F6":
            case "#E5E7EB": return surfaceSecondary(context);
            case "#DBEAFE":
            case "#E8EEFF": return accentSurface(context);
            case "#111827":
            case "#1F2937": return textPrimary(context);
            case "#374151":
            case "#4B5563": return textSecondary(context);
            case "#6B7280":
            case "#9CA3AF": return muted(context);
            case "#2563EB": return accent(context);
            case "#065F46":
            case "#15803D": return success(context);
            case "#D1FAE5": return successSurface(context);
            case "#92400E":
            case "#B45309": return warning(context);
            case "#B91C1C": return error(context);
            default:
                try {
                    return Color.parseColor(value);
                } catch (IllegalArgumentException invalid) {
                    return textPrimary(context);
                }
        }
    }

    private static int color(Context context, int light, int dark) {
        return isDark(context) ? dark : light;
    }
}
