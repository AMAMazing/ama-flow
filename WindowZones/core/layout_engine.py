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


def calculate_rects(zones, screen_w, screen_h, secondary_val="equal"):
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
                if secondary_val == "equal":
                    top_h = total_h // 2
                    bot_h = total_h - top_h
                else:
                    raw = str(secondary_val).strip()
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
                if secondary_val == "equal":
                    bot_h = total_h // 2
                    top_h = total_h - bot_h
                else:
                    raw = str(secondary_val).strip()
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
    Computes active zones based on currently open windows utilizing Semantic App Roles (Primary/Secondary).
      - Primary App: Takes the large/fill space. (Defaults to VS Code or 1st Chrome window)
      - Secondary App: Takes the shared space alongside Media. (Defaults to 2nd Chrome window)
    """
    layout_settings = config_or_data.get("layout_settings", {})
    corner_settings = config_or_data.get("corner_settings", {})
    
    # Legacy fallbacks
    chrome_sizes = config_or_data.get("chrome_sizes", layout_settings.get("chrome_sizes", {}))
    media_profiles = config_or_data.get("media_profiles", layout_settings.get("media_profiles", {}))
    
    # Semantic Roles Config
    app_roles = layout_settings.get("app_roles", {
        "primary": ["Visual Studio Code", "Google Chrome"],
        "secondary": ["Google Chrome"]
    })
    
    primary_candidates = [a.lower() for a in app_roles.get("primary", ["Visual Studio Code"])]
    secondary_candidates = [a.lower() for a in app_roles.get("secondary", ["Google Chrome"])]

    primary_side = layout_settings.get("primary_side") or layout_settings.get("vscode_side", "Right")
    active_profile = layout_settings.get("active_media_profile", "Auto (Smart Detect)")

    is_auto = (active_profile in ["Auto (Smart Detect)", "auto"])

    # Detect media window
    detected_app_name, detected_hwnd, detected_title = None, None, None
    matched_ar, matched_prof = "16:9", None

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

    primary_hwnd, primary_title = None, None
    secondary_hwnd, secondary_title = None, None

    # 1) Find Primary App
    for cand in primary_candidates:
        if primary_hwnd: break
        for win_title, hwnd in open_windows:
            if detected_hwnd and hwnd == detected_hwnd: continue # Skip media
            if cand in win_title.lower():
                primary_hwnd = hwnd
                primary_title = win_title
                break

    # 2) Find Secondary App (Ensure it's not the exact same window instance as Primary)
    for cand in secondary_candidates:
        if secondary_hwnd: break
        for win_title, hwnd in open_windows:
            if detected_hwnd and hwnd == detected_hwnd: continue # Skip media
            if primary_hwnd and hwnd == primary_hwnd: continue # Skip primary window instance
            if cand in win_title.lower():
                secondary_hwnd = hwnd
                secondary_title = win_title
                break

    is_primary_open = bool(primary_hwnd)
    is_secondary_open = bool(secondary_hwnd)

    # Fallbacks for titles if not open
    if not primary_title:
        primary_title = app_roles.get("primary", ["Visual Studio Code"])[0]
    if not secondary_title:
        secondary_title = app_roles.get("secondary", ["Google Chrome"])[0]

    # Check if manual mode override
    mode = config_or_data.get("mode", "3_window")
    if mode == "fullscreen_corner" and not is_auto:
        return calculate_fullscreen_corner_rects(corner_settings, media_profiles, screen_w, screen_h)

    # =========================================================================
    # SCENARIO 1: MEDIA IS OPEN
    # =========================================================================
    if detected_app_name:
        media_win_title = detected_title or detected_app_name or "Picture in picture"

        # Case A: ONLY 1 MAIN APP IS OPEN + MEDIA (2 windows total)
        # -> FULLSCREEN + CORNER POPUP!
        if (is_primary_open and not is_secondary_open) or (is_secondary_open and not is_primary_open):
            fs_app_name = primary_title if is_primary_open else secondary_title
            return calculate_fullscreen_corner_rects(
                corner_settings,
                media_profiles,
                screen_w,
                screen_h,
                detected_ar=matched_ar,
                fs_app_override=fs_app_name,
                media_title_override=media_win_title
            )

        # Case B: BOTH PRIMARY AND SECONDARY ARE OPEN (3 windows) OR PREVIEW MODE
        # -> 3-WINDOW SETUP WITH MEDIA ASPECT RATIO
        other_side = "Left" if primary_side == "Right" else "Right"
        top_pos = f"Top-{other_side}"
        bot_pos = f"Bottom-{other_side}"

        active_secondary_size = layout_settings.get("secondary_sizing") or layout_settings.get("chrome_sizing", "432px")
        secondary_val = chrome_sizes.get(active_secondary_size, "432")

        zones = [
            {
                "window_title": media_win_title,
                "role": "media",
                "pos": bot_pos,
                "stat": "Aspect Ratio",
                "val": matched_ar
            },
            {
                "window_title": secondary_title,
                "role": "secondary",
                "pos": top_pos,
                "stat": "Height (px)" if secondary_val == "equal" else ("Height (%)" if "%" in str(secondary_val) else "Height (px)"),
                "val": "" if secondary_val == "equal" else str(secondary_val)
            },
            {
                "window_title": primary_title,
                "role": "primary",
                "pos": primary_side,
                "stat": "Fill (Any)",
                "val": ""
            }
        ]
        return calculate_rects(zones, screen_w, screen_h, secondary_val=secondary_val)

    # =========================================================================
    # SCENARIO 2: NO MEDIA OPEN -> 50/50 SPLIT OR FULLSCREEN
    # =========================================================================
    half_w = screen_w // 2
    rem_w = screen_w - half_w

    if primary_side == "Right":
        secondary_rect = {"x": 0, "y": 0, "width": half_w, "height": screen_h}
        primary_rect = {"x": half_w, "y": 0, "width": rem_w, "height": screen_h}
        secondary_pos = "Left"
        primary_pos = "Right"
    else:
        primary_rect = {"x": 0, "y": 0, "width": half_w, "height": screen_h}
        secondary_rect = {"x": half_w, "y": 0, "width": rem_w, "height": screen_h}
        primary_pos = "Left"
        secondary_pos = "Right"

    return [
        {
            "window_title": secondary_title,
            "role": "secondary",
            "pos": secondary_pos,
            "stat": "Width (50%)",
            "val": "50%",
            "rect": secondary_rect
        },
        {
            "window_title": primary_title,
            "role": "primary",
            "pos": primary_pos,
            "stat": "Width (50%)",
            "val": "50%",
            "rect": primary_rect
        }
    ]