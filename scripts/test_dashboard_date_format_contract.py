from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
java_source = root / "app/src/main/java/com/veyravault/space/core/DashboardDateFormatter.java"
dashboard_source = (root / "app/src/main/java/com/veyravault/space/ui/DashboardActivity.java").read_text(encoding="utf-8")

# Verify the Dashboard uses fixed IANA zones, a 12-hour display, and date refresh callbacks.
assert "Math.floorDiv" not in (root / "app/src/main/java/com/veyravault/space/core/DashboardDateFormatter.java").read_text(encoding="utf-8")
assert "Math.floorMod" not in (root / "app/src/main/java/com/veyravault/space/core/DashboardDateFormatter.java").read_text(encoding="utf-8")

for marker in (
    'clock.setTimeZone(zoneId)',
    'clock.setFormat24Hour("hh:mm:ss a")',
    'clock.setFormat12Hour("hh:mm:ss a")',
    'clock.setOnTimeChangedListener(view -> updateDate.run())',
    'DashboardDateFormatter.formatTehranJalaliDate(now, fa)',
    'DashboardDateFormatter.formatNewYorkGregorianDate(now, fa)',
    '"Asia/Tehran"',
    '"America/New_York"',
):
    assert marker in dashboard_source, f"Missing Dashboard date/time behavior: {marker}"

# Compile and execute the actual production Java formatter, not a Python reimplementation.
harness = r"""
import com.veyravault.space.core.DashboardDateFormatter;
import java.util.Calendar;
import java.util.TimeZone;

public final class DashboardDateFormatterContract {
    private static void expect(String actual, String expected, String label) {
        if (!expected.equals(actual)) {
            throw new AssertionError(label + ": expected " + expected + " but got " + actual);
        }
    }

    private static long utc(int year, int month, int day, int hour, int minute) {
        Calendar calendar = Calendar.getInstance(TimeZone.getTimeZone("UTC"));
        calendar.clear();
        calendar.set(year, month - 1, day, hour, minute, 0);
        return calendar.getTimeInMillis();
    }

    public static void main(String[] args) {
        expect(date(2025, 3, 20), "1403/12/30", "Esfand leap-day boundary");
        expect(date(2025, 3, 21), "1404/01/01", "Nowruz 1404 boundary");
        expect(date(2024, 3, 20), "1403/01/01", "Nowruz 1403 boundary");
        expect(date(2026, 3, 20), "1404/12/29", "Esfand non-leap boundary");
        expect(date(2026, 3, 21), "1405/01/01", "Nowruz 1405 boundary");
        expect(DashboardDateFormatter.formatTehranJalaliDate(
                utc(2025, 3, 21, 2, 0), false), "1404/01/01",
                "Tehran timezone date selection");
        expect(DashboardDateFormatter.formatNewYorkGregorianDate(
                utc(2025, 3, 21, 2, 0), false), "2025/03/20",
                "New York timezone date selection");
        expect(DashboardDateFormatter.formatTehranJalaliDate(
                utc(2025, 3, 21, 2, 0), true), "۱۴۰۴/۰۱/۰۱",
                "Persian digit localization");
        System.out.println("PASS: Jalali conversion across Nowruz and leap-year boundaries.");
        System.out.println("PASS: Tehran and New York dates use their own IANA time zones.");
        System.out.println("PASS: Persian digit localization is correct.");
    }

    private static String date(int year, int month, int day) {
        int[] result = DashboardDateFormatter.toJalali(year, month, day);
        return String.format(java.util.Locale.US, "%04d/%02d/%02d",
                result[0], result[1], result[2]);
    }
}
"""
with tempfile.TemporaryDirectory(prefix="veyravault-jalali-") as temp:
    temp_path = Path(temp)
    harness_path = temp_path / "DashboardDateFormatterContract.java"
    harness_path.write_text(harness, encoding="utf-8")
    compile_result = subprocess.run(
        ["javac", "-encoding", "UTF-8", "-d", str(temp_path),
         str(java_source), str(harness_path)],
        cwd=root, text=True, capture_output=True
    )
    if compile_result.returncode != 0:
        raise SystemExit(compile_result.stdout + compile_result.stderr)
    run_result = subprocess.run(
        ["java", "-cp", str(temp_path), "DashboardDateFormatterContract"],
        cwd=root, text=True, capture_output=True
    )
    if run_result.returncode != 0:
        raise SystemExit(run_result.stdout + run_result.stderr)
    print(run_result.stdout, end="")
