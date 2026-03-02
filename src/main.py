import math
import random
import struct
import sys
import wave
from collections import deque
from pathlib import Path

import pygame

WINDOWED_WIDTH, WINDOWED_HEIGHT = 1000, 620
WIDTH, HEIGHT = WINDOWED_WIDTH, WINDOWED_HEIGHT

FOV = math.radians(70)
MAX_VIEW_DIST = 20.0
RAY_STEP_LIMIT = 128
WALL_HEIGHT_SCALE = 0.56

MOVE_SPEED = 2.35
TURN_SPEED = 2.3
MOUSE_SENSITIVITY = 0.0020
PITCH_SENSITIVITY = 0.0024
MAX_PITCH = 0.7
PITCH_VIEW_SCALE_CANDIDATES = [0.42, 0.36, 0.30, 0.24]
SPRINT_MULTIPLIER = 1.75
SPRINT_MAX = 100.0
SPRINT_DRAIN_PER_SEC = 55.0
SPRINT_REGEN_PER_SEC = 34.0
PLAYER_RADIUS = 0.18
PLAYER_MAX_HP = 160

SHOT_COOLDOWN_MS = 220
PROJECTILE_SPEED = 14.0
PROJECTILE_RADIUS = 0.05
PROJECTILE_LIFETIME_MS = 1400
SCOPED_FOV = math.radians(20)
ADS_SPREAD_MULT = 0.35
ADS_MOVE_MULT = 0.62
WEAPON_SWITCH_ANIM_MS = 220
WEAPON_ORDER = ["shotgun", "sniper", "smg"]

WEAPONS = {
    "shotgun": {
        "label": "Shotgun",
        "cooldown_ms": 650,
        "damage": 2,
        "pellets": 7,
        "spread_deg": 12.0,
        "auto": False,
        "crosshair": 22,
        "scope": False,
        "ads_fov_mult": 0.78,
        "color": (112, 84, 64),
        "proj_speed_mult": 0.9,
        "max_range": 6.0,
        "ammo_max": 64,
        "ammo_pickup": 16,
    },
    "sniper": {
        "label": "Sniper",
        "cooldown_ms": 950,
        "damage": 16,
        "pellets": 1,
        "spread_deg": 0.2,
        "auto": False,
        "crosshair": 7,
        "scope": True,
        "ads_fov_mult": SCOPED_FOV / FOV,
        "color": (68, 84, 74),
        "proj_speed_mult": 1.35,
        "max_range": 24.0,
        "ammo_max": 42,
        "ammo_pickup": 8,
    },
    "smg": {
        "label": "Submachine Gun",
        "cooldown_ms": 80,
        "damage": 0.65,
        "pellets": 1,
        "spread_deg": 4.0,
        "auto": True,
        "crosshair": 12,
        "scope": False,
        "ads_fov_mult": 0.76,
        "color": (76, 78, 84),
        "proj_speed_mult": 0.95,
        "max_range": 11.0,
        "ammo_max": 320,
        "ammo_pickup": 95,
    },
}
ENEMY_COUNT = 3
ENEMY_SPEED = 1.45
ENEMY_SPEED_PER_LEVEL = 0.24
ENEMY_RADIUS = 0.30
ENEMY_COLLIDER_RADIUS = 0.16
ENEMY_DAMAGE = 15
ENEMY_HP = 6
ENEMY_HP_PER_LEVEL = 2
HUNTER_SPAWN_CHANCE = 0.22
HUNTER_SPEED_MULT = 1.3
HUNTER_RADIUS = 0.26
HUNTER_DAMAGE = 22
BRUTE_SPAWN_CHANCE = 0.14
BRUTE_SPEED_MULT = 0.78
BRUTE_RADIUS = 0.36
BRUTE_DAMAGE = 28
BRUTE_HP_MULT = 1.85
ENEMY_HIT_COOLDOWN_MS = 900
BOSS_LEVEL_INTERVAL = 3
BOSS_BASE_HP = 520
BOSS_HP_PER_LEVEL = 95
BOSS_SPEED_MULT = 0.82
BOSS_RADIUS = 0.46
BOSS_PROJECTILE_SPEED = 8.5
BOSS_PROJECTILE_RADIUS = 0.09
BOSS_PROJECTILE_DAMAGE = 14
BOSS_SHOT_COOLDOWN_MS = 1200
BOSS_SHOT_RANGE = 16.0
SLOW_PICKUP_COUNT = 5
SLOW_DURATION_MS = 5000
SLOW_FACTOR = 0.55
HEAL_PICKUP_COUNT = 10
HEAL_AMOUNT = 22
TELEPORT_PICKUP_COUNT = 2
TELEPORT_MAX_CHARGES = 3
AMMO_CRATE_COUNT = 8
BARREL_COUNT = 14
BARREL_EXPLOSION_RADIUS = 10.5
BARREL_EXPLOSION_DAMAGE = 40
BARREL_SOLID_RADIUS = 0.34
BOMB_PEDESTAL_COUNT = 6
PEDESTAL_SOLID_RADIUS = 0.28
THROW_BOMB_FUSE_MS = 1600
THROW_BOMB_SPEED = 7.8
THROW_BOMB_RADIUS = 0.12
THROW_BOMB_BLAST_RADIUS = 2.8
THROW_BOMB_DAMAGE = 62
TURRET_COUNT = 4
TURRET_HP_BASE = 20
TURRET_HP_PER_LEVEL = 3
TURRET_RADIUS = 0.34
TURRET_SHOT_COOLDOWN_MS = 1200
TURRET_PROJECTILE_SPEED = 9.4
TURRET_PROJECTILE_RADIUS = 0.08
TURRET_PROJECTILE_DAMAGE = 16
TURRET_SHOT_RANGE = 9.5
EXIT_RADIUS = 0.32
CHECKPOINT_COUNT = 4
MULTI_EXIT_LEVEL = -1
STAIR_EXIT_COUNT = 3
ENEMY_RESPAWN_MS = 2600
MINIMAP_SIZE = 190
MINIMAP_MARGIN = 14

MAP_BASE_COLS = 51
MAP_BASE_ROWS = 37
MAP_GROWTH_COLS_PER_LEVEL = 3
MAP_GROWTH_ROWS_PER_LEVEL = 3
MAP_MAX_COLS = 95
MAP_MAX_ROWS = 71
DARKNESS_ALPHA = 34
SCANLINE_ALPHA = 8
MAZE_LIGHT_SPACING = 9
MAZE_LIGHT_RADIUS = 5.2
MAZE_LIGHT_BOOST = 58
MUSIC_FILE = "lofi_80s_loop.wav"
MUSIC_VOLUME = 0.34
WARNING_FILE = "enemy_warning.wav"
WARNING_VOLUME = 0.42
WARNING_DISTANCE = 3.4
WARNING_COOLDOWN_MS = 650
DAMAGE_FILE = "player_hit.wav"
DAMAGE_VOLUME = 0.5
DAMAGE_COOLDOWN_MS = 130

DIFFICULTY_PRESETS = {
    "easy": {
        "enemy_count_mult": 0.72,
        "enemy_hp_mult": 0.78,
        "enemy_speed_mult": 0.84,
        "enemy_damage_mult": 0.74,
        "turret_count_mult": 0.66,
        "turret_hp_mult": 0.75,
        "turret_range_mult": 0.82,
        "turret_damage_mult": 0.75,
        "boss_hp_mult": 0.82,
        "enemy_respawn_mult": 1.3,
    },
    "medium": {
        "enemy_count_mult": 1.0,
        "enemy_hp_mult": 1.0,
        "enemy_speed_mult": 1.0,
        "enemy_damage_mult": 1.0,
        "turret_count_mult": 1.0,
        "turret_hp_mult": 1.0,
        "turret_range_mult": 1.0,
        "turret_damage_mult": 1.0,
        "boss_hp_mult": 1.0,
        "enemy_respawn_mult": 1.0,
    },
    "hard": {
        "enemy_count_mult": 1.4,
        "enemy_hp_mult": 1.34,
        "enemy_speed_mult": 1.22,
        "enemy_damage_mult": 1.28,
        "turret_count_mult": 1.35,
        "turret_hp_mult": 1.35,
        "turret_range_mult": 1.2,
        "turret_damage_mult": 1.3,
        "boss_hp_mult": 1.45,
        "enemy_respawn_mult": 0.78,
    },
}


def _run_wall_gap_test_profile(overdraw_x: int, overdraw_y: int, bridge_w: int, col_w: int) -> bool:
    # Draw synthetic jagged wall slices and detect crack pixels between adjacent slices.
    w, h = 360, 220
    bg = (0, 0, 0)
    wall = (180, 180, 180)
    surf = pygame.Surface((w, h))
    surf.fill(bg)
    prev_top = None
    prev_bottom = None
    for i in range(w // col_w):
        x = i * col_w
        wave = math.sin(i * 0.41) * 24 + math.cos(i * 0.83) * 18
        wall_h = max(18, int(78 + wave))
        y = h // 2 - wall_h // 2 + int(math.sin(i * 0.14) * 9)
        pygame.draw.rect(
            surf,
            wall,
            pygame.Rect(x - overdraw_x, y - overdraw_y, col_w + overdraw_x * 2 + 1, wall_h + overdraw_y * 2),
        )
        if prev_top is not None:
            bridge_top = min(prev_top, y) - 1
            bridge_bottom = max(prev_bottom, y + wall_h) + 1
            pygame.draw.line(surf, wall, (x, bridge_top), (x, bridge_bottom), bridge_w)
            bridge_poly = [
                (x - 1, prev_top - overdraw_y),
                (x + overdraw_x, y - overdraw_y),
                (x + overdraw_x, y + wall_h + overdraw_y),
                (x - 1, prev_bottom + overdraw_y),
            ]
            pygame.draw.polygon(surf, wall, bridge_poly)
        prev_top = y
        prev_bottom = y + wall_h

    # Crack = empty pixel at slice boundary where both immediate neighbors are wall.
    y_min = h // 5
    y_max = (h * 4) // 5
    for x in range(col_w, w - col_w, col_w):
        for y in range(y_min, y_max):
            if surf.get_at((x, y))[:3] != bg:
                continue
            if surf.get_at((x - 1, y))[:3] == wall and surf.get_at((x + 1, y))[:3] == wall:
                return False
    return True


def choose_wall_gap_profile() -> tuple[int, int, int, int, bool]:
    # (overdraw_x, overdraw_y, bridge_w, ray_divisor)
    profiles = [
        (1, 1, 1, 220),
        (1, 1, 2, 260),
        (2, 1, 2, 320),
        (2, 2, 3, 420),
    ]
    for overdraw_x, overdraw_y, bridge_w, ray_divisor in profiles:
        test_col_w = max(1, 360 // ray_divisor)
        if _run_wall_gap_test_profile(overdraw_x, overdraw_y, bridge_w, max(1, test_col_w)):
            return overdraw_x, overdraw_y, bridge_w, ray_divisor, True
    overdraw_x, overdraw_y, bridge_w, ray_divisor = profiles[-1]
    # After all retries fail, force the safest profile for runtime rendering.
    return overdraw_x, overdraw_y, bridge_w, ray_divisor, True


def random_odd(min_size: int, max_size: int) -> int:
    value = random.randint(min_size, max_size)
    if value % 2 == 0:
        value = value + 1 if value < max_size else value - 1
    return value


def generate_lofi_music(path: Path) -> None:
    if path.exists():
        return
    sample_rate = 22050
    beat_sec = 0.26
    total_steps = 128
    total_samples = int(sample_rate * beat_sec * total_steps)
    chords = [
        (110.0, 138.59, 164.81),  # A2/C#3/E3
        (98.0, 123.47, 146.83),   # G2/B2/D3
        (82.41, 103.83, 123.47),  # E2/G#2/B2
        (92.5, 116.54, 138.59),   # F#2/A#2/C#3
    ]

    def sq(freq: float, t: float) -> float:
        return 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0

    pcm = bytearray()
    for i in range(total_samples):
        t = i / sample_rate
        step = int(t / beat_sec)
        chord = chords[(step // 8) % len(chords)]
        bass_f = chord[0] / 2.0
        lead_f = chord[(step // 2) % 3] * (2.0 if (step % 8) in (2, 6) else 1.0)

        # Soft detuned pads + lead.
        pad = (
            0.20 * sq(chord[0], t)
            + 0.16 * sq(chord[1] * 0.997, t)
            + 0.14 * sq(chord[2] * 1.003, t)
        )
        lead = 0.12 * sq(lead_f, t) * (0.6 + 0.4 * math.sin(2 * math.pi * 0.2 * t))
        bass = 0.25 * math.sin(2 * math.pi * bass_f * t)

        # Lo-fi drum accents.
        step_pos = (t / beat_sec) % 1.0
        kick_env = max(0.0, 1.0 - step_pos * 7.0) if step % 4 == 0 else 0.0
        kick = 0.42 * math.sin(2 * math.pi * (54 + 45 * kick_env) * t) * kick_env
        snare_hit = (step % 8) in (4, 6)
        snare_env = max(0.0, 1.0 - step_pos * 16.0) if snare_hit else 0.0
        snare_noise = (math.sin(2 * math.pi * 1600 * t) + math.sin(2 * math.pi * 2300 * t)) * 0.5
        snare = 0.13 * snare_noise * snare_env

        wobble = 0.06 * math.sin(2 * math.pi * 0.12 * t)
        sample = (pad + lead + bass + kick + snare) * (0.56 + wobble)
        sample = max(-1.0, min(1.0, sample))
        pcm.extend(struct.pack("<h", int(sample * 32767)))

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(bytes(pcm))


def generate_warning_sfx(path: Path) -> None:
    if path.exists():
        return
    sample_rate = 22050
    duration = 0.18
    total_samples = int(sample_rate * duration)
    freq = 920.0
    pcm = bytearray()
    for i in range(total_samples):
        t = i / sample_rate
        env = max(0.0, 1.0 - t / duration)
        tone = 0.62 * math.sin(2 * math.pi * freq * t) + 0.24 * math.sin(2 * math.pi * (freq * 1.98) * t)
        sample = max(-1.0, min(1.0, tone * env))
        pcm.extend(struct.pack("<h", int(sample * 32767)))
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(bytes(pcm))


def generate_damage_sfx(path: Path) -> None:
    if path.exists():
        return
    sample_rate = 22050
    duration = 0.14
    total_samples = int(sample_rate * duration)
    pcm = bytearray()
    for i in range(total_samples):
        t = i / sample_rate
        env = max(0.0, 1.0 - t / duration)
        thud = math.sin(2 * math.pi * (120 + 30 * env) * t)
        rasp = math.sin(2 * math.pi * 980 * t) * 0.35
        sample = max(-1.0, min(1.0, (0.68 * thud + 0.22 * rasp) * env))
        pcm.extend(struct.pack("<h", int(sample * 32767)))
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(bytes(pcm))


def generate_maze(cols: int, rows: int) -> list[str]:
    grid = [["#" for _ in range(cols)] for _ in range(rows)]
    stack = [(1, 1, 0, 0)]
    grid[1][1] = "."

    while stack:
        cx, cy, last_dx, last_dy = stack[-1]
        neighbors = []
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            nx, ny = cx + dx, cy + dy
            if 1 <= nx < cols - 1 and 1 <= ny < rows - 1 and grid[ny][nx] == "#":
                neighbors.append((nx, ny, dx, dy))
        if not neighbors:
            stack.pop()
            continue
        # Bias toward continuing the same direction to create longer hallways.
        weights = []
        for _, _, dx, dy in neighbors:
            weights.append(3.2 if (dx, dy) == (last_dx, last_dy) else 1.0)
        nx, ny, dx, dy = random.choices(neighbors, weights=weights, k=1)[0]
        grid[cy + dy // 2][cx + dx // 2] = "."
        grid[ny][nx] = "."
        stack.append((nx, ny, dx, dy))

    # Widen corridors from 1 tile to a roomier 2-tile feel.
    widened = [row[:] for row in grid]
    for y in range(2, rows - 2):
        for x in range(2, cols - 2):
            if grid[y][x] != ".":
                continue
            horizontal = grid[y][x - 1] == "." and grid[y][x + 1] == "." and grid[y - 1][x] == "#" and grid[y + 1][x] == "#"
            vertical = grid[y - 1][x] == "." and grid[y + 1][x] == "." and grid[y][x - 1] == "#" and grid[y][x + 1] == "#"
            if horizontal:
                if random.random() < 0.35:
                    widened[y - 1][x] = "."
                if random.random() < 0.35:
                    widened[y + 1][x] = "."
            elif vertical:
                if random.random() < 0.35:
                    widened[y][x - 1] = "."
                if random.random() < 0.35:
                    widened[y][x + 1] = "."
    grid = widened

    # Open pockets/rooms.
    room_count = 6 + (cols * rows) // 1200
    for _ in range(room_count):
        rw = random.randint(3, 6)
        rh = random.randint(3, 6)
        rx = random.randint(2, cols - rw - 3)
        ry = random.randint(2, rows - rh - 3)
        for y in range(ry, ry + rh):
            for x in range(rx, rx + rw):
                grid[y][x] = "."

    # Ensure clear spawn pocket.
    for y in range(1, 4):
        for x in range(1, 4):
            grid[y][x] = "."

    return ["".join(r) for r in grid]


def is_wall(grid: list[str], x: float, y: float) -> bool:
    tx = int(x)
    ty = int(y)
    if ty < 0 or ty >= len(grid) or tx < 0 or tx >= len(grid[0]):
        return True
    return grid[ty][tx] == "#"


def collides(grid: list[str], x: float, y: float, radius: float) -> bool:
    checks = [
        (x - radius, y - radius),
        (x + radius, y - radius),
        (x - radius, y + radius),
        (x + radius, y + radius),
    ]
    return any(is_wall(grid, cx, cy) for cx, cy in checks)


def cast_ray_hit(grid: list[str], px: float, py: float, angle: float) -> tuple[float, float, float]:
    step_size = 0.03
    dx = math.cos(angle) * step_size
    dy = math.sin(angle) * step_size
    rx, ry = px, py
    for i in range(int(MAX_VIEW_DIST / step_size)):
        rx += dx
        ry += dy
        if is_wall(grid, rx, ry):
            return i * step_size, rx, ry
    return MAX_VIEW_DIST, px + math.cos(angle) * MAX_VIEW_DIST, py + math.sin(angle) * MAX_VIEW_DIST


def cast_ray(grid: list[str], px: float, py: float, angle: float) -> float:
    return cast_ray_hit(grid, px, py, angle)[0]


def cast_ray_blockers(
    grid: list[str],
    px: float,
    py: float,
    angle: float,
    barrels: list[dict],
    bomb_pedestals: list[dict],
) -> float:
    step_size = 0.05
    dx = math.cos(angle) * step_size
    dy = math.sin(angle) * step_size
    rx, ry = px, py
    for i in range(int(MAX_VIEW_DIST / step_size)):
        rx += dx
        ry += dy
        if is_wall(grid, rx, ry) or collides_with_props(rx, ry, 0.02, barrels, bomb_pedestals):
            return i * step_size
    return MAX_VIEW_DIST


def marker_key(x: float, y: float) -> tuple[int, int]:
    return int(round(x * 2.0)), int(round(y * 2.0))


def can_encounter_point(
    grid: list[str],
    px: float,
    py: float,
    angle: float,
    view_fov: float,
    tx: float,
    ty: float,
    barrels: list[dict],
    bomb_pedestals: list[dict],
) -> bool:
    vx, vy = tx - px, ty - py
    dist = math.hypot(vx, vy)
    if dist < 0.1 or dist > MAX_VIEW_DIST:
        return False
    ang = math.atan2(vy, vx)
    da = (ang - angle + math.pi) % (2 * math.pi) - math.pi
    if abs(da) > view_fov * 0.6:
        return False
    return cast_ray_blockers(grid, px, py, ang, barrels, bomb_pedestals) + 0.05 >= dist


def _wall_height_for_dist(dist: float, screen_h: int) -> int:
    corrected = max(0.0001, dist)
    return min(screen_h, int((screen_h * WALL_HEIGHT_SCALE) / corrected))


def pitch_warp_test(scale: float, screen_h: int = 720) -> bool:
    # "Warp" guard: wall height should not change with pitch and horizon shift should remain bounded.
    dists = [0.8, 1.2, 1.8, 2.8, 4.0, 6.0, 9.0, 13.0, 18.0]
    reference = [_wall_height_for_dist(d, screen_h) for d in dists]
    for p in (-MAX_PITCH, 0.0, MAX_PITCH):
        horizon = screen_h // 2 + int(p * screen_h * scale)
        if horizon < int(screen_h * 0.18) or horizon > int(screen_h * 0.82):
            return False
        current = [_wall_height_for_dist(d, screen_h) for d in dists]
        if any(abs(a - b) > 1 for a, b in zip(reference, current)):
            return False
    return True


def choose_pitch_view_scale() -> float:
    for scale in PITCH_VIEW_SCALE_CANDIDATES:
        if pitch_warp_test(scale):
            return scale
    return PITCH_VIEW_SCALE_CANDIDATES[-1]


def run_pitch_warp_test() -> tuple[bool, float]:
    scale = choose_pitch_view_scale()
    return pitch_warp_test(scale), scale


def find_path(grid: list[str], start: tuple[int, int], target: tuple[int, int]) -> list[tuple[int, int]]:
    if start == target:
        return []
    q = deque([start])
    parent = {start: None}
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if (nx, ny) in parent:
                continue
            if ny < 0 or ny >= len(grid) or nx < 0 or nx >= len(grid[0]) or grid[ny][nx] == "#":
                continue
            parent[(nx, ny)] = (x, y)
            if (nx, ny) == target:
                q.clear()
                break
            q.append((nx, ny))
    if target not in parent:
        return []
    out = []
    cur = target
    while cur != start:
        out.append(cur)
        cur = parent[cur]
    out.reverse()
    return out


def nearest_open_tile(grid: list[str], cell: tuple[int, int]) -> tuple[int, int]:
    x, y = cell
    x = max(0, min(len(grid[0]) - 1, x))
    y = max(0, min(len(grid) - 1, y))
    if grid[y][x] != "#":
        return x, y
    q = deque([(x, y)])
    seen = {(x, y)}
    while q:
        cx, cy = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dx, cy + dy
            if ny < 0 or ny >= len(grid) or nx < 0 or nx >= len(grid[0]):
                continue
            if (nx, ny) in seen:
                continue
            if grid[ny][nx] != "#":
                return nx, ny
            seen.add((nx, ny))
            q.append((nx, ny))
    return 1, 1


def enemy_profile(kind: str) -> dict:
    if kind == "hunter":
        return {"speed_mult": HUNTER_SPEED_MULT, "radius": HUNTER_RADIUS, "damage": HUNTER_DAMAGE, "hp_mult": 0.78}
    if kind == "brute":
        return {"speed_mult": BRUTE_SPEED_MULT, "radius": BRUTE_RADIUS, "damage": BRUTE_DAMAGE, "hp_mult": BRUTE_HP_MULT}
    return {"speed_mult": 1.0, "radius": ENEMY_RADIUS, "damage": ENEMY_DAMAGE, "hp_mult": 1.0}


def roll_enemy_kind() -> str:
    r = random.random()
    if r < BRUTE_SPAWN_CHANCE:
        return "brute"
    if r < BRUTE_SPAWN_CHANCE + HUNTER_SPAWN_CHANCE:
        return "hunter"
    return "normal"


def enemy_hp_for_level(level: int, difficulty: dict) -> int:
    base = ENEMY_HP + max(0, level - 1) * ENEMY_HP_PER_LEVEL
    return max(1, int(base * difficulty["enemy_hp_mult"]))


def enemy_target_for_level(level: int, difficulty: dict) -> int:
    base = ENEMY_COUNT + max(0, level // 4)
    return max(1, int(base * difficulty["enemy_count_mult"]))


def spawn_enemies(grid: list[str], count: int, level: int, difficulty: dict) -> list[dict]:
    cells = []
    for y in range(1, len(grid) - 1):
        for x in range(1, len(grid[0]) - 1):
            if grid[y][x] == "." and abs(x - 1) + abs(y - 1) > 10:
                cells.append((x, y))
    random.shuffle(cells)
    enemies = []
    enemy_hp = enemy_hp_for_level(level, difficulty)
    for x, y in cells[:count]:
        kind = roll_enemy_kind()
        profile = enemy_profile(kind)
        enemies.append({
            "x": x + 0.5,
            "y": y + 0.5,
            "hp": max(1, int(enemy_hp * profile["hp_mult"])),
            "max_hp": max(1, int(enemy_hp * profile["hp_mult"])),
            "kind": kind,
            "speed_mult": profile["speed_mult"],
            "radius": profile["radius"],
            "damage": max(1, int(profile["damage"] * difficulty["enemy_damage_mult"])),
            "path": [],
            "next_path_ms": 0,
        })

    if level % BOSS_LEVEL_INTERVAL == 0 and cells:
        bx, by = max(cells, key=lambda p: abs(p[0] - 1) + abs(p[1] - 1))
        boss_hp = max(1, int((BOSS_BASE_HP + level * BOSS_HP_PER_LEVEL) * difficulty["boss_hp_mult"]))
        enemies.append({
            "x": bx + 0.5,
            "y": by + 0.5,
            "hp": boss_hp,
            "max_hp": boss_hp,
            "kind": "boss",
            "speed_mult": BOSS_SPEED_MULT,
            "radius": BOSS_RADIUS,
            "damage": max(1, int((ENEMY_DAMAGE + 6) * difficulty["enemy_damage_mult"])),
            "path": [],
            "next_path_ms": 0,
            "next_shot_ms": 0,
        })
    return enemies


def spawn_exit(grid: list[str]) -> tuple[float, float]:
    cells = []
    min_manhattan = int((len(grid) + len(grid[0])) * 0.58)
    min_euclid = min(len(grid), len(grid[0])) * 0.42
    for y in range(1, len(grid) - 1):
        for x in range(1, len(grid[0]) - 1):
            if grid[y][x] != ".":
                continue
            if abs(x - 1) + abs(y - 1) < min_manhattan:
                continue
            if math.hypot((x + 0.5) - 1.5, (y + 0.5) - 1.5) < min_euclid:
                continue
            cells.append((x, y))
    if not cells:
        # Fallback: still force "far from spawn" as much as possible.
        for y in range(1, len(grid) - 1):
            for x in range(1, len(grid[0]) - 1):
                if grid[y][x] == "." and abs(x - 1) + abs(y - 1) > (len(grid) + len(grid[0])) // 2:
                    cells.append((x, y))
    if not cells:
        cells = [(len(grid[0]) - 2, len(grid) - 2)]
    x, y = random.choice(cells)
    return x + 0.5, y + 0.5


def spawn_exits(grid: list[str], count: int) -> list[tuple[float, float]]:
    cells = []
    min_manhattan = int((len(grid) + len(grid[0])) * 0.58)
    min_euclid = min(len(grid), len(grid[0])) * 0.42
    for y in range(1, len(grid) - 1):
        for x in range(1, len(grid[0]) - 1):
            if grid[y][x] != ".":
                continue
            if abs(x - 1) + abs(y - 1) < min_manhattan:
                continue
            if math.hypot((x + 0.5) - 1.5, (y + 0.5) - 1.5) < min_euclid:
                continue
            cells.append((x, y))
    if not cells:
        for y in range(1, len(grid) - 1):
            for x in range(1, len(grid[0]) - 1):
                if grid[y][x] == "." and abs(x - 1) + abs(y - 1) > (len(grid) + len(grid[0])) // 2:
                    cells.append((x, y))
    random.shuffle(cells)
    chosen: list[tuple[int, int]] = []
    min_spacing = max(6, min(len(grid[0]), len(grid)) // 6)
    for x, y in cells:
        if all(abs(x - cx) + abs(y - cy) >= min_spacing for cx, cy in chosen):
            chosen.append((x, y))
            if len(chosen) >= count:
                break
    if not chosen:
        chosen = [(len(grid[0]) - 2, len(grid) - 2)]
    while len(chosen) < count:
        chosen.append(chosen[-1])
    return [(x + 0.5, y + 0.5) for x, y in chosen]


def spawn_items(grid: list[str], ex: float, ey: float, level: int) -> list[dict]:
    cells = []
    exi, eyi = int(ex), int(ey)
    for y in range(1, len(grid) - 1):
        for x in range(1, len(grid[0]) - 1):
            if grid[y][x] == "." and abs(x - 1) + abs(y - 1) > 4 and abs(x - exi) + abs(y - eyi) > 3:
                cells.append((x, y))
    random.shuffle(cells)
    items = []
    idx = 0
    slow_count = SLOW_PICKUP_COUNT
    heal_count = HEAL_PICKUP_COUNT
    teleport_count = TELEPORT_PICKUP_COUNT + 2
    for _ in range(min(slow_count, len(cells))):
        x, y = cells[idx]
        idx += 1
        items.append({"kind": "slow", "x": x + 0.5, "y": y + 0.5})
    for _ in range(min(heal_count, max(0, len(cells) - idx))):
        x, y = cells[idx]
        idx += 1
        items.append({"kind": "heal", "x": x + 0.5, "y": y + 0.5})
    for _ in range(min(teleport_count, max(0, len(cells) - idx))):
        x, y = cells[idx]
        idx += 1
        items.append({"kind": "teleport", "x": x + 0.5, "y": y + 0.5})
    return items


def spawn_barrels(grid: list[str], exits: list[tuple[float, float]], level: int) -> list[dict]:
    cells = []
    count = BARREL_COUNT + level // 2
    for y in range(1, len(grid) - 1):
        for x in range(1, len(grid[0]) - 1):
            if grid[y][x] != ".":
                continue
            if abs(x - 1) + abs(y - 1) < 8:
                continue
            if any(math.hypot((x + 0.5) - ex, (y + 0.5) - ey) < 3.8 for ex, ey in exits):
                continue
            cells.append((x, y))
    random.shuffle(cells)
    out = []
    for x, y in cells[:count]:
        out.append({"x": x + 0.5, "y": y + 0.5})
    return out


def spawn_ammo_crates(grid: list[str], exits: list[tuple[float, float]], level: int) -> list[dict]:
    cells = []
    count = AMMO_CRATE_COUNT + level // 3
    for y in range(1, len(grid) - 1):
        for x in range(1, len(grid[0]) - 1):
            if grid[y][x] != ".":
                continue
            if abs(x - 1) + abs(y - 1) < 6:
                continue
            if any(math.hypot((x + 0.5) - ex, (y + 0.5) - ey) < 3.0 for ex, ey in exits):
                continue
            cells.append((x, y))
    random.shuffle(cells)
    out = []
    for x, y in cells[:count]:
        out.append({"x": x + 0.5, "y": y + 0.5})
    return out


def spawn_bomb_pedestals(grid: list[str], exits: list[tuple[float, float]], level: int) -> list[dict]:
    cells = []
    count = BOMB_PEDESTAL_COUNT + level // 4
    for y in range(1, len(grid) - 1):
        for x in range(1, len(grid[0]) - 1):
            if grid[y][x] != ".":
                continue
            if abs(x - 1) + abs(y - 1) < 7:
                continue
            if any(math.hypot((x + 0.5) - ex, (y + 0.5) - ey) < 3.4 for ex, ey in exits):
                continue
            cells.append((x, y))
    random.shuffle(cells)
    out = []
    for x, y in cells[:count]:
        out.append({"x": x + 0.5, "y": y + 0.5})
    return out


def spawn_turrets(grid: list[str], exits: list[tuple[float, float]], level: int, difficulty: dict) -> list[dict]:
    cells = []
    count = max(1, int((TURRET_COUNT + level // 2) * difficulty["turret_count_mult"]))
    turret_hp = max(1, int((TURRET_HP_BASE + level * TURRET_HP_PER_LEVEL) * difficulty["turret_hp_mult"]))
    for y in range(1, len(grid) - 1):
        for x in range(1, len(grid[0]) - 1):
            if grid[y][x] != ".":
                continue
            if abs(x - 1) + abs(y - 1) < 10:
                continue
            if any(math.hypot((x + 0.5) - ex, (y + 0.5) - ey) < 4.2 for ex, ey in exits):
                continue
            cells.append((x, y))
    random.shuffle(cells)
    out = []
    for x, y in cells[:count]:
        out.append({
            "x": x + 0.5,
            "y": y + 0.5,
            "hp": turret_hp,
            "max_hp": turret_hp,
            "next_shot_ms": 0,
        })
    return out


def spawn_maze_lights(grid: list[str]) -> list[tuple[float, float]]:
    lights: list[tuple[float, float]] = []
    seen = set()
    for y in range(3, len(grid) - 3, MAZE_LIGHT_SPACING):
        for x in range(3, len(grid[0]) - 3, MAZE_LIGHT_SPACING):
            lx, ly = nearest_open_tile(grid, (x, y))
            if (lx, ly) in seen:
                continue
            seen.add((lx, ly))
            lights.append((lx + 0.5, ly + 0.5))
    return lights


def touching_wall(grid: list[str], x: float, y: float, radius: float) -> bool:
    checks = [
        (x + radius, y),
        (x - radius, y),
        (x, y + radius),
        (x, y - radius),
        (x + radius * 0.75, y + radius * 0.75),
        (x - radius * 0.75, y + radius * 0.75),
        (x + radius * 0.75, y - radius * 0.75),
        (x - radius * 0.75, y - radius * 0.75),
    ]
    return any(is_wall(grid, cx, cy) for cx, cy in checks)


def collides_with_props(
    x: float,
    y: float,
    radius: float,
    barrels: list[dict],
    bomb_pedestals: list[dict],
) -> bool:
    for b in barrels:
        if math.hypot(x - b["x"], y - b["y"]) < radius + BARREL_SOLID_RADIUS:
            return True
    for p in bomb_pedestals:
        if math.hypot(x - p["x"], y - p["y"]) < radius + PEDESTAL_SOLID_RADIUS:
            return True
    return False


def try_teleport_through_wall(grid: list[str], px: float, py: float, angle: float) -> tuple[float, float] | None:
    if not touching_wall(grid, px, py, PLAYER_RADIUS + 0.06):
        return None
    dx = math.cos(angle)
    dy = math.sin(angle)
    step = 0.05
    seen_wall = False
    for i in range(1, int(2.2 / step)):
        d = i * step
        tx = px + dx * d
        ty = py + dy * d
        if is_wall(grid, tx, ty):
            seen_wall = True
            continue
        if seen_wall and not collides(grid, tx, ty, PLAYER_RADIUS):
            return tx, ty
    return None


def bomb_front_point(
    grid: list[str],
    px: float,
    py: float,
    angle: float,
    barrels: list[dict],
    bomb_pedestals: list[dict],
) -> tuple[float, float]:
    dx = math.cos(angle)
    dy = math.sin(angle)
    step_d = 0.08
    max_dist = 1.7
    x, y = px, py
    steps = max(1, int(max_dist / step_d))
    for _ in range(steps):
        nx = x + dx * step_d
        ny = y + dy * step_d
        if collides(grid, nx, ny, 0.10) or collides_with_props(nx, ny, 0.10, barrels, bomb_pedestals):
            return x, y
        x, y = nx, ny
    return x, y


def spawn_normal_enemy(
    grid: list[str],
    px: float,
    py: float,
    exits: list[tuple[float, float]],
    enemies: list[dict],
    level: int,
    difficulty: dict,
) -> dict | None:
    cells = []
    for y in range(1, len(grid) - 1):
        for x in range(1, len(grid[0]) - 1):
            if grid[y][x] != ".":
                continue
            cx, cy = x + 0.5, y + 0.5
            if math.hypot(cx - px, cy - py) < 8.0:
                continue
            if any(math.hypot(cx - ex, cy - ey) < 4.0 for ex, ey in exits):
                continue
            if any(math.hypot(cx - e["x"], cy - e["y"]) < 1.0 for e in enemies):
                continue
            cells.append((x, y))
    if not cells:
        return None
    x, y = random.choice(cells)
    enemy_hp = enemy_hp_for_level(level, difficulty)
    kind = roll_enemy_kind()
    profile = enemy_profile(kind)
    return {
        "x": x + 0.5,
        "y": y + 0.5,
        "hp": max(1, int(enemy_hp * profile["hp_mult"])),
        "max_hp": max(1, int(enemy_hp * profile["hp_mult"])),
        "kind": kind,
        "speed_mult": profile["speed_mult"],
        "radius": profile["radius"],
        "damage": max(1, int(profile["damage"] * difficulty["enemy_damage_mult"])),
        "path": [],
        "next_path_ms": 0,
    }


def spawn_checkpoints(grid: list[str], ex: float, ey: float, level: int) -> list[dict]:
    count = min(7, CHECKPOINT_COUNT + level // 3)
    cells = []
    exi, eyi = int(ex), int(ey)
    for y in range(1, len(grid) - 1):
        for x in range(1, len(grid[0]) - 1):
            if grid[y][x] != ".":
                continue
            if abs(x - 1) + abs(y - 1) < 7:
                continue
            if abs(x - exi) + abs(y - eyi) < 5:
                continue
            cells.append((x, y))
    random.shuffle(cells)
    out = []
    for x, y in cells[:count]:
        out.append({"x": x + 0.5, "y": y + 0.5, "collected": False})
    return out


def load_level(
    level: int,
    difficulty: dict,
) -> tuple[
    list[str],
    float,
    float,
    list[dict],
    list[tuple[float, float]],
    list[dict],
    list[dict],
    bool,
    list[dict],
    list[dict],
    list[dict],
    list[dict],
    list[tuple[float, float]],
]:
    cols = min(MAP_MAX_COLS, MAP_BASE_COLS + (level - 1) * MAP_GROWTH_COLS_PER_LEVEL)
    rows = min(MAP_MAX_ROWS, MAP_BASE_ROWS + (level - 1) * MAP_GROWTH_ROWS_PER_LEVEL)
    cols = random_odd(max(21, cols - 2), min(MAP_MAX_COLS, cols + 2))
    rows = random_odd(max(17, rows - 2), min(MAP_MAX_ROWS, rows + 2))
    grid = generate_maze(cols, rows)
    is_stair_level = level == MULTI_EXIT_LEVEL
    if is_stair_level:
        exits = spawn_exits(grid, STAIR_EXIT_COUNT)
    else:
        exits = [spawn_exit(grid)]
    ex, ey = exits[0]
    items = spawn_items(grid, ex, ey, level)
    checkpoints = spawn_checkpoints(grid, ex, ey, level)
    barrels = spawn_barrels(grid, exits, level)
    ammo_crates = spawn_ammo_crates(grid, exits, level)
    bomb_pedestals = spawn_bomb_pedestals(grid, exits, level)
    turrets = spawn_turrets(grid, exits, level, difficulty)
    maze_lights = spawn_maze_lights(grid)
    return (
        grid,
        1.5,
        1.5,
        spawn_enemies(grid, enemy_target_for_level(level, difficulty), level, difficulty),
        exits,
        items,
        checkpoints,
        is_stair_level,
        barrels,
        ammo_crates,
        bomb_pedestals,
        turrets,
        maze_lights,
    )


def draw_enemy_3d(screen: pygame.Surface, sx: int, base_y: int, size: int, kind: str, now_ms: int) -> None:
    pulse = 0.5 + 0.5 * math.sin(now_ms * 0.01)
    body_h = size
    cy = base_y - body_h // 2
    half_w = max(6, size // 2)
    half_h = max(8, size // 2)
    diamond = [
        (sx, cy - half_h),
        (sx + half_w, cy),
        (sx, cy + half_h),
        (sx - half_w, cy),
    ]
    if kind == "boss":
        base = (80, 20, 20)
        side_c = (55, 10, 10)
        glow = (160, 40, 40)
        eye_c = (255, int(70 + 100 * pulse), int(70 + 100 * pulse))
    elif kind == "hunter":
        base = (72, 26, 118)
        side_c = (48, 18, 78)
        glow = (110, 52, 180)
        eye_c = (225, 165, 255)
    elif kind == "brute":
        base = (40, 88, 42)
        side_c = (26, 62, 28)
        glow = (92, 165, 96)
        eye_c = (190, 255, 190)
    else:
        base = (120, 36, 36)
        side_c = (78, 20, 20)
        glow = (185, 62, 62)
        eye_c = (255, int(60 + 90 * pulse), int(60 + 90 * pulse))
    pygame.draw.polygon(screen, side_c, diamond)
    inner = [
        (sx, cy - int(half_h * 0.72)),
        (sx + int(half_w * 0.72), cy),
        (sx, cy + int(half_h * 0.72)),
        (sx - int(half_w * 0.72), cy),
    ]
    pygame.draw.polygon(screen, base, inner)
    core = [
        (sx, cy - int(half_h * 0.4)),
        (sx + int(half_w * 0.4), cy),
        (sx, cy + int(half_h * 0.4)),
        (sx - int(half_w * 0.4), cy),
    ]
    pygame.draw.polygon(screen, glow, core)
    pygame.draw.polygon(screen, (16, 4, 4), diamond, 2)
    if kind == "boss":
        ring = [
            (sx, cy - int(half_h * 1.08)),
            (sx + int(half_w * 1.08), cy),
            (sx, cy + int(half_h * 1.08)),
            (sx - int(half_w * 1.08), cy),
        ]
        pygame.draw.polygon(screen, (150, 45, 45), ring, 2)
    eye_y = cy - max(2, size // 10)
    eye_dx = max(3, size // 6)
    eye_r = max(2, size // 12)
    pygame.draw.circle(screen, eye_c, (sx - eye_dx, eye_y), eye_r)
    pygame.draw.circle(screen, eye_c, (sx + eye_dx, eye_y), eye_r)
    mouth_y = eye_y + eye_r + 4
    pygame.draw.line(screen, (190, 35, 35), (sx - 6, mouth_y), (sx + 6, mouth_y), 2)


def draw_weapon_viewmodel(
    screen: pygame.Surface,
    weapon_key: str,
    now_ms: int,
    move_intensity: float,
    aiming: bool,
    switch_t: float,
    recoil_kick: float,
    sway_x: float,
    sway_y: float,
    muzzle_flash: float,
) -> None:
    w = WEAPONS[weapon_key]
    base_color = w["color"]
    dark = (max(0, base_color[0] - 28), max(0, base_color[1] - 28), max(0, base_color[2] - 28))
    light = (min(255, base_color[0] + 28), min(255, base_color[1] + 28), min(255, base_color[2] + 28))
    # Forward-facing orientation anchored at screen center-bottom.
    bx = WIDTH // 2 + int(math.sin(now_ms * 0.012) * 8 * move_intensity) + int(sway_x * 0.9)
    by = HEIGHT - 72 + int(abs(math.cos(now_ms * 0.018)) * 7 * move_intensity) + int(sway_y * 0.7) - int(recoil_kick * 24)
    if aiming:
        # Pull up and center when ADS (look down sights).
        by -= 118
    if switch_t < 1.0:
        # Slide down/up while switching.
        by += int(math.sin(switch_t * math.pi) * 110)

    shotgun_parts = None
    if weapon_key == "shotgun":
        body = pygame.Rect(bx - 66, by - 30, 132, 54)
        barrel = pygame.Rect(bx - 11, by - 190, 22, 170)
        stock = [(body.x + 8, body.bottom - 2), (body.x + 42, body.bottom - 2), (body.x + 18, body.bottom + 40), (body.x - 8, body.bottom + 40)]
        pump = pygame.Rect(bx - 21, by - 82, 42, 26)
        tube = pygame.Rect(bx - 7, barrel.y + 16, 14, barrel.height - 10)
        rib = pygame.Rect(bx - 3, barrel.y + 2, 6, max(8, barrel.height - 22))
        bead = (bx, barrel.y + 2)
        shotgun_parts = (stock, pump, tube, rib, bead)
    elif weapon_key == "sniper":
        body = pygame.Rect(bx - 54, by - 28, 108, 50)
        barrel = pygame.Rect(bx - 8, by - 220, 16, 200)
        scope = pygame.Rect(bx - 22, by - 128, 44, 28)
        pygame.draw.rect(screen, dark, scope, border_radius=5)
        pygame.draw.rect(screen, light, scope, 1, border_radius=5)
    elif weapon_key == "smg":
        body = pygame.Rect(bx - 58, by - 30, 116, 54)
        barrel = pygame.Rect(bx - 9, by - 168, 18, 148)
    else:
        body = pygame.Rect(bx - 62, by - 30, 124, 54)
        barrel = pygame.Rect(bx - 10, by - 180, 20, 160)

    pygame.draw.rect(screen, dark, body, border_radius=7)
    pygame.draw.rect(screen, base_color, pygame.Rect(body.x, body.y, body.width, body.height // 2), border_radius=7)
    pygame.draw.rect(screen, dark, barrel, border_radius=4)
    pygame.draw.rect(screen, light, pygame.Rect(barrel.x, barrel.y, barrel.width, max(2, barrel.height // 3)), border_radius=4)
    pygame.draw.rect(screen, (12, 12, 14), body, 2, border_radius=7)
    pygame.draw.rect(screen, (12, 12, 14), barrel, 2, border_radius=4)
    if shotgun_parts is not None:
        stock, pump, tube, rib, bead = shotgun_parts
        pygame.draw.polygon(screen, (98, 72, 50), stock)
        pygame.draw.polygon(screen, (46, 28, 18), stock, 2)
        pygame.draw.rect(screen, (82, 82, 88), tube, border_radius=3)
        pygame.draw.rect(screen, (142, 142, 154), pygame.Rect(tube.x, tube.y, tube.width, max(2, tube.height // 3)), border_radius=3)
        pygame.draw.rect(screen, (28, 28, 32), tube, 1, border_radius=3)
        pygame.draw.rect(screen, (92, 92, 98), rib, border_radius=2)
        pygame.draw.rect(screen, (22, 22, 26), rib, 1, border_radius=2)
        pygame.draw.rect(screen, (66, 56, 44), pump, border_radius=4)
        for i in range(4):
            gx = pump.x + 6 + i * max(6, pump.width // 5)
            pygame.draw.line(screen, (36, 30, 24), (gx, pump.y + 2), (gx, pump.bottom - 2), 1)
        pygame.draw.rect(screen, (24, 20, 16), pump, 1, border_radius=4)
        pygame.draw.circle(screen, (240, 220, 150), bead, 2)
    if muzzle_flash > 0.01:
        muzzle_x = barrel.centerx
        muzzle_y = barrel.y + 2
        r1 = max(7, int(26 * muzzle_flash))
        r2 = max(4, int(15 * muzzle_flash))
        pygame.draw.circle(screen, (255, 235, 120), (muzzle_x, muzzle_y), r1)
        pygame.draw.circle(screen, (255, 255, 210), (muzzle_x, muzzle_y), r2)
    # Low-detail hands for FPS hold pose.
    hand = (138, 108, 84)
    hand_dark = (94, 72, 56)
    back_hand = pygame.Rect(body.x - 10, body.y + body.height - 2, 34, 18)
    front_hand = pygame.Rect(body.right - 24, body.y + body.height - 2, 32, 16)
    pygame.draw.rect(screen, hand, back_hand, border_radius=6)
    pygame.draw.rect(screen, hand_dark, pygame.Rect(back_hand.x, back_hand.y + 8, back_hand.width, 8), border_radius=6)
    pygame.draw.rect(screen, hand, front_hand, border_radius=6)
    pygame.draw.rect(screen, hand_dark, pygame.Rect(front_hand.x, front_hand.y + 7, front_hand.width, 9), border_radius=6)


def main() -> None:
    global WIDTH, HEIGHT
    pygame.init()
    music_path = Path(__file__).resolve().parent / MUSIC_FILE
    warning_path = Path(__file__).resolve().parent / WARNING_FILE
    damage_path = Path(__file__).resolve().parent / DAMAGE_FILE
    warning_sound = None
    damage_sound = None
    try:
        generate_lofi_music(music_path)
        generate_warning_sfx(warning_path)
        generate_damage_sfx(damage_path)
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        pygame.mixer.music.load(str(music_path))
        pygame.mixer.music.set_volume(MUSIC_VOLUME)
        pygame.mixer.music.play(-1)
        warning_sound = pygame.mixer.Sound(str(warning_path))
        warning_sound.set_volume(WARNING_VOLUME)
        damage_sound = pygame.mixer.Sound(str(damage_path))
        damage_sound.set_volume(DAMAGE_VOLUME)
    except (pygame.error, OSError):
        pass
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Maze FPS")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 24)
    small_font = pygame.font.SysFont("arial", 18)
    static_labels = {
        "turret_world": small_font.render("Turret", True, (220, 220, 235)),
        "ammo_crate": small_font.render("Ammo Crate", True, (200, 245, 205)),
        "bomb_pedestal": small_font.render("Bomb Pedestal", True, (250, 220, 205)),
        "explosive_barrel": small_font.render("Explosive Barrel", True, (240, 180, 165)),
        "checkpoint": small_font.render("Checkpoint", True, (250, 238, 170)),
        "mini_t": small_font.render("T", True, (245, 245, 255)),
        "mini_exit": small_font.render("EXIT", True, (210, 245, 255)),
        "map_turret": small_font.render("TURRET", True, (245, 245, 255)),
        "map_exit": small_font.render("EXIT", True, (210, 245, 255)),
        "lock_exit": small_font.render("Exit locked: destroy all turrets", True, (255, 170, 120)),
        "boss_title": small_font.render("BOSS", True, (245, 220, 220)),
        "legend_slow": small_font.render("Slow pickup: enemies move slower", True, (220, 230, 235)),
        "legend_tp": small_font.render("Teleport pickup: press E at wall", True, (225, 215, 245)),
        "legend_bomb": small_font.render("Bomb pedestal: pick up, press F to throw", True, (245, 220, 205)),
        "legend_turret": small_font.render("Turret: destroy to unlock exit", True, (220, 220, 230)),
        "legend_cp": small_font.render("Checkpoint: reveals minimap", True, (235, 230, 210)),
        "pause_hint": small_font.render("Press M to resume", True, (220, 225, 235)),
    }
    pitch_view_scale = choose_pitch_view_scale()
    wall_overdraw_x, wall_overdraw_y, wall_bridge_w, wall_ray_divisor, wall_gap_test_ok = choose_wall_gap_profile()

    difficulty_key = "medium"
    difficulty = DIFFICULTY_PRESETS[difficulty_key]
    level = 1
    grid, px, py, enemies, exit_positions, items, checkpoints, is_stair_level, barrels, ammo_crates, bomb_pedestals, turrets, maze_lights = load_level(level, difficulty)
    angle = 0.0
    pitch = 0.0
    player_hp = PLAYER_MAX_HP
    sprint_meter = SPRINT_MAX
    last_enemy_hit_ms = -ENEMY_HIT_COOLDOWN_MS
    last_shot_ms = -SHOT_COOLDOWN_MS
    slow_until_ms = 0
    projectiles: list[dict] = []
    boss_projectiles: list[dict] = []
    turret_projectiles: list[dict] = []
    thrown_bombs: list[dict] = []
    explosions: list[dict] = []
    state = "start"
    shot_requested = False
    bomb_throw_requested = False
    teleport_requested = False
    teleport_charges = 0
    throw_bombs = 0
    selected_weapon = "shotgun"
    ammo_by_weapon = {k: int(v["ammo_max"] * 0.45) for k, v in WEAPONS.items()}
    ammo_by_weapon["shotgun"] = int(WEAPONS["shotgun"]["ammo_max"] * 0.55)
    switch_anim_start_ms = -WEAPON_SWITCH_ANIM_MS
    recoil_kick = 0.0
    look_sway_x = 0.0
    look_sway_y = 0.0
    muzzle_flash = 0.0
    pending_level = level
    normal_enemy_target = enemy_target_for_level(level, difficulty)
    next_enemy_respawn_ms = now_ms = pygame.time.get_ticks()
    next_warning_beep_ms = now_ms
    next_damage_sfx_ms = now_ms
    hp_regen_accum_s = 0.0
    seen_turrets: set[tuple[int, int]] = set()
    seen_exits: set[tuple[int, int]] = set()
    map_open = False

    running = True
    while running:
        dt = clock.tick(120) / 1000.0
        now_ms = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = max(800, event.w), max(500, event.h)
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            if event.type == pygame.KEYDOWN and state in ("start", "end"):
                if event.key == pygame.K_1:
                    selected_weapon = "shotgun"
                elif event.key == pygame.K_2:
                    selected_weapon = "sniper"
                elif event.key == pygame.K_3:
                    selected_weapon = "smg"
                elif event.key in (pygame.K_e, pygame.K_F1):
                    difficulty_key = "easy"
                    difficulty = DIFFICULTY_PRESETS[difficulty_key]
                elif event.key in (pygame.K_m, pygame.K_F2):
                    difficulty_key = "medium"
                    difficulty = DIFFICULTY_PRESETS[difficulty_key]
                elif event.key in (pygame.K_h, pygame.K_F3):
                    difficulty_key = "hard"
                    difficulty = DIFFICULTY_PRESETS[difficulty_key]
            if event.type == pygame.KEYDOWN and state == "playing":
                if event.key == pygame.K_1:
                    selected_weapon = "shotgun"
                    switch_anim_start_ms = now_ms
                elif event.key == pygame.K_2:
                    selected_weapon = "sniper"
                    switch_anim_start_ms = now_ms
                elif event.key == pygame.K_3:
                    selected_weapon = "smg"
                    switch_anim_start_ms = now_ms
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and state in ("start", "end"):
                level = 1
                grid, px, py, enemies, exit_positions, items, checkpoints, is_stair_level, barrels, ammo_crates, bomb_pedestals, turrets, maze_lights = load_level(level, difficulty)
                angle = 0.0
                pitch = 0.0
                player_hp = PLAYER_MAX_HP
                sprint_meter = SPRINT_MAX
                last_enemy_hit_ms = -ENEMY_HIT_COOLDOWN_MS
                last_shot_ms = -SHOT_COOLDOWN_MS
                slow_until_ms = 0
                projectiles = []
                boss_projectiles = []
                turret_projectiles = []
                thrown_bombs = []
                explosions = []
                teleport_charges = 0
                throw_bombs = 0
                ammo_by_weapon = {k: int(v["ammo_max"] * 0.45) for k, v in WEAPONS.items()}
                ammo_by_weapon["shotgun"] = int(WEAPONS["shotgun"]["ammo_max"] * 0.55)
                normal_enemy_target = enemy_target_for_level(level, difficulty)
                next_enemy_respawn_ms = now_ms + int(ENEMY_RESPAWN_MS * difficulty["enemy_respawn_mult"])
                hp_regen_accum_s = 0.0
                seen_turrets = set()
                seen_exits = set()
                state = "playing"
                map_open = False
                pygame.mouse.set_visible(False)
                pygame.event.set_grab(True)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and state == "level_complete":
                level = pending_level
                grid, px, py, enemies, exit_positions, items, checkpoints, is_stair_level, barrels, ammo_crates, bomb_pedestals, turrets, maze_lights = load_level(level, difficulty)
                projectiles = []
                boss_projectiles = []
                turret_projectiles = []
                thrown_bombs = []
                explosions = []
                slow_until_ms = 0
                player_hp = PLAYER_MAX_HP
                teleport_charges = 0
                throw_bombs = 0
                normal_enemy_target = enemy_target_for_level(level, difficulty)
                next_enemy_respawn_ms = now_ms + int(ENEMY_RESPAWN_MS * difficulty["enemy_respawn_mult"])
                hp_regen_accum_s = 0.0
                seen_turrets = set()
                seen_exits = set()
                state = "playing"
                map_open = False
                pygame.mouse.set_visible(False)
                pygame.event.set_grab(True)
            if event.type == pygame.KEYDOWN and state == "playing" and event.key == pygame.K_m:
                map_open = not map_open
                pygame.mouse.set_visible(map_open)
                pygame.event.set_grab(not map_open)
            if event.type == pygame.MOUSEMOTION and state == "playing" and not map_open:
                angle += event.rel[0] * MOUSE_SENSITIVITY
                pitch = max(-MAX_PITCH, min(MAX_PITCH, pitch - event.rel[1] * PITCH_SENSITIVITY))
                look_sway_x += max(-10.0, min(10.0, event.rel[0] * 0.22))
                look_sway_y += max(-8.0, min(8.0, event.rel[1] * 0.16))
            if event.type == pygame.MOUSEBUTTONDOWN and state == "playing" and not map_open and event.button == 1:
                shot_requested = True
            if event.type == pygame.MOUSEWHEEL and state == "playing" and not map_open:
                idx = WEAPON_ORDER.index(selected_weapon)
                selected_weapon = WEAPON_ORDER[(idx - event.y) % len(WEAPON_ORDER)]
                switch_anim_start_ms = now_ms
            if event.type == pygame.KEYDOWN and state == "playing" and not map_open and event.key == pygame.K_e:
                teleport_requested = True
            if event.type == pygame.KEYDOWN and state == "playing" and not map_open and event.key == pygame.K_f:
                bomb_throw_requested = True

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            running = False

        if state == "playing" and not map_open:
            weapon = WEAPONS[selected_weapon]
            mouse_buttons = pygame.mouse.get_pressed(3)
            aiming = mouse_buttons[2]
            view_fov = FOV * weapon["ads_fov_mult"] if aiming else FOV
            look_sway_x *= 0.86
            look_sway_y *= 0.86
            recoil_kick = max(0.0, recoil_kick - dt * 4.2)
            muzzle_flash = max(0.0, muzzle_flash - dt * 10.0)
            turn = 0.0
            if keys[pygame.K_LEFT] or keys[pygame.K_q]:
                turn -= TURN_SPEED * dt
            if keys[pygame.K_RIGHT]:
                turn += TURN_SPEED * dt
            angle += turn

            forward = 0.0
            strafe = 0.0
            sprinting = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
            can_sprint = sprinting and sprint_meter > 0.0 and (keys[pygame.K_w] or keys[pygame.K_s] or keys[pygame.K_a] or keys[pygame.K_d])
            speed_scale = SPRINT_MULTIPLIER if can_sprint else 1.0
            if aiming:
                speed_scale *= ADS_MOVE_MULT
            if keys[pygame.K_w]:
                forward += MOVE_SPEED * speed_scale * dt
            if keys[pygame.K_s]:
                forward -= MOVE_SPEED * speed_scale * dt
            if keys[pygame.K_a]:
                strafe -= MOVE_SPEED * speed_scale * dt
            if keys[pygame.K_d]:
                strafe += MOVE_SPEED * speed_scale * dt

            if can_sprint:
                sprint_meter = max(0.0, sprint_meter - SPRINT_DRAIN_PER_SEC * dt)
            else:
                sprint_meter = min(SPRINT_MAX, sprint_meter + SPRINT_REGEN_PER_SEC * dt)

            dx = math.cos(angle) * forward + math.cos(angle + math.pi / 2) * strafe
            dy = math.sin(angle) * forward + math.sin(angle + math.pi / 2) * strafe

            nx, ny = px + dx, py + dy
            if not collides(grid, nx, py, PLAYER_RADIUS) and not collides_with_props(nx, py, PLAYER_RADIUS, barrels, bomb_pedestals):
                px = nx
            if not collides(grid, px, ny, PLAYER_RADIUS) and not collides_with_props(px, ny, PLAYER_RADIUS, barrels, bomb_pedestals):
                py = ny

            wants_shot = (weapon["auto"] and mouse_buttons[0]) or ((not weapon["auto"]) and shot_requested)
            if wants_shot and ammo_by_weapon[selected_weapon] > 0 and now_ms - last_shot_ms >= weapon["cooldown_ms"]:
                last_shot_ms = now_ms
                ammo_by_weapon[selected_weapon] -= 1
                recoil_kick = min(1.35, recoil_kick + 0.28 + weapon["damage"] * 0.02)
                muzzle_flash = 1.0
                spread = math.radians(weapon["spread_deg"]) * (ADS_SPREAD_MULT if aiming else 1.0)
                for _ in range(weapon["pellets"]):
                    shot_ang = angle + random.uniform(-spread, spread)
                    projectiles.append({
                        "x": px,
                        "y": py,
                        "dx": math.cos(shot_ang),
                        "dy": math.sin(shot_ang),
                        "damage": weapon["damage"],
                        "speed": PROJECTILE_SPEED * weapon["proj_speed_mult"],
                        "dist": 0.0,
                        "max_dist": weapon["max_range"],
                        "born_ms": now_ms,
                    })
            shot_requested = False
            if bomb_throw_requested:
                if throw_bombs > 0:
                    bx, by = bomb_front_point(grid, px, py, angle, barrels, bomb_pedestals)
                    explosions.append({"x": bx, "y": by, "end_ms": now_ms + 260})
                    for enemy in enemies:
                        d = math.hypot(enemy["x"] - bx, enemy["y"] - by)
                        if d < THROW_BOMB_BLAST_RADIUS:
                            enemy["hp"] -= int(THROW_BOMB_DAMAGE * (1.0 - d / THROW_BOMB_BLAST_RADIUS))
                    for turret in turrets:
                        d = math.hypot(turret["x"] - bx, turret["y"] - by)
                        if d < THROW_BOMB_BLAST_RADIUS:
                            turret["hp"] -= int(THROW_BOMB_DAMAGE * (1.0 - d / THROW_BOMB_BLAST_RADIUS))
                    hit_barrels: list[int] = []
                    for bi, b in enumerate(barrels):
                        if math.hypot(b["x"] - bx, b["y"] - by) < THROW_BOMB_BLAST_RADIUS * 0.9:
                            hit_barrels.append(bi)
                    for bi in reversed(hit_barrels):
                        b = barrels.pop(bi)
                        explosions.append({"x": b["x"], "y": b["y"], "end_ms": now_ms + 220})
                    throw_bombs -= 1
                bomb_throw_requested = False
            if teleport_requested:
                if teleport_charges > 0:
                    tp = try_teleport_through_wall(grid, px, py, angle)
                    if tp is not None:
                        px, py = tp
                        teleport_charges -= 1
                teleport_requested = False

            kept_projectiles = []
            for p in projectiles:
                if now_ms - p["born_ms"] > PROJECTILE_LIFETIME_MS:
                    continue
                travel = p.get("speed", PROJECTILE_SPEED) * dt
                p["dist"] = p.get("dist", 0.0) + travel
                if p["dist"] > p.get("max_dist", 9999.0):
                    continue
                p["x"] += p["dx"] * travel
                p["y"] += p["dy"] * travel
                if collides(grid, p["x"], p["y"], PROJECTILE_RADIUS):
                    continue
                hit = False
                barrel_hit_idx = -1
                for bi, b in enumerate(barrels):
                    if math.hypot(b["x"] - p["x"], b["y"] - p["y"]) < 0.35:
                        barrel_hit_idx = bi
                        hit = True
                        break
                if barrel_hit_idx >= 0:
                    barrel = barrels.pop(barrel_hit_idx)
                    bx, by = barrel["x"], barrel["y"]
                    explosions.append({"x": bx, "y": by, "end_ms": now_ms + 220})
                    for enemy in enemies:
                        d = math.hypot(enemy["x"] - bx, enemy["y"] - by)
                        if d < BARREL_EXPLOSION_RADIUS:
                            enemy["hp"] -= int(BARREL_EXPLOSION_DAMAGE * (1.0 - d / BARREL_EXPLOSION_RADIUS))
                    for turret in turrets:
                        d = math.hypot(turret["x"] - bx, turret["y"] - by)
                        if d < BARREL_EXPLOSION_RADIUS:
                            turret["hp"] -= int(BARREL_EXPLOSION_DAMAGE * (1.0 - d / BARREL_EXPLOSION_RADIUS))
                    pd = math.hypot(px - bx, py - by)
                    if pd < BARREL_EXPLOSION_RADIUS:
                        player_hp -= int(BARREL_EXPLOSION_DAMAGE * (1.0 - pd / BARREL_EXPLOSION_RADIUS))
                        if damage_sound is not None and now_ms >= next_damage_sfx_ms:
                            damage_sound.play()
                            next_damage_sfx_ms = now_ms + DAMAGE_COOLDOWN_MS
                    continue
                for enemy in enemies:
                    enemy_radius = enemy.get("radius", ENEMY_RADIUS)
                    if math.hypot(enemy["x"] - p["x"], enemy["y"] - p["y"]) < enemy_radius + PROJECTILE_RADIUS + 0.02:
                        enemy["hp"] -= p.get("damage", 1)
                        hit = True
                        break
                if not hit:
                    if collides_with_props(p["x"], p["y"], PROJECTILE_RADIUS, [], bomb_pedestals):
                        hit = True
                if not hit:
                    for turret in turrets:
                        if math.hypot(turret["x"] - p["x"], turret["y"] - p["y"]) < TURRET_RADIUS + PROJECTILE_RADIUS + 0.02:
                            turret["hp"] -= p.get("damage", 1)
                            hit = True
                            break
                if not hit:
                    kept_projectiles.append(p)
            projectiles = kept_projectiles

            enemies = [e for e in enemies if e["hp"] > 0]
            turrets = [t for t in turrets if t["hp"] > 0]
            if now_ms >= next_enemy_respawn_ms:
                non_boss_alive = sum(1 for e in enemies if e.get("kind") != "boss")
                if non_boss_alive < normal_enemy_target:
                    new_enemy = spawn_normal_enemy(grid, px, py, exit_positions, enemies, level, difficulty)
                    if new_enemy is not None:
                        enemies.append(new_enemy)
                next_enemy_respawn_ms = now_ms + int(ENEMY_RESPAWN_MS * difficulty["enemy_respawn_mult"])

            # Enemy movement + damage.
            enemy_speed = (ENEMY_SPEED + (level - 1) * ENEMY_SPEED_PER_LEVEL) * (
                SLOW_FACTOR if now_ms < slow_until_ms else 1.0
            )
            enemy_speed *= difficulty["enemy_speed_mult"]
            for enemy in enemies:
                this_speed = enemy_speed * enemy.get("speed_mult", 1.0)
                enemy_radius = enemy.get("radius", ENEMY_RADIUS)
                if now_ms >= enemy["next_path_ms"]:
                    start = nearest_open_tile(grid, (int(enemy["x"]), int(enemy["y"])))
                    target = nearest_open_tile(grid, (int(px), int(py)))
                    enemy["path"] = find_path(grid, start, target)
                    enemy["next_path_ms"] = now_ms + 120
                if enemy["path"]:
                    tx, ty = enemy["path"][0]
                    tx += 0.5
                    ty += 0.5
                    evx, evy = tx - enemy["x"], ty - enemy["y"]
                    d = math.hypot(evx, evy)
                    if d > 0.01:
                        step = min(this_speed * dt, d)
                        nx = enemy["x"] + evx / d * step
                        ny = enemy["y"] + evy / d * step
                        if not collides(grid, nx, ny, min(enemy_radius - 0.03, ENEMY_COLLIDER_RADIUS)) and not collides_with_props(nx, ny, min(enemy_radius - 0.03, ENEMY_COLLIDER_RADIUS), barrels, bomb_pedestals):
                            enemy["x"] = nx
                            enemy["y"] = ny
                    if d < 0.18:
                        enemy["path"].pop(0)
                else:
                    # If path is empty but player is visible, chase directly.
                    evx, evy = px - enemy["x"], py - enemy["y"]
                    d = math.hypot(evx, evy)
                    if d > 0.01:
                        ang = math.atan2(evy, evx)
                        if cast_ray_blockers(grid, enemy["x"], enemy["y"], ang, barrels, bomb_pedestals) + 0.05 >= d:
                            step = min(this_speed * dt, d)
                            nx = enemy["x"] + evx / d * step
                            ny = enemy["y"] + evy / d * step
                            if not collides(grid, nx, ny, min(enemy_radius - 0.03, ENEMY_COLLIDER_RADIUS)) and not collides_with_props(nx, ny, min(enemy_radius - 0.03, ENEMY_COLLIDER_RADIUS), barrels, bomb_pedestals):
                                enemy["x"] = nx
                                enemy["y"] = ny

                if math.hypot(enemy["x"] - px, enemy["y"] - py) < PLAYER_RADIUS + enemy_radius + 0.04:
                    if now_ms - last_enemy_hit_ms >= ENEMY_HIT_COOLDOWN_MS:
                        player_hp -= enemy.get("damage", ENEMY_DAMAGE)
                        if damage_sound is not None and now_ms >= next_damage_sfx_ms:
                            damage_sound.play()
                            next_damage_sfx_ms = now_ms + DAMAGE_COOLDOWN_MS
                        last_enemy_hit_ms = now_ms
                if enemy.get("kind") == "boss" and now_ms >= enemy.get("next_shot_ms", 0):
                    bvx, bvy = px - enemy["x"], py - enemy["y"]
                    bd = math.hypot(bvx, bvy)
                    if bd > 0.1 and bd <= BOSS_SHOT_RANGE:
                        bang = math.atan2(bvy, bvx)
                        if cast_ray_blockers(grid, enemy["x"], enemy["y"], bang, barrels, bomb_pedestals) + 0.05 >= bd:
                            boss_projectiles.append({
                                "x": enemy["x"],
                                "y": enemy["y"],
                                "dx": math.cos(bang),
                                "dy": math.sin(bang),
                                "born_ms": now_ms,
                            })
                    enemy["next_shot_ms"] = now_ms + BOSS_SHOT_COOLDOWN_MS + random.randint(0, 350)

            for turret in turrets:
                if now_ms < turret["next_shot_ms"]:
                    continue
                tvx, tvy = px - turret["x"], py - turret["y"]
                td = math.hypot(tvx, tvy)
                turret_shot_range = TURRET_SHOT_RANGE * difficulty["turret_range_mult"]
                if td > 0.15 and td <= turret_shot_range:
                    tang = math.atan2(tvy, tvx)
                    if cast_ray_blockers(grid, turret["x"], turret["y"], tang, barrels, bomb_pedestals) + 0.05 >= td:
                        turret_projectiles.append({
                            "x": turret["x"],
                            "y": turret["y"],
                            "dx": math.cos(tang),
                            "dy": math.sin(tang),
                            "born_ms": now_ms,
                        })
                turret["next_shot_ms"] = now_ms + TURRET_SHOT_COOLDOWN_MS + random.randint(0, 260)

            kept_boss_projectiles = []
            for bp in boss_projectiles:
                if now_ms - bp["born_ms"] > PROJECTILE_LIFETIME_MS:
                    continue
                step = BOSS_PROJECTILE_SPEED * dt
                bp["x"] += bp["dx"] * step
                bp["y"] += bp["dy"] * step
                if collides(grid, bp["x"], bp["y"], BOSS_PROJECTILE_RADIUS):
                    continue
                if collides_with_props(bp["x"], bp["y"], BOSS_PROJECTILE_RADIUS, barrels, bomb_pedestals):
                    continue
                if math.hypot(bp["x"] - px, bp["y"] - py) < PLAYER_RADIUS + BOSS_PROJECTILE_RADIUS:
                    player_hp -= max(1, int(BOSS_PROJECTILE_DAMAGE * difficulty["enemy_damage_mult"]))
                    if damage_sound is not None and now_ms >= next_damage_sfx_ms:
                        damage_sound.play()
                        next_damage_sfx_ms = now_ms + DAMAGE_COOLDOWN_MS
                    continue
                kept_boss_projectiles.append(bp)
            boss_projectiles = kept_boss_projectiles

            kept_turret_projectiles = []
            for tp in turret_projectiles:
                if now_ms - tp["born_ms"] > PROJECTILE_LIFETIME_MS:
                    continue
                step = TURRET_PROJECTILE_SPEED * dt
                tp["x"] += tp["dx"] * step
                tp["y"] += tp["dy"] * step
                if collides(grid, tp["x"], tp["y"], TURRET_PROJECTILE_RADIUS):
                    continue
                if collides_with_props(tp["x"], tp["y"], TURRET_PROJECTILE_RADIUS, barrels, bomb_pedestals):
                    continue
                if math.hypot(tp["x"] - px, tp["y"] - py) < PLAYER_RADIUS + TURRET_PROJECTILE_RADIUS:
                    player_hp -= max(1, int(TURRET_PROJECTILE_DAMAGE * difficulty["turret_damage_mult"]))
                    if damage_sound is not None and now_ms >= next_damage_sfx_ms:
                        damage_sound.play()
                        next_damage_sfx_ms = now_ms + DAMAGE_COOLDOWN_MS
                    continue
                kept_turret_projectiles.append(tp)
            turret_projectiles = kept_turret_projectiles

            thrown_bombs = []
            explosions = [ex for ex in explosions if now_ms < ex["end_ms"]]

            # Pickups
            kept_items = []
            for it in items:
                if math.hypot(it["x"] - px, it["y"] - py) < PLAYER_RADIUS + 0.2:
                    if it["kind"] == "heal":
                        player_hp = min(PLAYER_MAX_HP, player_hp + HEAL_AMOUNT)
                    elif it["kind"] == "slow":
                        slow_until_ms = max(slow_until_ms, now_ms + SLOW_DURATION_MS)
                    elif it["kind"] == "teleport":
                        teleport_charges = min(TELEPORT_MAX_CHARGES, teleport_charges + 1)
                else:
                    kept_items.append(it)
            items = kept_items

            kept_crates = []
            for crate in ammo_crates:
                if math.hypot(crate["x"] - px, crate["y"] - py) < PLAYER_RADIUS + 0.25:
                    for wkey, cfg in WEAPONS.items():
                        ammo_by_weapon[wkey] = min(cfg["ammo_max"], ammo_by_weapon[wkey] + cfg["ammo_pickup"])
                else:
                    kept_crates.append(crate)
            ammo_crates = kept_crates

            kept_pedestals = []
            for ped in bomb_pedestals:
                if math.hypot(ped["x"] - px, ped["y"] - py) < PLAYER_RADIUS + PEDESTAL_SOLID_RADIUS + 0.1:
                    throw_bombs += 1
                else:
                    kept_pedestals.append(ped)
            bomb_pedestals = kept_pedestals

            for cp in checkpoints:
                if not cp["collected"] and math.hypot(cp["x"] - px, cp["y"] - py) < PLAYER_RADIUS + 0.2:
                    cp["collected"] = True

            # Exit
            if not turrets and any(math.hypot(ex - px, ey - py) < PLAYER_RADIUS + EXIT_RADIUS for ex, ey in exit_positions):
                pending_level = level + 1
                state = "level_complete"
                pygame.mouse.set_visible(True)
                pygame.event.set_grab(False)

            if player_hp <= 0:
                state = "end"
                pygame.mouse.set_visible(True)
                pygame.event.set_grab(False)

            # Encounter-based map intel.
            for ex, ey in exit_positions:
                if can_encounter_point(grid, px, py, angle, view_fov, ex, ey, barrels, bomb_pedestals):
                    seen_exits.add(marker_key(ex, ey))

            if player_hp < PLAYER_MAX_HP:
                hp_regen_accum_s += dt
                while hp_regen_accum_s >= 1.0 and player_hp < PLAYER_MAX_HP:
                    player_hp += 1
                    hp_regen_accum_s -= 1.0
            else:
                hp_regen_accum_s = 0.0

            if warning_sound is not None and now_ms >= next_warning_beep_ms and enemies:
                nearest_enemy_dist = min(math.hypot(e["x"] - px, e["y"] - py) for e in enemies)
                if nearest_enemy_dist <= WARNING_DISTANCE:
                    warning_sound.play()
                    next_warning_beep_ms = now_ms + WARNING_COOLDOWN_MS

        # Render
        horizon_y = HEIGHT // 2 + (int(pitch * HEIGHT * pitch_view_scale) if state == "playing" else 0)
        screen.fill((5, 5, 7))
        pygame.draw.rect(screen, (58, 62, 74), pygame.Rect(0, 0, WIDTH, max(0, horizon_y)))
        pygame.draw.rect(screen, (36, 38, 42), pygame.Rect(0, horizon_y, WIDTH, max(0, HEIGHT - horizon_y)))

        if state == "playing":
            view_center_y = horizon_y
            col_w = max(1, WIDTH // wall_ray_divisor)
            rays = WIDTH // col_w
            prev_top = None
            prev_bottom = None
            prev_shade = 0
            for i in range(rays):
                ray_angle = angle - view_fov / 2 + (i / max(1, rays - 1)) * view_fov
                dist, hit_x, hit_y = cast_ray_hit(grid, px, py, ray_angle)
                corrected = max(0.0001, dist * math.cos(ray_angle - angle))
                wall_h = min(HEIGHT, int((HEIGHT * WALL_HEIGHT_SCALE) / corrected))
                shade = max(16, min(130, int(150 - corrected * 14)))
                dirt = ((int(hit_x * 5) * 17 + int(hit_y * 5) * 31) % 19) - 9
                shade = max(10, min(180, shade + dirt))
                color = (shade, shade, shade)
                x = i * col_w
                y = view_center_y - wall_h // 2
                # Slight overdraw removes tiny cracks between adjacent wall slices.
                pygame.draw.rect(
                    screen,
                    color,
                    pygame.Rect(
                        x - wall_overdraw_x,
                        y - wall_overdraw_y,
                        col_w + wall_overdraw_x * 2 + 1,
                        wall_h + wall_overdraw_y * 2,
                    ),
                )
                if prev_top is not None:
                    bridge_top = min(prev_top, y) - 1
                    bridge_bottom = max(prev_bottom, y + wall_h) + 1
                    bridge_shade = (shade + prev_shade) // 2
                    bridge_color = (bridge_shade, bridge_shade, bridge_shade)
                    pygame.draw.line(screen, bridge_color, (x, bridge_top), (x, bridge_bottom), wall_bridge_w)
                prev_top = y
                prev_bottom = y + wall_h
                prev_shade = shade

            # Ceiling-only illumination, no visible bulbs.
            ceiling_glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            for li, (lx, ly) in enumerate(maze_lights):
                if li % 2 == 1:
                    continue
                vx, vy = lx - px, ly - py
                dist = math.hypot(vx, vy)
                if dist < 0.2:
                    continue
                ang = math.atan2(vy, vx)
                da = (ang - angle + math.pi) % (2 * math.pi) - math.pi
                if abs(da) > view_fov * 0.6:
                    continue
                wall_dist = cast_ray_blockers(grid, px, py, ang, barrels, bomb_pedestals)
                if dist > wall_dist + 0.08:
                    continue
                sx = int((0.5 + da / view_fov) * WIDTH)
                glow_r = max(20, int(HEIGHT / max(0.6, dist) * 0.24))
                glow_y = max(8, min(max(8, horizon_y - 10), int(horizon_y - glow_r * 0.55)))
                alpha = max(18, min(72, int(95 - dist * 4.0)))
                pygame.draw.circle(ceiling_glow, (245, 238, 205, alpha), (sx, glow_y), glow_r)
            screen.blit(ceiling_glow, (0, 0))


            # Draw enemies as billboards (sorted far to near)
            enemy_views = []
            for enemy in enemies:
                vx, vy = enemy["x"] - px, enemy["y"] - py
                dist = math.hypot(vx, vy)
                if dist < 0.2:
                    continue
                ang = math.atan2(vy, vx)
                da = (ang - angle + math.pi) % (2 * math.pi) - math.pi
                if abs(da) > view_fov * 0.6:
                    continue
                wall_dist = cast_ray_blockers(grid, px, py, ang, barrels, bomb_pedestals)
                if dist > wall_dist + 0.08:
                    continue
                screen_x = int((0.5 + da / view_fov) * WIDTH)
                base = HEIGHT / max(0.2, dist) * 0.25
                size = max(10, int(base * (enemy.get("radius", ENEMY_RADIUS) / ENEMY_RADIUS)))
                enemy_views.append((dist, screen_x, size, enemy.get("kind", "normal")))
            enemy_views.sort(reverse=True)
            for dist, sx, size, kind in enemy_views:
                y = view_center_y + size // 3
                draw_enemy_3d(screen, sx, y, size, kind, now_ms)
                if kind == "boss":
                    crown_y = y - size - max(5, size // 8)
                    pygame.draw.rect(screen, (245, 210, 85), pygame.Rect(sx - size // 3, crown_y, (size * 2) // 3, 4))

            for turret in turrets:
                vx, vy = turret["x"] - px, turret["y"] - py
                dist = math.hypot(vx, vy)
                if dist < 0.2:
                    continue
                ang = math.atan2(vy, vx)
                da = (ang - angle + math.pi) % (2 * math.pi) - math.pi
                if abs(da) > view_fov * 0.6:
                    continue
                wall_dist = cast_ray_blockers(grid, px, py, ang, barrels, bomb_pedestals)
                if dist > wall_dist + 0.08:
                    continue
                sx = int((0.5 + da / view_fov) * WIDTH)
                size = max(10, int(HEIGHT / max(0.3, dist) * 0.16))
                base = pygame.Rect(sx - size // 3, view_center_y + size // 3, (size * 2) // 3, size)
                head = pygame.Rect(sx - size // 2, base.y - size // 3, size, size // 3)
                pygame.draw.rect(screen, (95, 95, 108), base, border_radius=4)
                pygame.draw.rect(screen, (145, 145, 160), head, border_radius=4)
                pygame.draw.rect(screen, (45, 45, 52), base, 2, border_radius=4)
                pygame.draw.rect(screen, (45, 45, 52), head, 2, border_radius=4)
                pygame.draw.circle(screen, (255, 70, 70), (sx, head.centery), max(3, size // 12))
                label = static_labels["turret_world"]
                screen.blit(label, (sx - label.get_width() // 2, head.y - label.get_height() - 4))

            # Pickups + exit sprites (also wall-occluded)
            for it in items:
                vx, vy = it["x"] - px, it["y"] - py
                dist = math.hypot(vx, vy)
                if dist < 0.2:
                    continue
                ang = math.atan2(vy, vx)
                da = (ang - angle + math.pi) % (2 * math.pi) - math.pi
                if abs(da) > view_fov * 0.6:
                    continue
                wall_dist = cast_ray_blockers(grid, px, py, ang, barrels, bomb_pedestals)
                if dist > wall_dist + 0.08:
                    continue
                sx = int((0.5 + da / view_fov) * WIDTH)
                size = max(6, int(HEIGHT / max(0.3, dist) * 0.09))
                if it["kind"] == "slow":
                    color = (110, 220, 255)
                elif it["kind"] == "heal":
                    color = (255, 120, 120)
                else:
                    color = (165, 110, 255)
                pygame.draw.circle(screen, color, (sx, view_center_y + size), size)

            for crate in ammo_crates:
                vx, vy = crate["x"] - px, crate["y"] - py
                dist = math.hypot(vx, vy)
                if dist < 0.2:
                    continue
                ang = math.atan2(vy, vx)
                da = (ang - angle + math.pi) % (2 * math.pi) - math.pi
                if abs(da) > view_fov * 0.6:
                    continue
                wall_dist = cast_ray_blockers(grid, px, py, ang, barrels, bomb_pedestals)
                if dist > wall_dist + 0.08:
                    continue
                sx = int((0.5 + da / view_fov) * WIDTH)
                size = max(8, int(HEIGHT / max(0.3, dist) * 0.11))
                rect = pygame.Rect(sx - size // 2, view_center_y + size // 2, size, size)
                pygame.draw.rect(screen, (85, 185, 95), rect)
                pygame.draw.rect(screen, (155, 245, 165), rect, 2)
                pygame.draw.line(screen, (190, 255, 195), (rect.centerx, rect.y + 2), (rect.centerx, rect.bottom - 2), 1)
                label = static_labels["ammo_crate"]
                screen.blit(label, (sx - label.get_width() // 2, rect.y - label.get_height() - 4))

            for ped in bomb_pedestals:
                vx, vy = ped["x"] - px, ped["y"] - py
                dist = math.hypot(vx, vy)
                if dist < 0.2:
                    continue
                ang = math.atan2(vy, vx)
                da = (ang - angle + math.pi) % (2 * math.pi) - math.pi
                if abs(da) > view_fov * 0.6:
                    continue
                wall_dist = cast_ray_blockers(grid, px, py, ang, barrels, bomb_pedestals)
                if dist > wall_dist + 0.08:
                    continue
                sx = int((0.5 + da / view_fov) * WIDTH)
                size = max(8, int(HEIGHT / max(0.3, dist) * 0.12))
                pedestal_h = max(8, int(size * 1.05))
                top_w = max(8, int(size * 0.78))
                col_w = max(6, int(size * 0.46))
                base_y = view_center_y + size // 2
                pedestal = [
                    (sx - top_w // 2, base_y - pedestal_h),
                    (sx + top_w // 2, base_y - pedestal_h),
                    (sx + col_w // 2, base_y),
                    (sx - col_w // 2, base_y),
                ]
                pygame.draw.polygon(screen, (128, 128, 134), pedestal)
                pygame.draw.polygon(screen, (186, 186, 194), pedestal, 2)
                plinth = pygame.Rect(sx - top_w // 2 - 2, base_y - pedestal_h - max(4, size // 6), top_w + 4, max(5, size // 5))
                pygame.draw.rect(screen, (156, 156, 164), plinth, border_radius=3)
                pygame.draw.rect(screen, (210, 210, 218), plinth, 1, border_radius=3)
                orb_r = max(4, size // 4)
                orb_cy = plinth.y - orb_r + 2
                pygame.draw.circle(screen, (250, 145, 90), (sx, orb_cy), orb_r)
                pygame.draw.circle(screen, (255, 195, 140), (sx, orb_cy), max(2, orb_r // 2))
                pygame.draw.circle(screen, (120, 60, 35), (sx, orb_cy), orb_r, 1)
                label = static_labels["bomb_pedestal"]
                screen.blit(label, (sx - label.get_width() // 2, plinth.y - label.get_height() - 10))

            for b in barrels:
                vx, vy = b["x"] - px, b["y"] - py
                dist = math.hypot(vx, vy)
                if dist < 0.2:
                    continue
                ang = math.atan2(vy, vx)
                da = (ang - angle + math.pi) % (2 * math.pi) - math.pi
                if abs(da) > view_fov * 0.6:
                    continue
                wall_dist = cast_ray_blockers(grid, px, py, ang, barrels, bomb_pedestals)
                if dist > wall_dist + 0.08:
                    continue
                sx = int((0.5 + da / view_fov) * WIDTH)
                size = max(8, int(HEIGHT / max(0.3, dist) * 0.13))
                barrel_h = max(10, int(size * 1.2))
                barrel_w = max(8, int(size * 0.8))
                body = pygame.Rect(sx - barrel_w // 2, view_center_y + size // 5, barrel_w, barrel_h)
                top_oval = pygame.Rect(body.x, body.y - max(2, barrel_w // 8), body.width, max(4, barrel_w // 3))
                bot_oval = pygame.Rect(body.x, body.bottom - max(4, barrel_w // 5), body.width, max(4, barrel_w // 3))
                pygame.draw.rect(screen, (142, 46, 30), body, border_radius=max(3, barrel_w // 5))
                pygame.draw.ellipse(screen, (188, 68, 45), top_oval)
                pygame.draw.ellipse(screen, (120, 36, 24), bot_oval)
                band_h = max(3, barrel_h // 7)
                band1 = pygame.Rect(body.x, body.y + barrel_h // 4, body.width, band_h)
                band2 = pygame.Rect(body.x, body.y + (barrel_h * 2) // 3, body.width, band_h)
                pygame.draw.rect(screen, (68, 68, 74), band1)
                pygame.draw.rect(screen, (68, 68, 74), band2)
                warn = pygame.Rect(sx - max(5, barrel_w // 4), body.y + barrel_h // 2 - max(4, band_h), max(10, barrel_w // 2), max(8, band_h * 2))
                pygame.draw.rect(screen, (235, 195, 60), warn, border_radius=2)
                pygame.draw.rect(screen, (30, 30, 30), warn, 1, border_radius=2)
                pygame.draw.line(screen, (30, 30, 30), (warn.x + 2, warn.y + warn.height - 2), (warn.right - 2, warn.y + 2), 2)
                pygame.draw.rect(screen, (46, 14, 8), body, 2, border_radius=max(3, barrel_w // 5))
                label = static_labels["explosive_barrel"]
                screen.blit(label, (sx - label.get_width() // 2, body.y - label.get_height() - 4))

            for ex in explosions:
                vx, vy = ex["x"] - px, ex["y"] - py
                dist = math.hypot(vx, vy)
                if dist < 0.1:
                    continue
                ang = math.atan2(vy, vx)
                da = (ang - angle + math.pi) % (2 * math.pi) - math.pi
                if abs(da) > view_fov * 0.6:
                    continue
                sx = int((0.5 + da / view_fov) * WIDTH)
                life = max(0.0, min(1.0, (ex["end_ms"] - now_ms) / 220.0))
                size = max(16, int(HEIGHT / max(0.35, dist) * 0.42 * life))
                cy = view_center_y + size // 4
                pygame.draw.circle(screen, (255, 120, 35), (sx, cy), size)
                pygame.draw.circle(screen, (255, 170, 70), (sx, cy), max(8, int(size * 0.72)))
                pygame.draw.circle(screen, (255, 230, 155), (sx, cy), max(4, int(size * 0.44)))

            # Checkpoints are visible in-world until collected.
            for cp in checkpoints:
                if cp["collected"]:
                    continue
                vx, vy = cp["x"] - px, cp["y"] - py
                dist = math.hypot(vx, vy)
                if dist < 0.2:
                    continue
                ang = math.atan2(vy, vx)
                da = (ang - angle + math.pi) % (2 * math.pi) - math.pi
                if abs(da) > view_fov * 0.6:
                    continue
                wall_dist = cast_ray_blockers(grid, px, py, ang, barrels, bomb_pedestals)
                if dist > wall_dist + 0.08:
                    continue
                sx = int((0.5 + da / view_fov) * WIDTH)
                size = max(8, int(HEIGHT / max(0.3, dist) * 0.11))
                diamond = [(sx, view_center_y - size), (sx + size // 2, view_center_y), (sx, view_center_y + size), (sx - size // 2, view_center_y)]
                pygame.draw.polygon(screen, (245, 220, 100), diamond)
                pygame.draw.polygon(screen, (255, 245, 180), diamond, 2)
                label = static_labels["checkpoint"]
                screen.blit(label, (sx - label.get_width() // 2, view_center_y - size - label.get_height() - 4))

            for ex, ey in exit_positions:
                exv, eyv = ex - px, ey - py
                exit_dist = math.hypot(exv, eyv)
                if exit_dist <= 0.2:
                    continue
                exit_ang = math.atan2(eyv, exv)
                da = (exit_ang - angle + math.pi) % (2 * math.pi) - math.pi
                if abs(da) > view_fov * 0.6 or exit_dist > cast_ray_blockers(grid, px, py, exit_ang, barrels, bomb_pedestals) + 0.08:
                    continue
                sx = int((0.5 + da / view_fov) * WIDTH)
                size = max(10, int(HEIGHT / max(0.3, exit_dist) * 0.13))
                if is_stair_level:
                    stair_w = max(8, size // 2)
                    stair_h = max(4, size // 5)
                    base_y = view_center_y + size // 2
                    for step_idx in range(3):
                        sw = max(6, stair_w - step_idx * (stair_w // 4))
                        rect = pygame.Rect(sx - sw // 2, base_y - step_idx * stair_h, sw, stair_h - 1)
                        pygame.draw.rect(screen, (90, 155, 215), rect)
                        pygame.draw.rect(screen, (155, 210, 255), rect, 1)
                else:
                    pygame.draw.rect(screen, (80, 170, 255), pygame.Rect(sx - size // 3, view_center_y, size // 2, size))
                exit_name = "Stairs Exit" if is_stair_level else "Exit"
                if turrets:
                    exit_name += " (Locked)"
                label = small_font.render(exit_name, True, (190, 225, 255))
                screen.blit(label, (sx - label.get_width() // 2, view_center_y - label.get_height() - 4))

            for p in projectiles:
                vx, vy = p["x"] - px, p["y"] - py
                dist = math.hypot(vx, vy)
                if dist < 0.05:
                    continue
                ang = math.atan2(vy, vx)
                da = (ang - angle + math.pi) % (2 * math.pi) - math.pi
                if abs(da) > view_fov * 0.6:
                    continue
                sx = int((0.5 + da / view_fov) * WIDTH)
                sz = max(2, int(HEIGHT / max(0.5, dist) * 0.04))
                pygame.draw.circle(screen, (255, 235, 150), (sx, view_center_y + sz), sz)
            for bp in boss_projectiles:
                vx, vy = bp["x"] - px, bp["y"] - py
                dist = math.hypot(vx, vy)
                if dist < 0.05:
                    continue
                ang = math.atan2(vy, vx)
                da = (ang - angle + math.pi) % (2 * math.pi) - math.pi
                if abs(da) > view_fov * 0.6:
                    continue
                wall_dist = cast_ray_blockers(grid, px, py, ang, barrels, bomb_pedestals)
                if dist > wall_dist + 0.08:
                    continue
                sx = int((0.5 + da / view_fov) * WIDTH)
                sz = max(3, int(HEIGHT / max(0.5, dist) * 0.06))
                pygame.draw.circle(screen, (255, 70, 70), (sx, view_center_y + sz), sz)
            for tp in turret_projectiles:
                vx, vy = tp["x"] - px, tp["y"] - py
                dist = math.hypot(vx, vy)
                if dist < 0.05:
                    continue
                ang = math.atan2(vy, vx)
                da = (ang - angle + math.pi) % (2 * math.pi) - math.pi
                if abs(da) > view_fov * 0.6:
                    continue
                wall_dist = cast_ray_blockers(grid, px, py, ang, barrels, bomb_pedestals)
                if dist > wall_dist + 0.08:
                    continue
                sx = int((0.5 + da / view_fov) * WIDTH)
                sz = max(3, int(HEIGHT / max(0.5, dist) * 0.055))
                pygame.draw.circle(screen, (255, 120, 60), (sx, view_center_y + sz), sz)

            # Crosshair + HUD
            cross = max(2, int(weapon["crosshair"] * (0.42 if aiming else 1.0)))
            pygame.draw.line(screen, (240, 240, 220), (WIDTH // 2 - cross, HEIGHT // 2), (WIDTH // 2 + cross, HEIGHT // 2), 2)
            pygame.draw.line(screen, (240, 240, 220), (WIDTH // 2, HEIGHT // 2 - cross), (WIDTH // 2, HEIGHT // 2 + cross), 2)
            if weapon["scope"] and aiming:
                scope_r = min(WIDTH, HEIGHT) // 3
                top_h = HEIGHT // 2 - scope_r
                bot_y = HEIGHT // 2 + scope_r
                left_w = WIDTH // 2 - scope_r
                right_x = WIDTH // 2 + scope_r
                pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(0, 0, WIDTH, max(0, top_h)))
                pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(0, bot_y, WIDTH, max(0, HEIGHT - bot_y)))
                pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(0, top_h, max(0, left_w), max(0, bot_y - top_h)))
                pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(right_x, top_h, max(0, WIDTH - right_x), max(0, bot_y - top_h)))
                pygame.draw.circle(screen, (30, 30, 30), (WIDTH // 2, HEIGHT // 2), scope_r, 2)
            move_intensity = min(1.0, (abs(forward) + abs(strafe)) / max(0.0001, MOVE_SPEED * dt * 2))
            switch_t = min(1.0, (now_ms - switch_anim_start_ms) / max(1, WEAPON_SWITCH_ANIM_MS))
            draw_weapon_viewmodel(
                screen,
                selected_weapon,
                now_ms,
                move_intensity,
                aiming,
                switch_t,
                recoil_kick,
                look_sway_x,
                look_sway_y,
                muzzle_flash,
            )

            hp_ratio = max(0.0, min(1.0, player_hp / PLAYER_MAX_HP))
            bar_w = min(360, WIDTH - 80)
            bar_x = (WIDTH - bar_w) // 2
            bar_y = HEIGHT - 28
            pygame.draw.rect(screen, (40, 20, 20), pygame.Rect(bar_x, bar_y, bar_w, 14))
            pygame.draw.rect(screen, (210, 70, 70), pygame.Rect(bar_x, bar_y, int(bar_w * hp_ratio), 14))
            pygame.draw.rect(screen, (240, 210, 210), pygame.Rect(bar_x, bar_y, bar_w, 14), 2)

            sprint_ratio = max(0.0, min(1.0, sprint_meter / SPRINT_MAX))
            sprint_y = bar_y - 18
            pygame.draw.rect(screen, (20, 35, 45), pygame.Rect(bar_x, sprint_y, bar_w, 10))
            pygame.draw.rect(screen, (90, 180, 230), pygame.Rect(bar_x, sprint_y, int(bar_w * sprint_ratio), 10))
            pygame.draw.rect(screen, (190, 230, 250), pygame.Rect(bar_x, sprint_y, bar_w, 10), 1)

            slow_txt = " SLOW" if now_ms < slow_until_ms else ""
            checkpoint_total = len(checkpoints)
            checkpoint_done = sum(1 for cp in checkpoints if cp["collected"])
            info = font.render(
                f"HP {player_hp}   Enemies {len(enemies)}   Turrets {len(turrets)}   Level {level}   Diff {difficulty_key.title()}   Weapon {weapon['label']}   Ammo {ammo_by_weapon[selected_weapon]}   Bombs {throw_bombs}   CP {checkpoint_done}/{checkpoint_total}   TP {teleport_charges}{slow_txt}",
                True,
                (240, 240, 235),
            )
            screen.blit(info, (20, 16))
            if turrets:
                lock_txt = static_labels["lock_exit"]
                screen.blit(lock_txt, (20, 40))
            bosses = [e for e in enemies if e.get("kind") == "boss"]
            if bosses:
                boss = bosses[0]
                boss_ratio = max(0.0, min(1.0, boss["hp"] / max(1, boss.get("max_hp", boss["hp"]))))
                b_w = min(620, WIDTH - 140)
                b_x = (WIDTH - b_w) // 2
                b_y = 12
                bar_h = 20
                pygame.draw.rect(screen, (35, 10, 10), pygame.Rect(b_x, b_y, b_w, bar_h), border_radius=4)
                pygame.draw.rect(screen, (220, 80, 80), pygame.Rect(b_x, b_y, int(b_w * boss_ratio), bar_h), border_radius=4)
                pygame.draw.rect(screen, (245, 220, 220), pygame.Rect(b_x, b_y, b_w, bar_h), 2, border_radius=4)
                boss_title = static_labels["boss_title"]
                boss_hp_text = small_font.render(f"{int(max(0, boss['hp']))} / {int(max(1, boss.get('max_hp', boss['hp'])))}", True, (255, 235, 235))
                screen.blit(boss_title, (b_x - boss_title.get_width() - 10, b_y + 1))
                screen.blit(boss_hp_text, (b_x + b_w + 10, b_y + 1))
            legend_y = 48
            pygame.draw.circle(screen, (110, 220, 255), (28, legend_y + 9), 6)
            screen.blit(static_labels["legend_slow"], (42, legend_y))
            pygame.draw.circle(screen, (255, 120, 120), (28, legend_y + 31), 6)
            screen.blit(small_font.render(f"Heal pickup: +{HEAL_AMOUNT} HP", True, (235, 220, 220)), (42, legend_y + 22))
            pygame.draw.circle(screen, (165, 110, 255), (28, legend_y + 53), 6)
            screen.blit(static_labels["legend_tp"], (42, legend_y + 44))
            pygame.draw.circle(screen, (245, 145, 95), (28, legend_y + 75), 6)
            screen.blit(static_labels["legend_bomb"], (42, legend_y + 66))
            pygame.draw.rect(screen, (145, 145, 160), pygame.Rect(22, legend_y + 96, 12, 12))
            screen.blit(static_labels["legend_turret"], (42, legend_y + 88))
            pygame.draw.rect(screen, (240, 215, 90), pygame.Rect(22, legend_y + 67, 12, 12))
            screen.blit(static_labels["legend_cp"], (42, legend_y + 110))
            pygame.draw.rect(screen, (80, 170, 255), pygame.Rect(22, legend_y + 130, 12, 12))
            exit_label = "Stairs down: enter to finish level" if is_stair_level else "Exit: reach to finish level"
            screen.blit(small_font.render(exit_label, True, (210, 225, 245)), (42, legend_y + 130))

            # Minimap
            mini = pygame.Rect(WIDTH - MINIMAP_SIZE - MINIMAP_MARGIN, MINIMAP_MARGIN, MINIMAP_SIZE, MINIMAP_SIZE)
            pygame.draw.rect(screen, (10, 10, 15), mini)
            pygame.draw.rect(screen, (190, 190, 210), mini, 2)
            sx = mini.width / len(grid[0])
            sy = mini.height / len(grid)
            checkpoint_done = sum(1 for cp in checkpoints if cp["collected"])
            reveal_ratio = min(1.0, checkpoint_done / 2.0)
            for y in range(len(grid)):
                for x in range(len(grid[0])):
                    should_reveal = reveal_ratio >= 1.0 or (((x * 73856093) ^ (y * 19349663)) & 1023) / 1023.0 <= reveal_ratio
                    if not should_reveal:
                        continue
                    wx = mini.x + int(x * sx)
                    wy = mini.y + int(y * sy)
                    cell_rect = pygame.Rect(wx, wy, max(1, int(sx)), max(1, int(sy)))
                    if grid[y][x] == "#":
                        pygame.draw.rect(screen, (110, 120, 150), cell_rect)
                        pygame.draw.rect(screen, (88, 96, 122), cell_rect, 1)
                    else:
                        pygame.draw.rect(screen, (30, 34, 38), cell_rect)
            for enemy in enemies:
                ex = mini.x + int(enemy["x"] * sx)
                ey = mini.y + int(enemy["y"] * sy)
                if enemy.get("kind") == "boss":
                    pygame.draw.rect(screen, (255, 175, 90), pygame.Rect(ex - 2, ey - 2, 5, 5))
                elif enemy.get("kind") == "hunter":
                    pygame.draw.rect(screen, (185, 120, 255), pygame.Rect(ex - 2, ey - 2, 4, 4))
                elif enemy.get("kind") == "brute":
                    pygame.draw.rect(screen, (100, 210, 105), pygame.Rect(ex - 2, ey - 2, 5, 5))
                else:
                    pygame.draw.rect(screen, (210, 80, 80), pygame.Rect(ex - 1, ey - 1, 3, 3))
            for turret in turrets:
                tx = mini.x + int(turret["x"] * sx)
                ty = mini.y + int(turret["y"] * sy)
                pulse = 1 if (now_ms // 220) % 2 == 0 else 0
                r = 4 + pulse
                pygame.draw.circle(screen, (150, 150, 170), (tx, ty), r)
                pygame.draw.circle(screen, (230, 230, 245), (tx, ty), r, 1)
                t_lab = static_labels["mini_t"]
                screen.blit(t_lab, (tx + 5, ty - 6))
            for ex, ey in exit_positions:
                ekey = marker_key(ex, ey)
                if ekey not in seen_exits:
                    continue
                mx = mini.x + int(ex * sx)
                my = mini.y + int(ey * sy)
                pulse = 1 if (now_ms // 180) % 2 == 0 else 0
                r = 5 + pulse
                pygame.draw.circle(screen, (95, 215, 255), (mx, my), r)
                pygame.draw.circle(screen, (225, 250, 255), (mx, my), r, 1)
                e_lab = static_labels["mini_exit"]
                screen.blit(e_lab, (mx + 6, my - 8))
            for it in items:
                ix = mini.x + int(it["x"] * sx)
                iy = mini.y + int(it["y"] * sy)
                if it["kind"] == "slow":
                    color = (110, 220, 255)
                elif it["kind"] == "heal":
                    color = (255, 120, 120)
                else:
                    color = (165, 110, 255)
                pygame.draw.rect(screen, color, pygame.Rect(ix - 1, iy - 1, 3, 3))
            for crate in ammo_crates:
                ax = mini.x + int(crate["x"] * sx)
                ay = mini.y + int(crate["y"] * sy)
                pygame.draw.rect(screen, (85, 185, 95), pygame.Rect(ax - 1, ay - 1, 3, 3))
            for b in barrels:
                bx = mini.x + int(b["x"] * sx)
                by = mini.y + int(b["y"] * sy)
                pygame.draw.rect(screen, (170, 70, 50), pygame.Rect(bx - 1, by - 1, 3, 3))
            for ped in bomb_pedestals:
                bx = mini.x + int(ped["x"] * sx)
                by = mini.y + int(ped["y"] * sy)
                pygame.draw.rect(screen, (245, 145, 95), pygame.Rect(bx - 1, by - 1, 3, 3))
            for cp in checkpoints:
                if cp["collected"]:
                    continue
                cx = mini.x + int(cp["x"] * sx)
                cy = mini.y + int(cp["y"] * sy)
                pygame.draw.rect(screen, (240, 215, 90), pygame.Rect(cx - 2, cy - 2, 5, 5))
            pxm = mini.x + int(px * sx)
            pym = mini.y + int(py * sy)
            # Facing direction + FOV on minimap.
            dir_len = 12
            tip = (pxm + int(math.cos(angle) * dir_len), pym + int(math.sin(angle) * dir_len))
            left = (
                pxm + int(math.cos(angle + 2.5) * 5),
                pym + int(math.sin(angle + 2.5) * 5),
            )
            right = (
                pxm + int(math.cos(angle - 2.5) * 5),
                pym + int(math.sin(angle - 2.5) * 5),
            )
            pygame.draw.polygon(screen, (120, 240, 140), [tip, left, right])
            fov_len = 16
            fov_l = (pxm + int(math.cos(angle - view_fov * 0.5) * fov_len), pym + int(math.sin(angle - view_fov * 0.5) * fov_len))
            fov_r = (pxm + int(math.cos(angle + view_fov * 0.5) * fov_len), pym + int(math.sin(angle + view_fov * 0.5) * fov_len))
            pygame.draw.line(screen, (90, 190, 120), (pxm, pym), fov_l, 1)
            pygame.draw.line(screen, (90, 190, 120), (pxm, pym), fov_r, 1)

            # Post-process pass: dark ambient tint + scanlines.
            dark = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            dark.fill((0, 0, 0, DARKNESS_ALPHA))
            screen.blit(dark, (0, 0))
            scan = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            for y in range(0, HEIGHT, 3):
                pygame.draw.line(scan, (0, 0, 0, SCANLINE_ALPHA), (0, y), (WIDTH, y))
            screen.blit(scan, (0, 0))

            if map_open:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 185))
                screen.blit(overlay, (0, 0))

                pad = 34
                map_rect = pygame.Rect(pad, pad, WIDTH - pad * 2, HEIGHT - pad * 2)
                pygame.draw.rect(screen, (8, 10, 14), map_rect, border_radius=10)
                pygame.draw.rect(screen, (200, 210, 225), map_rect, 2, border_radius=10)

                fsx = map_rect.width / len(grid[0])
                fsy = map_rect.height / len(grid)
                checkpoint_done = sum(1 for cp in checkpoints if cp["collected"])
                reveal_ratio = min(1.0, checkpoint_done / 2.0)
                for y in range(len(grid)):
                    for x in range(len(grid[0])):
                        should_reveal = reveal_ratio >= 1.0 or (((x * 73856093) ^ (y * 19349663)) & 1023) / 1023.0 <= reveal_ratio
                        if not should_reveal:
                            continue
                        wx = map_rect.x + int(x * fsx)
                        wy = map_rect.y + int(y * fsy)
                        cell_rect = pygame.Rect(wx, wy, max(1, int(fsx + 0.4)), max(1, int(fsy + 0.4)))
                        if grid[y][x] == "#":
                            pygame.draw.rect(screen, (108, 120, 154), cell_rect)
                        else:
                            pygame.draw.rect(screen, (24, 28, 34), cell_rect)

                for enemy in enemies:
                    ex = map_rect.x + int(enemy["x"] * fsx)
                    ey = map_rect.y + int(enemy["y"] * fsy)
                    if enemy.get("kind") == "boss":
                        pygame.draw.rect(screen, (255, 175, 90), pygame.Rect(ex - 4, ey - 4, 9, 9))
                    elif enemy.get("kind") == "hunter":
                        pygame.draw.rect(screen, (185, 120, 255), pygame.Rect(ex - 3, ey - 3, 7, 7))
                    elif enemy.get("kind") == "brute":
                        pygame.draw.rect(screen, (100, 210, 105), pygame.Rect(ex - 3, ey - 3, 8, 8))
                    else:
                        pygame.draw.rect(screen, (210, 80, 80), pygame.Rect(ex - 3, ey - 3, 6, 6))
                for turret in turrets:
                    tx = map_rect.x + int(turret["x"] * fsx)
                    ty = map_rect.y + int(turret["y"] * fsy)
                    pulse = 1 if (now_ms // 220) % 2 == 0 else 0
                    rr = 8 + pulse
                    pygame.draw.circle(screen, (150, 150, 170), (tx, ty), rr)
                    pygame.draw.circle(screen, (230, 230, 245), (tx, ty), rr, 2)
                    t_lab = static_labels["map_turret"]
                    screen.blit(t_lab, (tx + 10, ty - 9))
                for ex, ey in exit_positions:
                    ekey = marker_key(ex, ey)
                    if ekey not in seen_exits:
                        continue
                    mx = map_rect.x + int(ex * fsx)
                    my = map_rect.y + int(ey * fsy)
                    pulse = 1 if (now_ms // 180) % 2 == 0 else 0
                    rr = 9 + pulse
                    pygame.draw.circle(screen, (95, 215, 255), (mx, my), rr)
                    pygame.draw.circle(screen, (225, 250, 255), (mx, my), rr, 2)
                    e_lab = static_labels["map_exit"]
                    screen.blit(e_lab, (mx + 12, my - 9))
                for it in items:
                    ix = map_rect.x + int(it["x"] * fsx)
                    iy = map_rect.y + int(it["y"] * fsy)
                    if it["kind"] == "slow":
                        color = (110, 220, 255)
                    elif it["kind"] == "heal":
                        color = (255, 120, 120)
                    else:
                        color = (165, 110, 255)
                    pygame.draw.rect(screen, color, pygame.Rect(ix - 3, iy - 3, 6, 6))
                for crate in ammo_crates:
                    ax = map_rect.x + int(crate["x"] * fsx)
                    ay = map_rect.y + int(crate["y"] * fsy)
                    pygame.draw.rect(screen, (85, 185, 95), pygame.Rect(ax - 3, ay - 3, 6, 6))
                for b in barrels:
                    bx = map_rect.x + int(b["x"] * fsx)
                    by = map_rect.y + int(b["y"] * fsy)
                    pygame.draw.rect(screen, (170, 70, 50), pygame.Rect(bx - 3, by - 3, 6, 6))
                for ped in bomb_pedestals:
                    bx = map_rect.x + int(ped["x"] * fsx)
                    by = map_rect.y + int(ped["y"] * fsy)
                    pygame.draw.rect(screen, (245, 145, 95), pygame.Rect(bx - 3, by - 3, 6, 6))
                for cp in checkpoints:
                    if cp["collected"]:
                        continue
                    cx = map_rect.x + int(cp["x"] * fsx)
                    cy = map_rect.y + int(cp["y"] * fsy)
                    pygame.draw.rect(screen, (240, 215, 90), pygame.Rect(cx - 4, cy - 4, 8, 8))

                pxm = map_rect.x + int(px * fsx)
                pym = map_rect.y + int(py * fsy)
                tip = (pxm + int(math.cos(angle) * 15), pym + int(math.sin(angle) * 15))
                left = (pxm + int(math.cos(angle + 2.5) * 6), pym + int(math.sin(angle + 2.5) * 6))
                right = (pxm + int(math.cos(angle - 2.5) * 6), pym + int(math.sin(angle - 2.5) * 6))
                pygame.draw.polygon(screen, (120, 240, 140), [tip, left, right])
                fov_l = (pxm + int(math.cos(angle - view_fov * 0.5) * 20), pym + int(math.sin(angle - view_fov * 0.5) * 20))
                fov_r = (pxm + int(math.cos(angle + view_fov * 0.5) * 20), pym + int(math.sin(angle + view_fov * 0.5) * 20))
                pygame.draw.line(screen, (90, 190, 120), (pxm, pym), fov_l, 1)
                pygame.draw.line(screen, (90, 190, 120), (pxm, pym), fov_r, 1)

                pause_text = font.render("PAUSED - Full Map", True, (235, 240, 245))
                hint_text = static_labels["pause_hint"]
                screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, 8))
                screen.blit(hint_text, (WIDTH // 2 - hint_text.get_width() // 2, 8 + pause_text.get_height()))

        elif state == "start":
            title = font.render("Maze FPS", True, (245, 245, 245))
            rule1 = font.render("WASD move, mouse look, left-click shoot, E teleport, F throw bomb", True, (220, 220, 220))
            rule2 = font.render("Blue item slows enemies, red item heals you.", True, (220, 220, 220))
            rule3 = font.render("Press 1-3 to choose gun. E/M/H (or F1/F2/F3) difficulty. ENTER starts.", True, (220, 220, 220))
            rule4 = font.render("Collect checkpoints to reveal minimap, then find the exit.", True, (220, 220, 220))
            rule5 = font.render("Level 2 has multiple stair entrances down.", True, (220, 220, 220))
            rule6 = font.render("Every 3rd level has a high-HP boss that fires projectiles.", True, (220, 220, 220))
            rule7 = font.render("Destroy turrets to unlock the exit.", True, (220, 220, 220))
            mode_txt = small_font.render(f"Difficulty: {difficulty_key.title()} (E easy / M medium / H hard)", True, (220, 230, 240))
            g1 = small_font.render(f"1 Shotgun: slow fire, high damage, wide crosshair ({'SELECTED' if selected_weapon == 'shotgun' else ''})", True, (230, 220, 220))
            g2 = small_font.render(f"2 Sniper: very high damage, very slow, right-click scope ({'SELECTED' if selected_weapon == 'sniper' else ''})", True, (220, 220, 235))
            g3 = small_font.render(f"3 Submachine Gun: very fast fire, low damage ({'SELECTED' if selected_weapon == 'smg' else ''})", True, (220, 235, 235))
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 70))
            screen.blit(rule1, (WIDTH // 2 - rule1.get_width() // 2, HEIGHT // 2 - 20))
            screen.blit(rule2, (WIDTH // 2 - rule2.get_width() // 2, HEIGHT // 2 + 20))
            screen.blit(rule4, (WIDTH // 2 - rule4.get_width() // 2, HEIGHT // 2 + 60))
            screen.blit(rule5, (WIDTH // 2 - rule5.get_width() // 2, HEIGHT // 2 + 95))
            screen.blit(rule6, (WIDTH // 2 - rule6.get_width() // 2, HEIGHT // 2 + 130))
            screen.blit(rule7, (WIDTH // 2 - rule7.get_width() // 2, HEIGHT // 2 + 160))
            screen.blit(rule3, (WIDTH // 2 - rule3.get_width() // 2, HEIGHT // 2 + 190))
            screen.blit(mode_txt, (WIDTH // 2 - mode_txt.get_width() // 2, HEIGHT // 2 + 220))
            screen.blit(g1, (WIDTH // 2 - g1.get_width() // 2, HEIGHT // 2 + 244))
            screen.blit(g2, (WIDTH // 2 - g2.get_width() // 2, HEIGHT // 2 + 266))
            screen.blit(g3, (WIDTH // 2 - g3.get_width() // 2, HEIGHT // 2 + 288))

        elif state == "end":
            over = font.render("You Died", True, (255, 120, 120))
            restart = font.render("Press 1-3 weapon, E/M/H difficulty, then ENTER to restart", True, (230, 230, 230))
            pick = small_font.render(f"Current: {WEAPONS[selected_weapon]['label']}  |  Difficulty: {difficulty_key.title()}", True, (220, 230, 235))
            screen.blit(over, (WIDTH // 2 - over.get_width() // 2, HEIGHT // 2 - 30))
            screen.blit(restart, (WIDTH // 2 - restart.get_width() // 2, HEIGHT // 2 + 15))
            screen.blit(pick, (WIDTH // 2 - pick.get_width() // 2, HEIGHT // 2 + 45))

        elif state == "level_complete":
            title = font.render("Level Complete!", True, (140, 230, 255))
            detail = font.render(f"Next Level: {pending_level}", True, (230, 230, 230))
            cont = font.render("Press ENTER to continue", True, (230, 230, 230))
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 50))
            screen.blit(detail, (WIDTH // 2 - detail.get_width() // 2, HEIGHT // 2 - 10))
            screen.blit(cont, (WIDTH // 2 - cont.get_width() // 2, HEIGHT // 2 + 30))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
