package com.veyravault.space.ui;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.view.MotionEvent;
import android.view.View;
import java.util.ArrayList;
import java.util.List;

public class PatternLockView extends View {
    public interface OnPatternListener {
        void onPatternComplete(String patternString);
    }

    private final List<Integer> selectedDots = new ArrayList<Integer>();
    private final Paint dotPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint activePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint linePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private float curX, curY;
    private boolean tracking = false;
    private OnPatternListener listener;

    public PatternLockView(Context context) {
        super(context);
        dotPaint.setColor(Color.parseColor("#CBD5E1"));
        dotPaint.setStyle(Paint.Style.FILL);
        activePaint.setColor(Color.parseColor("#2563EB"));
        activePaint.setStyle(Paint.Style.FILL);
        linePaint.setColor(Color.parseColor("#60A5FA"));
        linePaint.setStrokeWidth(12f);
        linePaint.setStyle(Paint.Style.STROKE);
        linePaint.setStrokeCap(Paint.Cap.ROUND);
    }

    public void setOnPatternListener(OnPatternListener l) {
        this.listener = l;
    }

    public void clearPattern() {
        selectedDots.clear();
        invalidate();
    }

    private float getDotX(int idx) {
        int col = idx % 3;
        float step = getWidth() / 4f;
        return step * (col + 1);
    }

    private float getDotY(int idx) {
        int row = idx / 3;
        float step = getHeight() / 4f;
        return step * (row + 1);
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        for (int i = 0; i < selectedDots.size() - 1; i++) {
            int a = selectedDots.get(i);
            int b = selectedDots.get(i + 1);
            canvas.drawLine(getDotX(a), getDotY(a), getDotX(b), getDotY(b), linePaint);
        }
        if (tracking && !selectedDots.isEmpty()) {
            int last = selectedDots.get(selectedDots.size() - 1);
            canvas.drawLine(getDotX(last), getDotY(last), curX, curY, linePaint);
        }
        for (int i = 0; i < 9; i++) {
            boolean sel = selectedDots.contains(i);
            canvas.drawCircle(getDotX(i), getDotY(i), sel ? 28f : 20f, sel ? activePaint : dotPaint);
        }
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        curX = event.getX();
        curY = event.getY();
        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                selectedDots.clear();
                tracking = true;
                checkHit(curX, curY);
                invalidate();
                return true;
            case MotionEvent.ACTION_MOVE:
                checkHit(curX, curY);
                invalidate();
                return true;
            case MotionEvent.ACTION_UP:
                tracking = false;
                invalidate();
                if (listener != null && !selectedDots.isEmpty()) {
                    StringBuilder sb = new StringBuilder();
                    for (int d : selectedDots) sb.append(d);
                    listener.onPatternComplete(sb.toString());
                }
                return true;
        }
        return super.onTouchEvent(event);
    }

    private void checkHit(float x, float y) {
        float radius = Math.min(getWidth(), getHeight()) / 8f;
        for (int i = 0; i < 9; i++) {
            if (!selectedDots.contains(i)) {
                float dx = x - getDotX(i);
                float dy = y - getDotY(i);
                if (Math.sqrt(dx * dx + dy * dy) <= radius) {
                    selectedDots.add(i);
                }
            }
        }
    }
}
