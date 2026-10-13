import re

try:
    from .detector import detector, DEFAULT_APP_PROFILES
    from .win_utils import get_open_windows
except (ImportError, ValueError):
    from core.detector import detector, DEFAULT_APP_PROFILES
    from core.win_utils import get_open_windows


def parse_aspect_ratio(val):
    try:
        v = str(val).replace(":", "/")
        num, den = map(float, v.split("/"))
        return num / den
    except Exception:
        return 16.0 / 9.0


def calculate_fullscreen_corner_rects(corner_settings, media_profiles, screen_w, screen_h, detected_ar=None, fs_app_override=None, media_title_override=None):
    fs_title = fs_app_override or corner_settings.get("fullscreen_app", "").strip() or "Visual Studio Code"
    media_title = media_title_override or corner_settings.get("media_app", "").strip() or "Picture in picture"
    corner = corner_settings.get("corner", "Bottom-Right")
    max_w = int(corner_settings.get("max_width", 640))
    max_h = int(corner_settings.get("max_height", 360))

    if detected_ar:
        ar_str = str(detected_ar)
    else:
        active_ar_name = corner_settings.get("active_media_profile", "16:9 (PiP)")
        prof = media_profiles.get(active_ar_name, "16:9")
        if isinstance(prof, dict):
            ar_str = prof.get("aspect_ratio", "16:9")
        else:
            ar_str = str(prof)

    ar = parse_aspect_ratio(ar_str)

    if max_w / max_h > ar:
        mw = int(max_h * ar)
        mh = max_h
    else:
        mw = max_w
        mh = int(max_w / ar)

    mw = max(100, min(mw, screen_w))
    mh = max(100, min(mh, screen_h))

    if corner == "Bottom-Right":
        mx = screen_w - mw
        my = screen_h - mh
    elif corner == "Bottom-Left":
        mx = 0
        my = screen_h - mh
    elif corner == "Top-Right":
        mx = screen_w - mw
        my = 0
    else:  # Top-Left
        mx = 0
        my = 0

    return [
        {
            "window_title": fs_title,
            "role": "fullscreen",
            "pos": "Fullscreen",
            "stat": "Fullscreen",
            "val": "",
            "rect": {
                "x": 0,
                "y": 0,
                "width": screen_w,
                "height": screen_h
            }
        },
        {
            "window_title": media_title,
            "role": "media",
            "pos": corner,
            "stat": f"Aspect Ratio ({ar_str})",
            "val": ar_str,
            "rect": {
                "x": mx,
                "y": my,
                "width": mw,
                "height": mh
            }
        }
    ]


def calculate_rects(zones, screen_w, screen_h, chrome_val="equal"):
    rem_x, rem_y, rem_w, rem_h = 0, 0, screen_w, screen_h

    def get_val(z, max_val, is_width=True):
        stat = z.get("stat", "")
        val = z.get("val", "0")
        try:
            if stat == "Width (px)" and is_width:
                return int(val)
            if stat in ["Height (px)", "Min Height (px)"] and not is_width:
                return int(val)
            if stat == "Width (%)" and is_width:
                return int(max_val * float(val) / 100.0)
            if stat in ["Height (%)", "Min Height (%)"] and not is_width:
                return int(max_val * float(val) / 100.0)
        except Exception:
            pass
        return 0

    def is_fill(z):
        return z.get("pos") == "Fill Space" or z.get("stat") == "Fill (Any)"

    # Pass 1: Explicit Side Snaps (Left, Right, Top, Bottom)
    for z in zones:
        pos = z.get("pos", "")
        if is_fill(z) or pos in ["Top-Left", "Bottom-Left", "Top-Right", "Bottom-Right"]:
            continue

        stat = z.get("stat", "")
        if pos in ["Right", "Left"]:
            if "Aspect Ratio" in stat:
                w = int(rem_h * parse_aspect_ratio(z.get("val", "")))
            else:
                w = get_val(z, rem_w, True) or (rem_w // 2)

            w = max(0, min(w, rem_w))
            if pos == "Right":
                z["rect"] = {"x": rem_x + rem_w - w, "y": rem_y, "width": w, "height": rem_h}
                rem_w -= w
            else:
                z["rect"] = {"x": rem_x, "y": rem_y, "width": w, "height": rem_h}
                rem_x += w
                rem_w -= w

        elif pos in ["Top", "Bottom"]:
            if "Aspect Ratio" in stat:
                h = int(rem_w / parse_aspect_ratio(z.get("val", "")))
            else:
                h = get_val(z, rem_h, False) or (rem_h // 2)

            h = max(0, min(h, rem_h))
            if pos == "Top":
                z["rect"] = {"x": rem_x, "y": rem_y, "width": rem_w, "height": h}
                rem_y += h
                rem_h -= h
            else:
                z["rect"] = {"x": rem_x, "y": rem_y + rem_h - h, "width": rem_w, "height": h}
                rem_h -= h

    # Pass 2: Corner Columns (Left and Right Columns)
    def solve_column(top_zone, bot_zone, col_x, total_h, total_w):
        if not top_zone and not bot_zone:
            return 0

        top_h, bot_h, col_w = 0, 0, 0

        if top_zone and bot_zone:
            top_stat = top_zone.get("stat", "")
            bot_stat = bot_zone.get("stat", "")

            if "Height" in top_stat and "Aspect Ratio" in bot_stat:
                ar = parse_aspect_ratio(bot_zone.get("val", ""))
                if chrome_val == "equal":
                    top_h = total_h // 2
                    bot_h = total_h - top_h
                else:
                    raw = str(chrome_val).strip()
                    if "%" in raw:
                        match = re.search(r"(\d+(\.\d+)?)", raw)
                        pct = float(match.group(1)) if match else 50.0
                        top_h = int(total_h * pct / 100.0)
                    else:
                        match = re.search(r"(\d+)", raw)
                        top_h = int(match.group(1)) if match else (get_val(top_zone, total_h, False) or (total_h // 2))
                    bot_h = total_h - top_h
                col_w = int(bot_h * ar)
            elif "Height" in bot_stat and "Aspect Ratio" in top_stat:
                ar = parse_aspect_ratio(top_zone.get("val", ""))
                if chrome_val == "equal":
                    bot_h = total_h // 2
                    top_h = total_h - bot_h
                else:
                    raw = str(chrome_val).strip()
                    if "%" in raw:
                        match = re.search(r"(\d+(\.\d+)?)", raw)
                        pct = float(match.group(1)) if match else 50.0
                        bot_h = int(total_h * pct / 100.0)
                    else:
                        match = re.search(r"(\d+)", raw)
                        bot_h = int(match.group(1)) if match else (get_val(bot_zone, total_h, False) or (total_h // 2))
                    top_h = total_h - bot_h
                col_w = int(top_h * ar)
            elif "Height" in top_stat and "Height" in bot_stat:
                top_h = get_val(top_zone, total_h, False)
                bot_h = get_val(bot_zone, total_h, False)
                col_w = max(get_val(top_zone, total_w, True), get_val(bot_zone, total_w, True)) or (total_w // 2)
            elif "Aspect Ratio" in top_stat and "Aspect Ratio" in bot_stat:
                top_h = total_h // 2
                bot_h = total_h - top_h
                ar_top = parse_aspect_ratio(top_zone.get("val", ""))
                ar_bot = parse_aspect_ratio(bot_zone.get("val", ""))
                col_w = max(int(top_h * ar_top), int(bot_h * ar_bot))
            else:
                top_h = get_val(top_zone, total_h, False) or (total_h // 2)
                bot_h = total_h - top_h
                col_w = max(get_val(top_zone, total_w, True), get_val(bot_zone, total_w, True)) or (total_w // 2)
        elif top_zone:
            top_stat = top_zone.get("stat", "")
            if "Aspect Ratio" in top_stat:
                top_h = total_h
                col_w = int(top_h * parse_aspect_ratio(top_zone.get("val", "")))
            else:
                top_h = get_val(top_zone, total_h, False) or total_h
                col_w = get_val(top_zone, total_w, True) or (total_w // 2)
        elif bot_zone:
            bot_stat = bot_zone.get("stat", "")
            if "Aspect Ratio" in bot_stat:
                bot_h = total_h
                col_w = int(bot_h * parse_aspect_ratio(bot_zone.get("val", "")))
            else:
                bot_h = get_val(bot_zone, total_h, False) or total_h
                col_w = get_val(bot_zone, total_w, True) or (total_w // 2)

        col_w = max(0, min(col_w, total_w))

        if top_zone:
            top_zone["rect"] = {"x": col_x, "y": rem_y, "width": col_w, "height": top_h}
        if bot_zone:
            bot_y = rem_y + (top_h if top_zone else (total_h - bot_h))
            bot_zone["rect"] = {"x": col_x, "y": bot_y, "width": col_w, "height": bot_h}

        return col_w

    # Solve Left Column
    tl_zone = next((z for z in zones if z.get("pos") == "Top-Left"), None)
    bl_zone = next((z for z in zones if z.get("pos") == "Bottom-Left"), None)
    left_w = solve_column(tl_zone, bl_zone, rem_x, rem_h, rem_w)
    rem_x += left_w
    rem_w -= left_w

    # Solve Right Column
    tr_zone = next((z for z in zones if z.get("pos") == "Top-Right"), None)
    br_zone = next((z for z in zones if z.get("pos") == "Bottom-Right"), None)
    right_x = rem_x + rem_w
    right_w = solve_column(tr_zone, br_zone, right_x - min(rem_w, rem_w // 2), rem_h, rem_w)
    if right_w > 0:
        if tr_zone:
            tr_zone["rect"]["x"] = rem_x + rem_w - right_w
        if br_zone:
            br_zone["rect"]["x"] = rem_x + rem_w - right_w
        rem_w -= right_w

    # Pass 3: Fill Remaining Space
    fill_zones = [z for z in zones if "rect" not in z or is_fill(z)]
    if fill_zones:
        n = len(fill_zones)
        fill_w = rem_w // n
        for i, z in enumerate(fill_zones):
            fw = fill_w if i < n - 1 else (rem_w - i * fill_w)
            z["rect"] = {"x": rem_x + i * fill_w, "y": rem_y, "width": max(0, fw), "height": rem_h}

    return zones


def calculate_smart_layout(config_or_data, screen_w, screen_h, open_windows=None):
    """
    Computes active zones based on currently open windows:
      - 2 windows open where 1 is media:
          -> Fullscreen for the open main app (VS Code or Chrome) + Corner Popup for Media (with its aspect ratio).
      - 3 windows open (Media + VS Code + Chrome):
          -> 3-Window Layout (VS Code on one side, Chrome + Media with aspect ratio on the other side).
      - No media window open:
          -> 50/50 split between Chrome and VS Code (or Fullscreen if only 1 is open).
    """
    layout_settings = config_or_data.get("layout_settings", {})
    corner_settings = config_or_data.get("corner_settings", {})
    chrome_sizes = config_or_data.get("chrome_sizes", layout_settings.get("chrome_sizes", {}))
    media_profiles = config_or_data.get("media_profiles", layout_settings.get("media_profiles", {}))
    app_titles = config_or_data.get("app_titles", {})

    code_title = app_titles.get("vscode") or layout_settings.get("vscode_title") or "Visual Studio Code"
    chrome_title = app_titles.get("chrome") or layout_settings.get("chrome_title") or "Google Chrome"

    vscode_side = layout_settings.get("vscode_side", "Right")
    active_profile = layout_settings.get("active_media_profile", "Auto (Smart Detect)")

    is_auto = (active_profile in ["Auto (Smart Detect)", "auto"])

    # Detect media window
    detected_app_name = None
    detected_hwnd = None
    detected_title = None
    matched_ar = "16:9"
    matched_prof = None

    if is_auto:
        detected_app_name, detected_hwnd, detected_title, matched_ar, matched_prof = detector.detect_active_media(media_profiles)
    else:
        prof_data = media_profiles.get(active_profile)
        if isinstance(prof_data, dict):
            matched_ar = prof_data.get("aspect_ratio", "16:9")
        elif isinstance(prof_data, str):
            matched_ar = prof_data
        detected_title = active_profile
        detected_app_name = active_profile

    # Inspect currently open windows to count main apps
    if open_windows is None:
        try:
            open_windows = get_open_windows()
        except Exception:
            open_windows = []

    is_vsc_open = False
    is_chrome_open = False

    for win_title, hwnd in open_windows:
        tl = win_title.lower()
        if "visual studio code" in tl:
            is_vsc_open = True
        elif "google chrome" in tl and not ("picture in picture" in tl or "pip" in tl):
            # Check it's not the detected media window
            if not detected_hwnd or hwnd != detected_hwnd:
                is_chrome_open = True

    # Check if manual mode override
    mode = config_or_data.get("mode", "3_window")
    if mode == "fullscreen_corner" and not is_auto:
        return calculate_fullscreen_corner_rects(corner_settings, media_profiles, screen_w, screen_h)

    # =========================================================================
    # SCENARIO 1: MEDIA IS OPEN
    # =========================================================================
    if detected_app_name:
        media_win_title = detected_title or detected_app_name or "Picture in picture"

        # Case A: ONLY 1 MAIN APP IS OPEN + MEDIA (2 windows total: media + vscode OR media + chrome)
        # -> FULLSCREEN + CORNER POPUP!
        if (is_vsc_open and not is_chrome_open) or (is_chrome_open and not is_vsc_open):
            fs_app_name = code_title if is_vsc_open else chrome_title
            return calculate_fullscreen_corner_rects(
                corner_settings,
                media_profiles,
                screen_w,
                screen_h,
                detected_ar=matched_ar,
                fs_app_override=fs_app_name,
                media_title_override=media_win_title
            )

        # Case B: BOTH CHROME AND VS CODE ARE OPEN (3 windows) OR PREVIEW MODE
        # -> 3-WINDOW SETUP WITH MEDIA ASPECT RATIO
        other_side = "Left" if vscode_side == "Right" else "Right"
        top_pos = f"Top-{other_side}"
        bot_pos = f"Bottom-{other_side}"

        active_chrome = layout_settings.get("chrome_sizing", "432px")
        chrome_val = chrome_sizes.get(active_chrome, "432")

        zones = [
            {
                "window_title": media_win_title,
                "role": "media",
                "pos": bot_pos,
                "stat": "Aspect Ratio",
                "val": matched_ar
            },
            {
                "window_title": chrome_title,
                "role": "chrome",
                "pos": top_pos,
                "stat": "Height (px)" if chrome_val == "equal" else ("Height (%)" if "%" in str(chrome_val) else "Height (px)"),
                "val": "" if chrome_val == "equal" else str(chrome_val)
            },
            {
                "window_title": code_title,
                "role": "vscode",
                "pos": vscode_side,
                "stat": "Fill (Any)",
                "val": ""
            }
        ]
        return calculate_rects(zones, screen_w, screen_h, chrome_val=chrome_val)

    # =========================================================================
    # SCENARIO 2: NO MEDIA OPEN -> 50/50 SPLIT OR FULLSCREEN
    # =========================================================================
    half_w = screen_w // 2
    rem_w = screen_w - half_w

    if vscode_side == "Right":
        chrome_rect = {"x": 0, "y": 0, "width": half_w, "height": screen_h}
        vscode_rect = {"x": half_w, "y": 0, "width": rem_w, "height": screen_h}
        chrome_pos = "Left"
        vscode_pos = "Right"
    else:
        vscode_rect = {"x": 0, "y": 0, "width": half_w, "height": screen_h}
        chrome_rect = {"x": half_w, "y": 0, "width": rem_w, "height": screen_h}
        vscode_pos = "Left"
        chrome_pos = "Right"

    return [
        {
            "window_title": chrome_title,
            "role": "chrome",
            "pos": chrome_pos,
            "stat": "Width (50%)",
            "val": "50%",
            "rect": chrome_rect
        },
        {
            "window_title": code_title,
            "role": "vscode",
            "pos": vscode_pos,
            "stat": "Width (50%)",
            "val": "50%",
            "rect": vscode_rect
        }
    ]