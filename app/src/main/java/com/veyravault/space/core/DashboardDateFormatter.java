package com.veyravault.space.core;

import java.util.Calendar;
import java.util.Locale;
import java.util.TimeZone;

/**
 * Formats the Dashboard's fixed-city dates without changing the device or clone time zone.
 * The Jalali conversion follows the Gregorian/Jalali break-year algorithm and is independent
 * of Android API-level calendar providers.
 */
public final class DashboardDateFormatter {
    private static final String TEHRAN_ZONE = "Asia/Tehran";
    private static final String NEW_YORK_ZONE = "America/New_York";
    private static final int[] BREAK_YEARS = {
            -61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181,
            1210, 1635, 2060, 2097, 2192, 2262, 2324, 2394, 2456, 3178
    };

    private DashboardDateFormatter() { }

    public static String formatTehranJalaliDate(long epochMillis, boolean persianDigits) {
        Calendar calendar = Calendar.getInstance(TimeZone.getTimeZone(TEHRAN_ZONE), Locale.US);
        calendar.setTimeInMillis(epochMillis);
        int[] date = toJalali(calendar.get(Calendar.YEAR),
                calendar.get(Calendar.MONTH) + 1, calendar.get(Calendar.DAY_OF_MONTH));
        return localizeDigits(pad(date[0], 4) + "/" + pad(date[1], 2) + "/"
                + pad(date[2], 2), persianDigits);
    }

    public static String formatNewYorkGregorianDate(long epochMillis, boolean persianDigits) {
        Calendar calendar = Calendar.getInstance(TimeZone.getTimeZone(NEW_YORK_ZONE), Locale.US);
        calendar.setTimeInMillis(epochMillis);
        String date = pad(calendar.get(Calendar.YEAR), 4) + "/"
                + pad(calendar.get(Calendar.MONTH) + 1, 2) + "/"
                + pad(calendar.get(Calendar.DAY_OF_MONTH), 2);
        return localizeDigits(date, persianDigits);
    }

    /** Converts a Gregorian date (month is 1-based) to {Jalali year, month, day}. */
    public static int[] toJalali(int gregorianYear, int gregorianMonth, int gregorianDay) {
        if (gregorianMonth < 1 || gregorianMonth > 12
                || gregorianDay < 1 || gregorianDay > 31) {
            throw new IllegalArgumentException("Invalid Gregorian date");
        }
        int jalaliYear = gregorianYear - 621;
        int[] calculation = jalaliCalendar(jalaliYear);
        int leap = calculation[0];
        int march = calculation[2];
        int dayOffset = gregorianToDayNumber(gregorianYear, gregorianMonth, gregorianDay)
                - gregorianToDayNumber(gregorianYear, 3, march);

        int jalaliMonth;
        int jalaliDay;
        if (dayOffset >= 0) {
            if (dayOffset <= 185) {
                jalaliMonth = 1 + dayOffset / 31;
                jalaliDay = dayOffset % 31 + 1;
                return new int[] {jalaliYear, jalaliMonth, jalaliDay};
            }
            dayOffset -= 186;
        } else {
            jalaliYear--;
            dayOffset += 179;
            if (leap == 1) dayOffset++;
        }

        jalaliMonth = 7 + dayOffset / 30;
        jalaliDay = dayOffset % 30 + 1;
        return new int[] {jalaliYear, jalaliMonth, jalaliDay};
    }

    private static int[] jalaliCalendar(int jalaliYear) {
        int gregorianYear = jalaliYear + 621;
        int leapJalali = -14;
        int previousBreak = BREAK_YEARS[0];
        int jump = 0;

        for (int i = 1; i < BREAK_YEARS.length; i++) {
            int nextBreak = BREAK_YEARS[i];
            jump = nextBreak - previousBreak;
            if (jalaliYear < nextBreak) break;
            leapJalali += (jump / 33) * 8 + Math.floorMod(jump, 33) / 4;
            previousBreak = nextBreak;
        }

        int yearsSinceBreak = jalaliYear - previousBreak;
        leapJalali += (yearsSinceBreak / 33) * 8
                + (Math.floorMod(yearsSinceBreak, 33) + 3) / 4;
        if (Math.floorMod(jump, 33) == 4 && jump - yearsSinceBreak == 4) {
            leapJalali++;
        }

        int leapGregorian = gregorianYear / 4
                - ((gregorianYear / 100 + 1) * 3) / 4 - 150;
        int march = 20 + leapJalali - leapGregorian;

        int adjustedYears = yearsSinceBreak;
        if (jump - adjustedYears < 6) {
            adjustedYears = adjustedYears - jump + (jump + 4) / 33 * 33;
        }
        int leap = Math.floorMod(Math.floorMod(adjustedYears + 1, 33) - 1, 4);
        if (leap == -1) leap = 4;
        return new int[] {leap, gregorianYear, march};
    }

    private static int gregorianToDayNumber(int year, int month, int day) {
        int monthOffset = Math.floorDiv(month - 8, 6);
        int dayNumber = Math.floorDiv(
                (year + monthOffset + 100100) * 1461, 4)
                + Math.floorDiv(153 * Math.floorMod(month + 9, 12) + 2, 5)
                + day - 34840408;
        return dayNumber - Math.floorDiv(
                Math.floorDiv(year + 100100 + monthOffset, 100) * 3, 4) + 752;
    }

    private static String pad(int value, int width) {
        String text = Integer.toString(value);
        StringBuilder result = new StringBuilder();
        for (int i = text.length(); i < width; i++) result.append('0');
        return result.append(text).toString();
    }

    private static String localizeDigits(String value, boolean persianDigits) {
        if (!persianDigits) return value;
        StringBuilder result = new StringBuilder(value.length());
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            result.append(c >= '0' && c <= '9' ? (char) ('\u06F0' + (c - '0')) : c);
        }
        return result.toString();
    }
}
