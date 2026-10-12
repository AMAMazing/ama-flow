import re

PWA_MEDIA_KEYWORDS = [
    "netflix",
    "youtube",
    "disney+",
    "disney plus",
    "prime video",
    "amazon prime",
    "hulu",
    "twitch",
    "crunchyroll",
    "max",
    "hbo max",
    "apple tv",
    "spotify"
]

def parse_aspect_ratio(val):
    try:
        v = str(val).replace(":", "/")
        num, den = map(float, v.split("/"))
        return num / den
    except Exception:
        return 16.0 / 9.0

def detect_smart_media_window(open_windows, configured_media_title=None, code_title="Visual Studio Code", chrome_title="Google Chrome"):
    """
    Inspects currently open windows [(title, hwnd), ...] to detect if an active media
    tab/window is open, and returns:
        (detected_title, detected_hwnd, profile_name, ar_str)
    or
        (None, None, None, None) if no media window is found.

    Priority:
      1. Window named "Picture in picture" or "Picture-in-Picture" -> PiP (16:9)
      2. Window containing "MyAEW" -> MYAEW (3:2)
      3. PWA streaming services (Netflix, YouTube, Disney+, etc.) -> App (1.68:1)
      4. Configured media title substring (if specified and open)
    """
    if not open_windows:
        return None, None, None, None

    code_lower = (code_title or "visual studio code").lower()
    chrome_lower = (chrome_title or "google chrome").lower()

    # Rule 1: Window named "Picture in picture" or "Picture-in-Picture"
    for title, hwnd in open_windows:
        tl = title.lower()
        if "picture in picture" in tl or "picture-in-picture" in tl:
            return title, hwnd, "16:9 (PiP)", "16:9"

    # Rule 2: Window containing "MyAEW"
    for title, hwnd in open_windows:
        tl = title.lower()
        if "myaew" in tl:
            return title, hwnd, "MYAEW (3:2)", "3:2"

    # Identify primary VSCode and Chrome windows to prevent treating main browser as media
    primary_code_hwnd = None
    primary_chrome_hwnd = None
    for title, hwnd in open_windows:
        tl = title.lower()
        if not primary_code_hwnd and (code_lower in tl or "visual studio code" in tl):
            primary_code_hwnd = hwnd
        if not primary_chrome_hwnd and (chrome_lower in tl or "google chrome" in tl):
            primary_chrome_hwnd = hwnd

    # Rule 3: PWA versions of Netflix, YouTube, Disney+, etc.
    for title, hwnd in open_windows:
        if hwnd == primary_code_hwnd:
            continue
        tl = title.lower()
        # If it's the only Chrome window and it's regular browsing (e.g. "New Tab - Google Chrome"), skip
        if hwnd == primary_chrome_hwnd and "google chrome" in tl and not any(kw in tl for kw in ["netflix", "youtube", "disney"]):
            continue

        for kw in PWA_MEDIA_KEYWORDS:
            if kw in tl:
                return title, hwnd, "App (1.68:1)", "1.68:1"

    # Rule 4: Configured media title if explicitly provided and open
    if configured_media_title and configured_media_title.strip():
        cfg_lower = configured_media_title.strip().lower()
        for title, hwnd in open_windows:
            if hwnd == primary_code_hwnd or hwnd == primary_chrome_hwnd:
                continue
            if cfg_lower in title.lower():
                return title, hwnd, "16:9 (PiP)", "16:9"

    return None, None, None, None

def calculate_fullscreen_corner_rects(corner_settings, media_profiles, screen_w, screen_h):
    fs_title = corner_settings.get("fullscreen_app", "").strip() or "Main Fullscreen"
    media_title = corner_settings.get("media_app", "").strip() or "Media (Corner)"
    corner = corner_settings.get("corner", "Bottom-Right")
    max_w = int(corner_settings.get("max_width", 720))
    max_h = int(corner_settings.get("max_height", 450))

    active_ar_name = corner_settings.get("active_media_profile")
    ar_str = media_profiles.get(active_ar_name, "16:9")
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
    Computes active zones intelligently based on currently open windows:
      - If no media tab/window is open -> 50/50 split between Chrome and VS Code.
      - If media tab/window is open:
          * "Picture in picture" -> 16:9
          * "MyAEW" -> 3:2
          * PWA (Netflix, YouTube, Disney+, etc.) -> 1.68:1
          * Configured media -> configured ratio
    """
    layout_settings = config_or_data.get("layout_settings", {})
    chrome_sizes = config_or_data.get("chrome_sizes", layout_settings.get("chrome_sizes", {}))
    media_profiles = config_or_data.get("media_profiles", layout_settings.get("media_profiles", {}))
    app_titles = config_or_data.get("app_titles", {})

    # Extract configured titles
    code_title = app_titles.get("vscode") or layout_settings.get("vscode_title") or "Visual Studio Code"
    chrome_title = app_titles.get("chrome") or layout_settings.get("chrome_title") or "Google Chrome"
    configured_media = app_titles.get("media") or layout_settings.get("media_title") or "Picture in picture"

    vscode_side = layout_settings.get("vscode_side", "Right")
    active_profile = layout_settings.get("active_media_profile", "Auto (Smart Detect)")

    # Detect media window
    detected_title, detected_hwnd, profile_name, ar_str = detect_smart_media_window(
        open_windows,
        configured_media_title=configured_media,
        code_title=code_title,
        chrome_title=chrome_title
    )

    is_auto = (active_profile == "Auto (Smart Detect)" or active_profile == "auto")

    # If no media window is detected:
    # 50/50 split between Chrome and VS Code (no media zone)
    if detected_title is None and (is_auto or open_windows is not None):
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

    # Media window is present (or previewing 3-window)
    if is_auto:
        media_val = ar_str or "16:9"
        media_win_title = detected_title or configured_media or "Picture in picture"
    else:
        media_val = media_profiles.get(active_profile, "16:9")
        media_win_title = detected_title or configured_media or "Picture in picture"

    other_side = "Left" if vscode_side == "Right" else "Right"
    top_pos = f"Top-{other_side}"
    bot_pos = f"Bottom-{other_side}"

    active_chrome = layout_settings.get("chrome_sizing", "Equal Size")
    chrome_val = chrome_sizes.get(active_chrome, "equal")

    zones = [
        {
            "window_title": media_win_title,
            "role": "media",
            "pos": bot_pos,
            "stat": "Aspect Ratio",
            "val": media_val
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