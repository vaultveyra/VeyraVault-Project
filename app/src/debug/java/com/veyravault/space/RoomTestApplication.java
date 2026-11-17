package com.veyravault.space;

import android.app.Application;

/**
 * Debug-only application for Room instrumentation. It deliberately avoids starting
 * the virtual-app engine; production Application and startup remain unchanged.
 */
public final class RoomTestApplication extends Application { }
