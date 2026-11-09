"""
AURORA - Airport layout and movement visualizer
Uses airport infrastructure and scheduled operations to render a simplified airport map:
- Loads airport infrastructure directly from MySQL (aurora_db)
- Renders runway geometry, taxiway centerlines, amber waypoints and aircraft markers
- Supports switching between Map 1 (DFW Hub) and Map 2 (BOM Hub)
- Interactive aircraft telemetry and waypoint route viewer
"""

import pygame
import math
from db import fetch_all, fetch_one
from ui_components import CompassHUD, COLOR_GRID, COLOR_ACCENT_CYAN, COLOR_RUNWAY_BLUE, COLOR_TEXT_YELLOW

class AirportMapView:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.current_airport_id = 1 # 1 = DFW (Map 1), 3 = BOM (Map 2)
        self.runways = []
        self.taxiways = []
        self.waypoints = []
        self.aircraft_markers = []
        self.selected_aircraft = None
        self.compass = CompassHUD(center=(self.rect.right - 80, self.rect.y + 80), radius=45)
        self.messages = [
            "TOWER: DFW Radar Scope Active",
            "RADAR: KDFW Ground Transponders Live",
            "SYSTEM: Real-time Database Link Established"
        ]
        # Load map data lazily when an authenticated administrator opens the map.

    def set_airport(self, airport_id):
        self.current_airport_id = airport_id
        self.selected_aircraft = None
        self.load_map_data()
        self.messages.append(f"RADAR: Switched Scope to Airport ID {airport_id}")

    def load_map_data(self):
        # 1. Runways from aurora_db
        rw_query = """
        SELECT runway_id, runway_designation, start_x, start_y, end_x, end_y, runway_status, surface_type, runway_length
        FROM runway
        WHERE airport_id = %s
        """
        self.runways = fetch_all(rw_query, (self.current_airport_id,))

        # 2. Taxiways from aurora_db
        tw_query = """
        SELECT taxiway_id, taxiway_name, start_x, start_y, end_x, end_y, surface_type
        FROM taxiway
        WHERE airport_id = %s
        """
        self.taxiways = fetch_all(tw_query, (self.current_airport_id,))

        # 3. Waypoints from map_feature in aurora_db
        wp_query = """
        SELECT mf.feature_id, mf.feature_name, mf.pos_x, mf.pos_y
        FROM map_feature mf
        JOIN airport_map am ON mf.map_id = am.map_id
        WHERE am.airport_id = %s
        """
        self.waypoints = fetch_all(wp_query, (self.current_airport_id,))

        # 4. Active flights at this station
        ac_query = """
        SELECT 
          fo.operation_id, fo.operation_type, fo.scheduled_datetime,
          f.flight_number, ac.registration_number, act.model, act.max_takeoff_weight,
          rd.designation AS assigned_direction, rw.runway_designation,
          rw.start_x, rw.start_y, rw.end_x, rw.end_y
        FROM flight_operation fo
        JOIN flight f ON fo.flight_id = f.flight_id
        JOIN aircraft ac ON f.aircraft_id = ac.aircraft_id
        JOIN aircraft_type act ON ac.type_id = act.type_id
        LEFT JOIN runway_assignment ra ON fo.operation_id = ra.operation_id
        LEFT JOIN runway_direction rd ON ra.direction_id = rd.direction_id
        LEFT JOIN runway rw ON rd.runway_id = rw.runway_id
        WHERE fo.airport_id = %s
        LIMIT 6
        """
        active_ops = fetch_all(ac_query, (self.current_airport_id,))

        self.aircraft_markers = []
        for idx, op in enumerate(active_ops):
            # Scale coordinates into radar display area
            if op.get("start_x") and op.get("end_x"):
                t = 0.2 + (0.15 * idx)
                px = op["start_x"] + t * (op["end_x"] - op["start_x"])
                py = op["start_y"] + t * (op["end_y"] - op["start_y"])
                heading = -math.degrees(math.atan2(op["end_y"] - op["start_y"], op["end_x"] - op["start_x"]))
            else:
                px = 125 + (idx * 60)
                py = 250 + (idx * 50)
                heading = 90

            self.aircraft_markers.append({
                "op": op,
                "x": px,
                "y": py,
                "heading": heading
            })

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # Check if an aircraft marker was clicked
            for ac in self.aircraft_markers:
                # Map coordinates relative to rect
                sx = self.rect.x + (ac["x"] * self.rect.width / 1000)
                sy = self.rect.y + (ac["y"] * self.rect.height / 1000)
                if math.hypot(mx - sx, my - sy) < 14:
                    self.selected_aircraft = ac
                    self.messages.append(f"PILOT: {ac['op']['flight_number']} reporting inbound beacon.")
                    return True
            # Clicking elsewhere deselects
            if self.rect.collidepoint(event.pos):
                self.selected_aircraft = None
        return False

    def draw(self, surface, font_main, font_small):
        # Clip drawing to radar sub-rectangle
        clip_rect = surface.get_clip()
        surface.set_clip(self.rect)

        # 1. Background
        pygame.draw.rect(surface, (17, 28, 40), self.rect)

        # 2. Subtle map grid
        grid_spacing = 35
        for x in range(self.rect.x, self.rect.right, grid_spacing):
            pygame.draw.line(surface, COLOR_GRID, (x, self.rect.y), (x, self.rect.bottom), 1)
        for y in range(self.rect.y, self.rect.bottom, grid_spacing):
            pygame.draw.line(surface, COLOR_GRID, (self.rect.x, y), (self.rect.right, y), 1)

        # Helper coordinate scaling function
        def to_screen(x, y):
            sx = self.rect.x + (x * self.rect.width / 1000)
            sy = self.rect.y + (y * self.rect.height / 1000)
            return int(sx), int(sy)

        # 3. Draw Apron / Terminal Parking Strip
        apron_start = to_screen(50, 0)
        apron_end = to_screen(150, 1000)
        pygame.draw.rect(surface, (27, 43, 57), (apron_start[0], self.rect.y, apron_end[0] - apron_start[0], self.rect.height))

        # 4. Draw taxiway centerlines
        for tw in self.taxiways:
            p1 = to_screen(tw["start_x"], tw["start_y"])
            p2 = to_screen(tw["end_x"], tw["end_y"])
            pygame.draw.line(surface, (107, 151, 174), p1, p2, 2)
            # Label
            mid = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)
            lbl = font_small.render(tw["taxiway_name"], True, (160, 190, 205))
            surface.blit(lbl, (mid[0] + 4, mid[1] - 8))

        # 5. Draw Runways (Thick Blue strips)
        for rw in self.runways:
            p1 = to_screen(rw["start_x"], rw["start_y"])
            p2 = to_screen(rw["end_x"], rw["end_y"])
            pygame.draw.line(surface, COLOR_RUNWAY_BLUE, p1, p2, 16)
            # Centerline dashed effect
            pygame.draw.line(surface, (240, 240, 240), p1, p2, 2)

            # Runway labels
            mid = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)
            lbl = font_small.render(f"RWY {rw['runway_designation']}", True, (255, 255, 255))
            surface.blit(lbl, (mid[0] - 25, mid[1] - 20))

        # 6. Draw infrastructure waypoints
        for wp in self.waypoints:
            p = to_screen(wp["pos_x"], wp["pos_y"])
            pygame.draw.circle(surface, (232, 190, 92), p, 5)
            pygame.draw.circle(surface, (255, 244, 220), p, 2)
            lbl = font_small.render(wp["feature_name"], True, (232, 206, 150))
            surface.blit(lbl, (p[0] + 6, p[1] - 6))

        # 7. Draw Aircraft Markers
        for ac in self.aircraft_markers:
            p = to_screen(ac["x"], ac["y"])
            is_sel = (self.selected_aircraft == ac)
            dot_color = (75, 178, 132) if is_sel else (220, 110, 105)

            # Pulsing target circle
            pygame.draw.circle(surface, dot_color, p, 7 if is_sel else 5)
            if is_sel:
                pygame.draw.circle(surface, COLOR_ACCENT_CYAN, p, 12, 1)

            # Heading vector line
            h_rad = math.radians(ac["heading"])
            end_x = p[0] + 25 * math.cos(h_rad)
            end_y = p[1] - 25 * math.sin(h_rad)
            pygame.draw.line(surface, (255, 200, 200), p, (int(end_x), int(end_y)), 2)

            # Flight text tag
            tag_str = f"{ac['op']['flight_number']} ({ac['op']['model'][:6]})"
            t_surf = font_small.render(tag_str, True, (255, 255, 255))
            surface.blit(t_surf, (p[0] - 20, p[1] - 18))

        # 8. Compass HUD (Top Right)
        active_heading = self.selected_aircraft["heading"] if self.selected_aircraft else 103
        self.compass.draw(surface, active_heading, font_small)

        # 9. Tactical Message Log Box (Bottom Right)
        msg_box_rect = pygame.Rect(self.rect.right - 340, self.rect.bottom - 110, 330, 100)
        pygame.draw.rect(surface, (15, 25, 35, 220), msg_box_rect, border_radius=4)
        pygame.draw.rect(surface, (0, 100, 150), msg_box_rect, width=1, border_radius=4)

        log_hdr = font_small.render("ATC RADAR COMMUNICATIONS LOG", True, COLOR_ACCENT_CYAN)
        surface.blit(log_hdr, (msg_box_rect.x + 8, msg_box_rect.y + 6))
        for idx, m in enumerate(self.messages[-3:]):
            m_surf = font_small.render(m, True, (220, 230, 240))
            surface.blit(m_surf, (msg_box_rect.x + 8, msg_box_rect.y + 28 + (idx * 20)))

        # 10. Selected Aircraft Details Panel (Bottom Left overlay)
        if self.selected_aircraft:
            op = self.selected_aircraft["op"]
            panel_rect = pygame.Rect(self.rect.x + 20, self.rect.bottom - 150, 360, 135)
            pygame.draw.rect(surface, (15, 24, 34), panel_rect, border_radius=6)
            pygame.draw.rect(surface, COLOR_ACCENT_CYAN, panel_rect, width=1, border_radius=6)

            title = font_main.render(f"TARGET: {op['flight_number']} [{op['registration_number']}]", True, COLOR_TEXT_YELLOW)
            surface.blit(title, (panel_rect.x + 12, panel_rect.y + 10))

            info_lines = [
                f"Airframe Type: {op['model']} (MTOW {float(op['max_takeoff_weight']):,.0f} kg)",
                f"Operation: {op['operation_type']} @ {op['scheduled_datetime']}",
                f"Assigned Vector: {op['assigned_direction'] or 'UNASSIGNED'} ({op['runway_designation'] or 'PENDING'})",
                f"Calculated Heading: {self.selected_aircraft['heading']:.1f}°"
            ]
            for idx, ln in enumerate(info_lines):
                ln_surf = font_small.render(ln, True, (230, 240, 250))
                surface.blit(ln_surf, (panel_rect.x + 12, panel_rect.y + 38 + (idx * 22)))

        # Scope Border
        pygame.draw.rect(surface, (40, 60, 85), self.rect, width=1)
        surface.set_clip(clip_rect)
