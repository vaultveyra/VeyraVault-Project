package com.veyravault.space.core;

import android.content.Context;
import android.location.Location;
import android.location.LocationManager;
import android.os.Build;
import android.os.SystemClock;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.util.TimeZone;

public class VirtualHookManager {

    private static volatile boolean activeMockGps = false;
    private static volatile double activeLat = 0.0;
    private static volatile double activeLng = 0.0;

    public static void installProcessHooks(final Context ctx) {
        try {
            CloneStore.CloneEntry last = CloneStore.getLastActiveLaunch(ctx);
            if (last != null) {
                syncCloneHooks(ctx, last);
            } else {
                CloneStore.GlobalEnvConfig g = CloneStore.getGlobalEnv(ctx);
                if (g.enabled) {
                    applyDeviceProperties(0, g.brand, g.manufacturer, g.model, g.device,
                            g.countryIso, g.simOperator, g.simOperatorName);
                }
            }
            hookSystemLocationManager(ctx);
        } catch (Throwable ignored) {}
    }

    public static void syncCloneHooks(Context ctx, CloneStore.CloneEntry entry) {
        if (entry == null) return;
        boolean masterGps = CloneStore.isMasterMockGpsEnabled(ctx);
        boolean gpsOn = masterGps && entry.mockGpsEnabled;
        activeMockGps = gpsOn;
        activeLat = entry.latitude;
        activeLng = entry.longitude;

        applyEngineLocationHook(entry.packageName, entry.userId, gpsOn, entry.latitude, entry.longitude);

        CloneStore.GlobalEnvConfig g = CloneStore.getGlobalEnv(ctx);
        if (entry.customDeviceEnabled && !entry.deviceModel.isEmpty()) {
            String b = entry.deviceBrand.isEmpty() ? "Samsung" : entry.deviceBrand;
            applyDeviceProperties(entry.userId, b, b, entry.deviceModel, entry.deviceModel,
                    g.countryIso, g.simOperator, g.simOperatorName);
        } else if (g.enabled) {
            applyDeviceProperties(entry.userId, g.brand, g.manufacturer, g.model, g.device,
                    g.countryIso, g.simOperator, g.simOperatorName);
        }
    }

    public static void applyEngineLocationHook(String pkg, int userId, boolean enable, double lat, double lng) {
        String[] mgrClasses = {
            "top.niunaijun.blackbox.fake.frameworks.BLocationManager",
            "com.vcore.fake.frameworks.BLocationManager"
        };
        String[] locClasses = {
            "top.niunaijun.blackbox.entity.location.BLocation",
            "com.vcore.entity.location.BLocation"
        };
        for (int i = 0; i < mgrClasses.length; i++) {
            try {
                Class<?> mgrCls = Class.forName(mgrClasses[i]);
                Object mgr = mgrCls.getMethod("get").invoke(null);
                for (Method m : mgrCls.getMethods()) {
                    if (m.getName().equals("setPattern") && m.getParameterTypes().length == 3) {
                        m.invoke(mgr, userId, pkg, enable ? 2 : 0);
                    }
                }
                if (enable) {
                    Class<?> bLocCls = Class.forName(locClasses[i]);
                    Object bLoc = bLocCls.getConstructor(double.class, double.class).newInstance(lat, lng);
                    for (Method m : mgrCls.getMethods()) {
                        if (m.getName().equals("setLocation") && m.getParameterTypes().length == 3) {
                            m.invoke(mgr, userId, pkg, bLoc);
                        }
                    }
                }
            } catch (Throwable ignored) {}
        }
    }

    public static void applyDeviceProperties(int userId, String brand, String manufacturer, String model,
                                             String device, String countryIso, String simOp, String simOpName) {
        // 1. Direct In-Process android.os.Build reflection override (read by Telegram, Instagram, WhatsApp, etc.)
        setStaticField(Build.class, "BRAND", brand);
        setStaticField(Build.class, "MANUFACTURER", manufacturer);
        setStaticField(Build.class, "MODEL", model);
        setStaticField(Build.class, "PRODUCT", device);
        setStaticField(Build.class, "DEVICE", device);
        setStaticField(Build.class, "HARDWARE", device);
        String fp = brand + "/" + device + "/" + device + ":13/TP1A.220624.014/Veyra200:user/release-keys";
        setStaticField(Build.class, "FINGERPRINT", fp);

        // 2. Push into BlackBox BDeviceManager for the virtual userId
        String[] devMgrs = {
            "top.niunaijun.blackbox.fake.frameworks.BDeviceManager",
            "com.vcore.fake.frameworks.BDeviceManager"
        };
        String[] devCfgs = {
            "top.niunaijun.blackbox.entity.device.BDeviceConfig",
            "com.vcore.entity.device.BDeviceConfig"
        };
        for (int i = 0; i < devMgrs.length; i++) {
            try {
                Class<?> devMgrCls = Class.forName(devMgrs[i]);
                Object devMgr = devMgrCls.getMethod("get").invoke(null);
                Class<?> cfgCls = Class.forName(devCfgs[i]);
                Object cfg = cfgCls.newInstance();
                setObjectField(cfg, "BRAND", brand);
                setObjectField(cfg, "MANUFACTURER", manufacturer);
                setObjectField(cfg, "MODEL", model);
                setObjectField(cfg, "PRODUCT", device);
                setObjectField(cfg, "DEVICE", device);
                setObjectField(cfg, "FINGERPRINT", fp);
                setObjectField(cfg, "locale", countryIso);
                setObjectField(cfg, "simOperator", simOp);
                setObjectField(cfg, "simOperatorName", simOpName);
                setObjectField(cfg, "simCountryIso", countryIso);
                setObjectField(cfg, "networkCountryIso", countryIso);
                for (Method m : devMgrCls.getMethods()) {
                    if (m.getName().equals("setDeviceConfig") && m.getParameterTypes().length == 2) {
                        m.invoke(devMgr, userId, cfg);
                    }
                }
            } catch (Throwable ignored) {}
        }
    }

    private static void hookSystemLocationManager(Context ctx) {
        try {
            LocationManager lm = (LocationManager) ctx.getSystemService(Context.LOCATION_SERVICE);
            if (lm == null) return;
            Field serviceField = LocationManager.class.getDeclaredField("mService");
            serviceField.setAccessible(true);
            final Object originalService = serviceField.get(lm);
            if (originalService == null) return;

            Class<?> iLocMgrCls = Class.forName("android.location.ILocationManager");
            Object proxy = Proxy.newProxyInstance(
                    iLocMgrCls.getClassLoader(),
                    new Class<?>[]{iLocMgrCls},
                    new InvocationHandler() {
                        @Override
                        public Object invoke(Object p, Method method, Object[] args) throws Throwable {
                            if (activeMockGps && (method.getName().equals("getLastLocation")
                                    || method.getName().equals("getLastKnownLocation"))) {
                                return buildSyntheticLocation("gps", activeLat, activeLng);
                            }
                            return method.invoke(originalService, args);
                        }
                    });
            serviceField.set(lm, proxy);
        } catch (Throwable ignored) {}
    }

    public static Location buildSyntheticLocation(String provider, double lat, double lng) {
        Location loc = new Location(provider != null ? provider : LocationManager.GPS_PROVIDER);
        loc.setLatitude(lat);
        loc.setLongitude(lng);
        loc.setAltitude(42.0);
        loc.setAccuracy(3.2f);
        loc.setTime(System.currentTimeMillis());
        if (Build.VERSION.SDK_INT >= 17) {
            loc.setElapsedRealtimeNanos(SystemClock.elapsedRealtimeNanos());
        }
        return loc;
    }

    private static void setStaticField(Class<?> cls, String fieldName, Object value) {
        try {
            Field f = cls.getDeclaredField(fieldName);
            f.setAccessible(true);
            f.set(null, value);
        } catch (Throwable ignored) {}
    }

    private static void setObjectField(Object obj, String name, Object val) {
        try {
            for (Field f : obj.getClass().getDeclaredFields()) {
                if (f.getName().equalsIgnoreCase(name)) {
                    f.setAccessible(true);
                    f.set(obj, val);
                    return;
                }
            }
        } catch (Throwable ignored) {}
    }
}
