"""
AURORA - Main Desktop Pygame Application
Integrates all operational views:
  1. Dashboard & Schedule
  2. Manual Runway Assignment & Validation Engine
  3. Airport Map (Map 1 & Map 2)
  4. Fleet & Infrastructure Management
  5. Academic DBMS SQL Concept Demonstrator
"""

import pygame
import sys
from auth import authenticate, has_permission
from db import fetch_all, fetch_one, execute, transaction
from validator import validate_runway_assignment
from ui_components import (
    Button, StatCard, DataTable, ModalDialog,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT_CYAN, COLOR_RUNWAY_BLUE,
    COLOR_TEXT_WHITE, COLOR_TEXT_MUTED, COLOR_TEXT_YELLOW,
    COLOR_SUCCESS_GREEN, COLOR_ALERT_RED
)
from airport_map import AirportMapView

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800

class AuroraApp:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("AURORA | Airport Operations & Departure Information")
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_title = pygame.font.SysFont("Segoe UI, Arial", 20, bold=True)
        self.font_hdr = pygame.font.SysFont("Segoe UI, Arial", 15, bold=True)
        self.font_main = pygame.font.SysFont("Segoe UI, Arial", 13)
        self.font_sub = pygame.font.SysFont("Segoe UI, Arial", 11)
        self.font_card_val = pygame.font.SysFont("Segoe UI, Arial", 24, bold=True)

        # Authentication state. No operational query runs before login.
        self.current_user = None
        self.login_username = ""
        self.login_password = ""
        self.login_active_field = "username"
        self.login_message = ""
        self.login_button = Button((480, 520, 240, 48), "SIGN IN", self.font_hdr,
                                   on_click=self.on_login, bg_color=(31, 111, 148))
        self.logout_button = Button((1050, 13, 125, 36), "SIGN OUT", self.font_sub,
                                    on_click=self.logout)

        # State
        self.current_tab = "DASHBOARD"
        self.active_modal = None
        self.stats = {}

        # Top Nav Buttons
        nav_y = 13
        btn_w = 145
        self.nav_buttons = [
            Button((250 + i * (btn_w + 10), nav_y, btn_w, 36), title, self.font_hdr,
                   on_click=lambda t=key: self.set_tab(t), active=(key == "DASHBOARD"))
            for i, (title, key) in enumerate([
                ("OVERVIEW", "DASHBOARD"),
                ("ASSIGN", "ASSIGNMENT"),
                ("MAP", "RADAR"),
                ("FLEET", "FLEET"),
                ("REPORTS", "REPORTS")
            ])
        ]

        # Views & Data
        self.customer_table = DataTable((42, 250, WINDOW_WIDTH - 84, WINDOW_HEIGHT - 300),
                                        ["FLIGHT", "AIRLINE", "FROM", "TO", "SCHEDULED DEPARTURE", "STATUS"],
                                        [130, 220, 100, 100, 260, 150], self.font_main)
        self.radar_view = AirportMapView((20, 95, WINDOW_WIDTH - 40, WINDOW_HEIGHT - 115))
        self.init_dashboard_view()
        self.init_assignment_view()
        self.init_fleet_view()
        self.init_reports_view()

        # Data is loaded only after an authenticated session is established.

    def on_login(self):
        try:
            user = authenticate(self.login_username, self.login_password)
        except Exception as exc:
            self.login_message = f"Database unavailable: {exc}"
            return
        if not user:
            self.login_message = "Invalid username or password, or account disabled."
            self.login_password = ""
            return
        self.current_user = user
        self.login_password = ""
        self.login_message = ""
        if user["role_code"] == "ADMIN":
            self.current_tab = "DASHBOARD"
            self.refresh_all_data()
        else:
            self.refresh_customer_schedule()

    def logout(self):
        self.current_user = None
        self.login_username = ""
        self.login_password = ""
        self.login_active_field = "username"
        self.current_tab = "DASHBOARD"
        self.active_modal = None

    def refresh_customer_schedule(self):
        rows = fetch_all("""
            SELECT flight_number, airline_name, departure_airport,
                   destination_airport, scheduled_datetime, operation_status
            FROM view_scheduled_departures
            ORDER BY scheduled_datetime ASC
        """)
        self.customer_table.set_data([
            [r["flight_number"], r["airline_name"], r["departure_airport"],
             r["destination_airport"], str(r["scheduled_datetime"]), r["operation_status"]]
            for r in rows
        ])

    def handle_login_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if pygame.Rect(390, 340, 420, 48).collidepoint(event.pos):
                self.login_active_field = "username"
            elif pygame.Rect(390, 410, 420, 48).collidepoint(event.pos):
                self.login_active_field = "password"
            else:
                self.login_button.handle_event(event)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                self.login_active_field = "password" if self.login_active_field == "username" else "username"
            elif event.key == pygame.K_RETURN:
                self.on_login()
            elif event.key == pygame.K_BACKSPACE:
                if self.login_active_field == "username":
                    self.login_username = self.login_username[:-1]
                else:
                    self.login_password = self.login_password[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.login_password = ""
            elif event.unicode.isprintable() and event.unicode:
                if self.login_active_field == "username" and len(self.login_username) < 60:
                    self.login_username += event.unicode
                elif self.login_active_field == "password" and len(self.login_password) < 128:
                    self.login_password += event.unicode

    def set_tab(self, tab_key):
        if not self.current_user or not has_permission(self.current_user, {
            "DASHBOARD": "operations.read", "ASSIGNMENT": "assignment.manage",
            "RADAR": "radar.read", "FLEET": "fleet.read", "REPORTS": "reports.read"
        }.get(tab_key, "operations.read")):
            return
        self.current_tab = tab_key
        active_label = {
            "DASHBOARD": "OVERVIEW", "ASSIGNMENT": "ASSIGN",
            "RADAR": "MAP", "FLEET": "FLEET", "REPORTS": "REPORTS"
        }.get(tab_key)
        for btn in self.nav_buttons:
            btn.active = btn.text == active_label
        if tab_key == "DASHBOARD":
            self.refresh_dashboard()
        elif tab_key == "ASSIGNMENT":
            self.refresh_assignment_data()
        elif tab_key == "FLEET":
            self.refresh_fleet_data()
        elif tab_key == "RADAR":
            self.radar_view.load_map_data()

    def show_modal(self, title, message, is_success):
        self.active_modal = ModalDialog(title, message, is_success, on_close=self.close_modal)

    def close_modal(self):
        self.active_modal = None

    # =========================================================================
    # VIEW INITIALIZERS & DATA LOADERS
    # =========================================================================
    def init_dashboard_view(self):
        # Schedule Table
        cols = ["ID", "FLIGHT", "AIRLINE", "TYPE", "STATION", "SCHEDULED TIME", "ASSIGNED VECTOR", "STATUS"]
        widths = [45, 95, 170, 90, 80, 210, 160, 110]
        self.schedule_table = DataTable((20, 215, WINDOW_WIDTH - 40, WINDOW_HEIGHT - 235), cols, widths, self.font_main)

    def init_assignment_view(self):
        # Operations List Table (Left)
        op_cols = ["ID", "FLIGHT", "STATION", "TYPE", "SCHEDULED TIME", "ASSIGNED"]
        op_widths = [40, 90, 75, 85, 190, 120]
        self.assign_op_table = DataTable((20, 105, 620, WINDOW_HEIGHT - 125), op_cols, op_widths, self.font_main)

        # Available Directions Table (Right)
        dir_cols = ["DIR ID", "VECTOR", "RWY", "AIRPORT", "LAND", "T/O", "ILS", "CATEGORY"]
        dir_widths = [60, 65, 75, 70, 55, 55, 50, 80]
        self.assign_dir_table = DataTable((660, 105, 520, 360), dir_cols, dir_widths, self.font_main)

        # Action Buttons
        self.btn_validate = Button((660, 485, 250, 42), "CHECK VALIDATION RULES", self.font_hdr,
                                   on_click=self.on_validate_assignment, bg_color=(20, 80, 120))
        self.btn_confirm = Button((930, 485, 250, 42), "CONFIRM ASSIGNMENT", self.font_hdr,
                                  on_click=self.on_confirm_assignment, bg_color=(30, 120, 60))
        self.btn_cancel_assignment = Button((660, 540, 250, 36), "CANCEL CURRENT VECTOR", self.font_main,
                                           on_click=self.on_cancel_assignment, bg_color=(120, 40, 40))

    def init_fleet_view(self):
        self.fleet_subtab = "AIRCRAFT"
        self.fleet_buttons = [
            Button((20, 70, 140, 30), "AIRCRAFT FLEET", self.font_sub,
                   on_click=lambda: self.set_fleet_subtab("AIRCRAFT"), active=True),
            Button((170, 70, 140, 30), "AIRCRAFT TYPES", self.font_sub,
                   on_click=lambda: self.set_fleet_subtab("TYPES")),
            Button((320, 70, 140, 30), "AIRLINES", self.font_sub,
                   on_click=lambda: self.set_fleet_subtab("AIRLINES")),
            Button((470, 70, 140, 30), "AIRPORTS", self.font_sub,
                   on_click=lambda: self.set_fleet_subtab("AIRPORTS"))
        ]
        self.fleet_table = DataTable((20, 112, WINDOW_WIDTH - 40, WINDOW_HEIGHT - 132), [], [], self.font_main)

    def set_fleet_subtab(self, subtab):
        self.fleet_subtab = subtab
        for b in self.fleet_buttons:
            b.active = (subtab in b.text)
        self.refresh_fleet_data()

    def init_reports_view(self):
        self.current_report_key = "UNASSIGNED"
        self.report_buttons = [
            Button((20, 70, 220, 30), "1. UNASSIGNED (ANTI-JOIN)", self.font_sub,
                   on_click=lambda: self.load_report("UNASSIGNED"), active=True),
            Button((250, 70, 220, 30), "2. COMPATIBILITY MATRIX", self.font_sub,
                   on_click=lambda: self.load_report("COMPATIBILITY")),
            Button((480, 70, 220, 30), "3. OPERATOR FLEET AGG", self.font_sub,
                   on_click=lambda: self.load_report("OPERATOR_AGG")),
            Button((710, 70, 220, 30), "4. INFRASTRUCTURE STATS", self.font_sub,
                   on_click=lambda: self.load_report("INFRASTRUCTURE")),
            Button((940, 70, 220, 30), "5. AUDIT TRAIL LOGS", self.font_sub,
                   on_click=lambda: self.load_report("AUDIT"))
        ]
        self.report_title = "Unassigned Operations (Outer Anti-Join)"
        self.report_sql = "SELECT fo.operation_id, f.flight_number... FROM flight_operation fo LEFT JOIN runway_assignment ra..."
        self.report_table = DataTable((20, 170, WINDOW_WIDTH - 40, WINDOW_HEIGHT - 190), [], [], self.font_main)

    def refresh_all_data(self):
        try:
            self.refresh_dashboard()
            self.refresh_assignment_data()
            self.refresh_fleet_data()
            self.load_report(self.current_report_key)
        except Exception as e:
            print(f"Initial DB connect warning: {e}")

    def refresh_dashboard(self):
        # Stats counts
        try:
            ac_res = fetch_one("SELECT COUNT(*) AS total, SUM(CASE WHEN aircraft_status='ACTIVE' THEN 1 ELSE 0 END) AS active FROM aircraft") or {}
            ap_res = fetch_one("SELECT COUNT(*) AS cnt FROM airport") or {}
            rw_res = fetch_one("SELECT COUNT(*) AS cnt FROM runway") or {}
            op_res = fetch_one("SELECT COUNT(fo.operation_id) AS total, SUM(CASE WHEN ra.assignment_id IS NULL THEN 1 ELSE 0 END) AS unassigned FROM flight_operation fo LEFT JOIN runway_assignment ra ON fo.operation_id = ra.operation_id") or {}

            self.stats = {
                "total_ac": ac_res.get("total", 0),
                "active_ac": ac_res.get("active", 0),
                "airports": ap_res.get("cnt", 0),
                "runways": rw_res.get("cnt", 0),
                "total_ops": op_res.get("total", 0),
                "unassigned_ops": op_res.get("unassigned", 0)
            }

            # Operations list
            ops = fetch_all("""
            SELECT 
              fo.operation_id, f.flight_number, al.airline_name, fo.operation_type,
              ap.iata_code AS station, fo.scheduled_datetime,
              COALESCE(rd.designation, 'UNASSIGNED') AS assigned_vector,
              fo.operation_status
            FROM flight_operation fo
            JOIN flight f ON fo.flight_id = f.flight_id
            JOIN airline al ON f.airline_id = al.airline_id
            JOIN airport ap ON fo.airport_id = ap.airport_id
            LEFT JOIN runway_assignment ra ON fo.operation_id = ra.operation_id
            LEFT JOIN runway_direction rd ON ra.direction_id = rd.direction_id
            ORDER BY fo.scheduled_datetime ASC
            """)
            table_rows = [
                [r["operation_id"], r["flight_number"], r["airline_name"][:18], r["operation_type"],
                 r["station"], str(r["scheduled_datetime"]), r["assigned_vector"], r["operation_status"]]
                for r in ops
            ]
            self.schedule_table.set_data(table_rows)
        except Exception as e:
            print(f"Error refreshing dashboard: {e}")

    def refresh_assignment_data(self):
        try:
            ops = fetch_all("""
            SELECT 
              fo.operation_id, f.flight_number, ap.iata_code AS station,
              fo.operation_type, fo.scheduled_datetime,
              COALESCE(rd.designation, 'NONE') AS assigned
            FROM flight_operation fo
            JOIN flight f ON fo.flight_id = f.flight_id
            JOIN airport ap ON fo.airport_id = ap.airport_id
            LEFT JOIN runway_assignment ra ON fo.operation_id = ra.operation_id
            LEFT JOIN runway_direction rd ON ra.direction_id = rd.direction_id
            ORDER BY (ra.assignment_id IS NOT NULL), fo.scheduled_datetime ASC
            """)
            self.assign_op_table.set_data([
                [r["operation_id"], r["flight_number"], r["station"], r["operation_type"],
                 str(r["scheduled_datetime"]), r["assigned"]]
                for r in ops
            ])

            dirs = fetch_all("""
            SELECT 
              rd.direction_id, rd.designation, rw.runway_designation,
              ap.iata_code AS airport_code,
              CASE WHEN rd.landing_permitted=1 THEN 'YES' ELSE 'NO' END AS land,
              CASE WHEN rd.takeoff_permitted=1 THEN 'YES' ELSE 'NO' END AS to_perm,
              CASE WHEN rd.ils_available=1 THEN 'YES' ELSE 'NO' END AS ils,
              rd.approach_category
            FROM runway_direction rd
            JOIN runway rw ON rd.runway_id = rw.runway_id
            JOIN airport ap ON rw.airport_id = ap.airport_id
            ORDER BY ap.iata_code, rd.designation
            """)
            self.assign_dir_table.set_data([
                [r["direction_id"], r["designation"], r["runway_designation"], r["airport_code"],
                 r["land"], r["to_perm"], r["ils"], r["approach_category"]]
                for r in dirs
            ])
        except Exception as e:
            print(f"Error refreshing assignment data: {e}")

    def refresh_fleet_data(self):
        try:
            if self.fleet_subtab == "AIRCRAFT":
                rows = fetch_all("""
                SELECT ac.aircraft_id, ac.registration_number, act.model, al.airline_name,
                       ac.aircraft_status, ac.manufacturing_date
                FROM aircraft ac
                JOIN aircraft_type act ON ac.type_id = act.type_id
                JOIN airline al ON ac.operator_airline_id = al.airline_id
                ORDER BY ac.registration_number
                """)
                cols = ["ID", "REGISTRATION", "MODEL", "OPERATOR AIRLINE", "STATUS", "MANUFACTURED"]
                widths = [50, 140, 220, 280, 140, 160]
                self.fleet_table.columns = cols
                self.fleet_table.col_widths = widths
                self.fleet_table.set_data([[r["aircraft_id"], r["registration_number"], r["model"],
                                            r["airline_name"], r["aircraft_status"], str(r["manufacturing_date"])]
                                           for r in rows])

            elif self.fleet_subtab == "TYPES":
                rows = fetch_all("""
                SELECT type_id, manufacturer, model, variant, aircraft_category,
                       passenger_capacity, max_takeoff_weight, min_runway_length
                FROM aircraft_type ORDER BY manufacturer, model
                """)
                cols = ["ID", "MANUFACTURER", "MODEL", "VARIANT", "CAT", "PAX", "MTOW (KG)", "MIN RWY (M)"]
                widths = [45, 160, 180, 160, 100, 70, 140, 130]
                self.fleet_table.columns = cols
                self.fleet_table.col_widths = widths
                self.fleet_table.set_data([[r["type_id"], r["manufacturer"], r["model"], r["variant"],
                                            r["aircraft_category"], r["passenger_capacity"],
                                            f"{float(r['max_takeoff_weight']):,.0f}", f"{float(r['min_runway_length']):,.0f}"]
                                           for r in rows])

            elif self.fleet_subtab == "AIRLINES":
                rows = fetch_all("SELECT airline_id, airline_name, iata_code, icao_code, country, callsign, operating_status FROM airline")
                cols = ["ID", "AIRLINE NAME", "IATA", "ICAO", "COUNTRY", "CALLSIGN", "STATUS"]
                widths = [50, 260, 80, 80, 180, 160, 120]
                self.fleet_table.columns = cols
                self.fleet_table.col_widths = widths
                self.fleet_table.set_data([[r["airline_id"], r["airline_name"], r["iata_code"],
                                            r["icao_code"], r["country"], r["callsign"], r["operating_status"]]
                                           for r in rows])

            elif self.fleet_subtab == "AIRPORTS":
                rows = fetch_all("""
                SELECT ap.airport_id, ap.iata_code, ap.icao_code, ap.airport_name, ap.city, ap.country,
                       ap.elevation, COUNT(rw.runway_id) AS runways_cnt
                FROM airport ap
                LEFT JOIN runway rw ON ap.airport_id = rw.airport_id
                GROUP BY ap.airport_id, ap.iata_code, ap.icao_code, ap.airport_name, ap.city, ap.country, ap.elevation
                """)
                cols = ["ID", "IATA", "ICAO", "AIRPORT NAME", "CITY", "COUNTRY", "ELEV (M)", "RUNWAYS"]
                widths = [45, 75, 75, 300, 160, 140, 95, 90]
                self.fleet_table.columns = cols
                self.fleet_table.col_widths = widths
                self.fleet_table.set_data([[r["airport_id"], r["iata_code"], r["icao_code"],
                                            r["airport_name"], r["city"], r["country"],
                                            f"{float(r['elevation']):.1f}", r["runways_cnt"]]
                                           for r in rows])
        except Exception as e:
            print(f"Error in fleet data: {e}")

    def load_report(self, report_key):
        self.current_report_key = report_key
        for b in self.report_buttons:
            b.active = (report_key in b.text or 
                        (report_key == "UNASSIGNED" and "UNASSIGNED" in b.text) or
                        (report_key == "COMPATIBILITY" and "COMPATIBILITY" in b.text) or
                        (report_key == "OPERATOR_AGG" and "OPERATOR" in b.text) or
                        (report_key == "INFRASTRUCTURE" and "INFRASTRUCTURE" in b.text) or
                        (report_key == "AUDIT" and "AUDIT" in b.text))
        try:
            if report_key == "UNASSIGNED":
                self.report_title = "Unassigned Operations (Outer Anti-Join)"
                self.report_sql = "SELECT fo.operation_id, f.flight_number, al.airline_name, ap.iata_code, fo.scheduled_datetime FROM flight_operation fo LEFT JOIN runway_assignment ra ON fo.operation_id = ra.operation_id WHERE ra.assignment_id IS NULL"
                rows = fetch_all("""
                SELECT fo.operation_id, f.flight_number, al.airline_name, ap.iata_code,
                       fo.operation_type, fo.scheduled_datetime, fo.operation_status
                FROM flight_operation fo
                JOIN flight f ON fo.flight_id = f.flight_id
                JOIN airline al ON f.airline_id = al.airline_id
                JOIN airport ap ON fo.airport_id = ap.airport_id
                LEFT JOIN runway_assignment ra ON fo.operation_id = ra.operation_id
                WHERE ra.assignment_id IS NULL
                """)
                cols = ["OP ID", "FLIGHT", "AIRLINE", "AIRPORT", "TYPE", "SCHEDULED TIME", "STATUS"]
                widths = [60, 110, 220, 95, 100, 220, 140]
                self.report_table.columns = cols
                self.report_table.col_widths = widths
                self.report_table.set_data([[r["operation_id"], r["flight_number"], r["airline_name"],
                                             r["iata_code"], r["operation_type"], str(r["scheduled_datetime"]), r["operation_status"]]
                                            for r in rows])

            elif report_key == "COMPATIBILITY":
                self.report_title = "Aircraft-Runway Compatibility Matrix (Relational Intersect)"
                self.report_sql = "SELECT act.model, ap.iata_code, rw.runway_designation, arc.landing_eligible, arc.takeoff_eligible, arc.remarks FROM aircraft_runway_compatibility arc JOIN aircraft_type act..."
                rows = fetch_all("""
                SELECT act.model, ap.iata_code, rw.runway_designation,
                       CASE WHEN arc.landing_eligible=1 THEN 'YES' ELSE 'NO' END AS landing_ok,
                       CASE WHEN arc.takeoff_eligible=1 THEN 'YES' ELSE 'NO' END AS takeoff_ok,
                       COALESCE(arc.remarks, 'Certified standard') AS remarks
                FROM aircraft_runway_compatibility arc
                JOIN aircraft_type act ON arc.type_id = act.type_id
                JOIN runway rw ON arc.runway_id = rw.runway_id
                JOIN airport ap ON rw.airport_id = ap.airport_id
                ORDER BY act.model, ap.iata_code
                """)
                cols = ["AIRCRAFT MODEL", "AIRPORT", "RUNWAY", "LANDING OK", "TAKEOFF OK", "RESTRICTIONS / REMARKS"]
                widths = [190, 85, 95, 105, 105, 420]
                self.report_table.columns = cols
                self.report_table.col_widths = widths
                self.report_table.set_data([[r["model"], r["iata_code"], r["runway_designation"],
                                             r["landing_ok"], r["takeoff_ok"], r["remarks"][:55]]
                                            for r in rows])

            elif report_key == "OPERATOR_AGG":
                self.report_title = "Aircraft Fleet Aggregation by Airline (GROUP BY & HAVING)"
                self.report_sql = "SELECT al.airline_name, act.aircraft_category, COUNT(ac.aircraft_id) AS airframes, SUM(CASE WHEN ac.aircraft_status='ACTIVE' THEN 1 ELSE 0 END) AS active_frames FROM aircraft ac GROUP BY al.airline_name, act.aircraft_category"
                rows = fetch_all("""
                SELECT al.airline_name, act.aircraft_category,
                       COUNT(ac.aircraft_id) AS total_frames,
                       SUM(CASE WHEN ac.aircraft_status='ACTIVE' THEN 1 ELSE 0 END) AS active_frames
                FROM aircraft ac
                JOIN airline al ON ac.operator_airline_id = al.airline_id
                JOIN aircraft_type act ON ac.type_id = act.type_id
                GROUP BY al.airline_name, act.aircraft_category
                ORDER BY al.airline_name
                """)
                cols = ["AIRLINE NAME", "AIRCRAFT CATEGORY", "TOTAL FLEET COUNT", "ACTIVE FLEET COUNT"]
                widths = [320, 220, 200, 200]
                self.report_table.columns = cols
                self.report_table.col_widths = widths
                self.report_table.set_data([[r["airline_name"], r["aircraft_category"], r["total_frames"], r["active_frames"]]
                                            for r in rows])

            elif report_key == "INFRASTRUCTURE":
                self.report_title = "Airport Infrastructure Summary (Relational View Integration)"
                self.report_sql = "SELECT * FROM view_airport_infrastructure_summary"
                rows = fetch_all("SELECT * FROM view_airport_infrastructure_summary")
                cols = ["IATA", "ICAO", "AIRPORT NAME", "CITY", "RUNWAYS", "DIRECTIONS", "TAXIWAYS", "TERMINALS", "STANDS"]
                widths = [75, 75, 290, 150, 85, 90, 85, 90, 80]
                self.report_table.columns = cols
                self.report_table.col_widths = widths
                self.report_table.set_data([[r["iata_code"], r["icao_code"], r["airport_name"],
                                             r["city"], r["runway_count"], r["direction_count"],
                                             r["taxiway_count"], r["terminal_count"], r["stand_count"]]
                                            for r in rows])

            elif report_key == "AUDIT":
                self.report_title = "Assignment Audit Trail (Automatic Trigger Log)"
                self.report_sql = "SELECT aa.audit_id, f.flight_number, aa.old_status, aa.new_status, aa.action_type, aa.changed_by, aa.changed_at FROM assignment_audit aa JOIN flight_operation fo..."
                rows = fetch_all("""
                SELECT aa.audit_id, f.flight_number, fo.operation_type,
                       COALESCE(aa.old_status, 'NULL') AS old_st,
                       aa.new_status, aa.action_type, aa.changed_by, aa.changed_at
                FROM assignment_audit aa
                JOIN flight_operation fo ON aa.operation_id = fo.operation_id
                JOIN flight f ON fo.flight_id = f.flight_id
                ORDER BY aa.changed_at DESC
                LIMIT 50
                """)
                cols = ["AUDIT ID", "FLIGHT", "OPERATION", "OLD STATUS", "NEW STATUS", "ACTION", "OPERATOR", "TIMESTAMP"]
                widths = [75, 110, 120, 110, 110, 95, 150, 220]
                self.report_table.columns = cols
                self.report_table.col_widths = widths
                self.report_table.set_data([[r["audit_id"], r["flight_number"], r["operation_type"],
                                             r["old_st"], r["new_status"], r["action_type"],
                                             r["changed_by"], str(r["changed_at"])]
                                            for r in rows])
        except Exception as e:
            print(f"Error loading report {report_key}: {e}")

    # =========================================================================
    # EVENT HANDLERS
    # =========================================================================
    def on_validate_assignment(self):
        if not has_permission(self.current_user, "assignment.manage"):
            self.show_modal("ACCESS DENIED", "Your account cannot manage runway assignments.", False)
            return
        sel_op = self.assign_op_table.get_selected_row()
        sel_dir = self.assign_dir_table.get_selected_row()

        if not sel_op:
            self.show_modal("SELECTION REQUIRED", "Please select a flight operation row on the left table.", False)
            return
        if not sel_dir:
            self.show_modal("SELECTION REQUIRED", "Please select a candidate runway direction row on the right table.", False)
            return

        op_id = sel_op[0]
        dir_id = sel_dir[0]
        result = validate_runway_assignment(op_id, dir_id)

        title = "RULE VALIDATION PASSED" if result.is_valid else "VALIDATION REJECTED"
        self.show_modal(title, result.reason, result.is_valid)

    def on_confirm_assignment(self):
        if not has_permission(self.current_user, "assignment.manage"):
            self.show_modal("ACCESS DENIED", "Your account cannot manage runway assignments.", False)
            return
        sel_op = self.assign_op_table.get_selected_row()
        sel_dir = self.assign_dir_table.get_selected_row()

        if not sel_op or not sel_dir:
            self.show_modal("SELECTION ERROR", "Please select both a flight operation and a candidate runway vector.", False)
            return

        op_id = sel_op[0]
        dir_id = sel_dir[0]
        # Lock the operation and candidate runway while revalidating and writing.
        # This closes the previous validate-then-insert race between concurrent users.
        try:
            with transaction() as cursor:
                result = validate_runway_assignment(op_id, dir_id, cursor=cursor)
                if not result.is_valid:
                    self.show_modal("CANNOT COMMIT INVALID ASSIGNMENT", result.reason, False)
                    return
                cursor.execute(
                    "SELECT assignment_id FROM runway_assignment WHERE operation_id = %s FOR UPDATE",
                    (op_id,),
                )
                existing = cursor.fetchone()
                if existing:
                    cursor.execute("""
                        UPDATE runway_assignment
                        SET direction_id = %s, assignment_status = 'CONFIRMED',
                            assignment_datetime = NOW(), assigned_by = %s
                        WHERE operation_id = %s
                    """, (dir_id, self.current_user["username"], op_id))
                else:
                    cursor.execute("""
                        INSERT INTO runway_assignment
                            (operation_id, direction_id, assignment_status, assigned_by, remarks)
                        VALUES (%s, %s, 'CONFIRMED', %s, 'Manual assignment validated and saved')
                    """, (op_id, dir_id, self.current_user["username"]))

            self.show_modal(
                "ASSIGNMENT RECORDED",
                f"Runway direction {sel_dir[1]} on {sel_dir[2]} confirmed for {sel_op[1]}. Audit trigger recorded the change.",
                True,
            )
            self.refresh_assignment_data()
            self.refresh_dashboard()
        except Exception as e:
            self.show_modal("DATABASE ERROR", f"Transaction rolled back: {e}", False)

    def on_cancel_assignment(self):
        if not has_permission(self.current_user, "assignment.manage"):
            self.show_modal("ACCESS DENIED", "Your account cannot manage runway assignments.", False)
            return
        sel_op = self.assign_op_table.get_selected_row()
        if not sel_op:
            self.show_modal("SELECTION ERROR", "Select an operation on the left to cancel its runway assignment.", False)
            return
        op_id = sel_op[0]
        try:
            execute("DELETE FROM runway_assignment WHERE operation_id = %s", (op_id,))
            self.show_modal("ASSIGNMENT CANCELLED", f"Cleared runway vector for Operation {sel_op[1]}. Audit trigger recorded.", True)
            self.refresh_assignment_data()
            self.refresh_dashboard()
        except Exception as e:
            self.show_modal("ERROR", f"Failed to cancel: {e}", False)

    # =========================================================================
    # MAIN LOOP & DRAW ROUTINES
    # =========================================================================
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                if not self.current_user:
                    self.handle_login_event(event)
                    continue
                if self.active_modal:
                    self.active_modal.handle_event(event)
                    continue
                for btn in self.nav_buttons:
                    btn.handle_event(event)
                self.logout_button.handle_event(event)
                if self.current_user["role_code"] == "CUSTOMER":
                    self.customer_table.handle_event(event)
                elif self.current_tab == "DASHBOARD":
                    self.schedule_table.handle_event(event)
                elif self.current_tab == "ASSIGNMENT":
                    self.assign_op_table.handle_event(event)
                    self.assign_dir_table.handle_event(event)
                    self.btn_validate.handle_event(event)
                    self.btn_confirm.handle_event(event)
                    self.btn_cancel_assignment.handle_event(event)
                elif self.current_tab == "RADAR":
                    self.radar_view.handle_event(event)
                elif self.current_tab == "FLEET":
                    for b in self.fleet_buttons:
                        b.handle_event(event)
                    self.fleet_table.handle_event(event)
                elif self.current_tab == "REPORTS":
                    for b in self.report_buttons:
                        b.handle_event(event)
                    self.report_table.handle_event(event)
            self.draw()
            pygame.display.flip()
            self.clock.tick(30)
        pygame.quit()
        sys.exit()

    def draw_login(self):
        self.screen.fill(COLOR_BG)
        pygame.draw.rect(self.screen, COLOR_PANEL, (0, 0, WINDOW_WIDTH, 86))
        brand = self.font_title.render("AURORA", True, COLOR_TEXT_WHITE)
        tagline = self.font_main.render("AIRPORT OPERATIONS & DEPARTURE INFORMATION", True, COLOR_TEXT_MUTED)
        self.screen.blit(brand, (56, 22))
        self.screen.blit(tagline, (190, 29))
        title = self.font_title.render("Welcome back", True, COLOR_TEXT_WHITE)
        subtitle = self.font_main.render("Sign in to continue to the airport operations system.", True, COLOR_TEXT_MUTED)
        self.screen.blit(title, (390, 245))
        self.screen.blit(subtitle, (390, 278))
        for label, value, y, active in [
            ("USERNAME", self.login_username, 340, self.login_active_field == "username"),
            ("PASSWORD", "*" * len(self.login_password), 410, self.login_active_field == "password")
        ]:
            lbl = self.font_sub.render(label, True, COLOR_TEXT_MUTED)
            self.screen.blit(lbl, (390, y - 22))
            rect = pygame.Rect(390, y, 420, 48)
            pygame.draw.rect(self.screen, COLOR_PANEL, rect, border_radius=7)
            pygame.draw.rect(self.screen, COLOR_ACCENT_CYAN if active else (52, 67, 84), rect, 2, border_radius=7)
            value_surf = self.font_main.render(value or ("Enter " + label.lower()), True,
                                                COLOR_TEXT_WHITE if value else COLOR_TEXT_MUTED)
            self.screen.blit(value_surf, (408, y + 14))
        self.login_button.draw(self.screen)
        if self.login_message:
            msg = self.font_sub.render(self.login_message[:90], True, COLOR_ALERT_RED)
            self.screen.blit(msg, (390, 585))
        hint = self.font_sub.render("DEMO ACCOUNTS  |  admin / AuroraAdmin!2026   •   customer / AuroraGuest!2026",
                                    True, COLOR_TEXT_MUTED)
        self.screen.blit(hint, (330, 650))

    def draw_customer(self):
        self.screen.fill(COLOR_BG)
        pygame.draw.rect(self.screen, COLOR_PANEL, (0, 0, WINDOW_WIDTH, 70))
        brand = self.font_title.render("AURORA", True, COLOR_TEXT_WHITE)
        role = self.font_sub.render("PUBLIC DEPARTURES", True, COLOR_ACCENT_CYAN)
        self.screen.blit(brand, (32, 18))
        self.screen.blit(role, (155, 24))
        self.logout_button.draw(self.screen)
        heading = self.font_title.render("Departures", True, COLOR_TEXT_WHITE)
        sub = self.font_main.render("Scheduled takeoffs across the modeled airport network", True, COLOR_TEXT_MUTED)
        self.screen.blit(heading, (42, 112))
        self.screen.blit(sub, (42, 148))
        self.customer_table.draw(self.screen)
        footer = self.font_sub.render("Schedule information only • Controller tools and infrastructure are restricted",
                                      True, COLOR_TEXT_MUTED)
        self.screen.blit(footer, (42, WINDOW_HEIGHT - 28))

    def draw(self):
        if not self.current_user:
            self.draw_login()
            return
        if self.current_user["role_code"] == "CUSTOMER":
            self.draw_customer()
            return
        self.screen.fill(COLOR_BG)
        pygame.draw.rect(self.screen, COLOR_PANEL, (0, 0, WINDOW_WIDTH, 62))
        pygame.draw.line(self.screen, (52, 67, 84), (0, 62), (WINDOW_WIDTH, 62), 1)
        brand = self.font_title.render("AURORA", True, COLOR_TEXT_WHITE)
        sub = self.font_sub.render("AIRPORT OPERATIONS", True, COLOR_TEXT_MUTED)
        self.screen.blit(brand, (20, 9))
        self.screen.blit(sub, (20, 36))
        for btn in self.nav_buttons:
            btn.draw(self.screen)
        self.logout_button.draw(self.screen)
        if self.current_tab == "DASHBOARD":
            self.draw_dashboard()
        elif self.current_tab == "ASSIGNMENT":
            self.draw_assignment()
        elif self.current_tab == "RADAR":
            self.draw_radar()
        elif self.current_tab == "FLEET":
            self.draw_fleet()
        elif self.current_tab == "REPORTS":
            self.draw_reports()
        if self.active_modal:
            self.active_modal.draw(self.screen, self.font_hdr, self.font_main, self.font_hdr)

    def draw_dashboard(self):
        # Stat Cards
        card_w = 180
        card_gap = 16
        c1 = StatCard((20 + 0 * (card_w + card_gap), 70, card_w, 100), "Total Aircraft", self.stats.get("total_ac", 0), "Registered Fleet", COLOR_ACCENT_CYAN)
        c2 = StatCard((20 + 1 * (card_w + card_gap), 70, card_w, 100), "Active Aircraft", self.stats.get("active_ac", 0), "Operational Airframes", COLOR_SUCCESS_GREEN)
        c3 = StatCard((20 + 2 * (card_w + card_gap), 70, card_w, 100), "Airports Hubs", self.stats.get("airports", 0), "Modeled Stations", (180, 120, 255))
        c4 = StatCard((20 + 3 * (card_w + card_gap), 70, card_w, 100), "Runway Strips", self.stats.get("runways", 0), "Physical Runways", COLOR_RUNWAY_BLUE)
        c5 = StatCard((20 + 4 * (card_w + card_gap), 70, card_w, 100), "Scheduled Ops", self.stats.get("total_ops", 0), "Landing & Takeoffs", COLOR_TEXT_YELLOW)
        c6 = StatCard((20 + 5 * (card_w + card_gap), 70, card_w, 100), "Unassigned Ops", self.stats.get("unassigned_ops", 0), "Awaiting Runway Assignment", COLOR_ALERT_RED)

        for c in [c1, c2, c3, c4, c5, c6]:
            c.draw(self.screen, self.font_sub, self.font_card_val, self.font_sub)

        # Section Header
        hdr = self.font_hdr.render("UPCOMING LANDING & TAKEOFF SCHEDULE (PREDEFINED OPERATIONS)", True, COLOR_TEXT_WHITE)
        self.screen.blit(hdr, (20, 188))
        self.schedule_table.draw(self.screen)

    def draw_assignment(self):
        lbl1 = self.font_hdr.render("1. SELECT FLIGHT OPERATION TO ASSIGN", True, COLOR_TEXT_YELLOW)
        self.screen.blit(lbl1, (20, 78))
        self.assign_op_table.draw(self.screen)

        lbl2 = self.font_hdr.render("2. SELECT CANDIDATE RUNWAY DIRECTION VECTOR", True, COLOR_ACCENT_CYAN)
        self.screen.blit(lbl2, (660, 78))
        self.assign_dir_table.draw(self.screen)

        self.btn_validate.draw(self.screen)
        self.btn_confirm.draw(self.screen)
        self.btn_cancel_assignment.draw(self.screen)

        # Explanatory prompt box
        exp_rect = pygame.Rect(660, 590, 520, 150)
        pygame.draw.rect(self.screen, COLOR_PANEL, exp_rect, border_radius=6)
        pygame.draw.rect(self.screen, (40, 55, 75), exp_rect, width=1, border_radius=6)
        info_t = self.font_hdr.render("ACADEMIC DBMS VALIDATION RULES ENFORCED:", True, COLOR_ACCENT_CYAN)
        self.screen.blit(info_t, (exp_rect.x + 14, exp_rect.y + 12))
        rules = [
            "• Airport Alignment: Vector must belong to operation's station airport.",
            "• Direction Eligibility: Landing vs Takeoff permitted flags checked.",
            "• Airframe Compatibility: Aircraft type MTOW / runway length compatibility certified.",
            "• Operational Status: Physical runway must be OPEN (not CLOSED/RESTRICTED).",
            "• Restriction Window: Checks no scheduled maintenance or noise curfews overlap.",
            "• Referential Integrity: Updates are committed atomically with trigger audit logging."
        ]
        for idx, r in enumerate(rules):
            r_surf = self.font_sub.render(r, True, COLOR_TEXT_MUTED)
            self.screen.blit(r_surf, (exp_rect.x + 14, exp_rect.y + 36 + (idx * 17)))

    def draw_radar(self):
        # Airport switch buttons
        btn_dfw = Button((20, 70, 200, 28), "DFW HUB", self.font_sub,
                         on_click=lambda: self.radar_view.set_airport(1),
                         active=(self.radar_view.current_airport_id == 1))
        btn_bom = Button((230, 70, 200, 28), "BOM HUB", self.font_sub,
                         on_click=lambda: self.radar_view.set_airport(3),
                         active=(self.radar_view.current_airport_id == 3))
        btn_dfw.draw(self.screen)
        btn_bom.draw(self.screen)

        # Radar Scope
        self.radar_view.draw(self.screen, self.font_hdr, self.font_sub)

    def draw_fleet(self):
        for b in self.fleet_buttons:
            b.draw(self.screen)
        self.fleet_table.draw(self.screen)

    def draw_reports(self):
        for b in self.report_buttons:
            b.draw(self.screen)

        # Query Title & SQL
        t_surf = self.font_hdr.render(f"SQL DEMONSTRATION: {self.report_title}", True, COLOR_TEXT_YELLOW)
        self.screen.blit(t_surf, (20, 110))

        sql_box = pygame.Rect(20, 134, WINDOW_WIDTH - 40, 26)
        pygame.draw.rect(self.screen, (15, 20, 28), sql_box, border_radius=4)
        sql_surf = self.font_sub.render(f"SQL: {self.report_sql[:145]}...", True, COLOR_ACCENT_CYAN)
        self.screen.blit(sql_surf, (sql_box.x + 8, sql_box.y + 6))

        self.report_table.draw(self.screen)
