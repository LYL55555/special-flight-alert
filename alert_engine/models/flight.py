from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from FlightRadar24.entities.flight import Flight as SdkFlight


def _norm_reg(reg: Optional[str]) -> Optional[str]:
    if not reg or reg == "N/A":
        return None
    r = reg.strip().upper().replace("-", "").replace(" ", "")
    return r or None


@dataclass
class Flight:
    flight_number: str | None
    registration: str | None
    aircraft_type: str | None
    operator: str | None
    origin: str | None
    destination: str | None
    scheduled_arrival: datetime | None
    estimated_arrival: datetime | None
    scheduled_departure: datetime | None = None
    estimated_departure: datetime | None = None
    latitude: float | None = None
    longitude: float | None = None
    altitude: float | None = None
    speed: float | None = None
    fr24_id: str | None = None
    callsign: str | None = None
    airline_icao: str | None = None
    on_ground: bool | None = None
    monitored_airport: str | None = None
    movement: str | None = None
    origin_timezone_name: str | None = None
    destination_timezone_name: str | None = None
    origin_timezone_offset: int | None = None
    destination_timezone_offset: int | None = None
    monitored_timezone_name: str | None = None
    schedule_row_id: str | None = None
    source: str = "live"

    def spot_time_for_sort(self) -> datetime | None:
        """
        Chronological sort key: departure rows use dep time, arrival rows use arr time
        (estimated over scheduled when both exist).
        """
        mv = (self.movement or "").lower()
        if mv == "arrival":
            return self.estimated_arrival or self.scheduled_arrival
        if mv == "departure":
            return self.estimated_departure or self.scheduled_departure
        if mv == "both":
            return (
                self.estimated_departure
                or self.scheduled_departure
                or self.estimated_arrival
                or self.scheduled_arrival
            )
        return (
            self.estimated_departure
            or self.scheduled_departure
            or self.estimated_arrival
            or self.scheduled_arrival
        )

    def spot_time_local_display(self) -> str:
        """Local wall time for the same instant as spot_time_for_sort (dep → origin TZ, arr → dest TZ)."""
        from utils.time_local import format_local

        st = self.spot_time_for_sort()
        if st is None:
            return ""

        def norm(dt: datetime) -> datetime:
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

        mv = (self.movement or "").lower()
        if mv == "arrival":
            return format_local(
                st,
                self.destination_timezone_name,
                self.destination_timezone_offset,
            )
        if mv == "departure":
            return format_local(
                st,
                self.origin_timezone_name,
                self.origin_timezone_offset,
            )
        if mv == "both":
            cand_dep = self.estimated_departure or self.scheduled_departure
            if cand_dep is not None:
                if norm(st).timestamp() == norm(cand_dep).timestamp():
                    return format_local(
                        st,
                        self.origin_timezone_name,
                        self.origin_timezone_offset,
                    )
            return format_local(
                st,
                self.destination_timezone_name,
                self.destination_timezone_offset,
            )
        cand_dep = self.estimated_departure or self.scheduled_departure
        if cand_dep is not None and norm(st).timestamp() == norm(cand_dep).timestamp():
            return format_local(
                st,
                self.origin_timezone_name,
                self.origin_timezone_offset,
            )
        return format_local(
            st,
            self.destination_timezone_name,
            self.destination_timezone_offset,
        )

    def leg_signature(self) -> str:
        """Stable leg id: same aircraft can have separate arrival vs departure rows."""

        def ts(d: datetime | None) -> str:
            if d is None:
                return ""
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            return str(int(d.timestamp()))

        return "|".join(
            [
                self.source,
                self.movement or "",
                self.flight_number or "",
                self.registration or "",
                self.origin or "",
                self.destination or "",
                ts(self.scheduled_departure),
                ts(self.scheduled_arrival),
                self.schedule_row_id or "",
                self.fr24_id or "",
            ]
        )

    def row_local_times(self) -> dict[str, str]:
        from utils.time_local import format_local

        return {
            "scheduled_departure_local": format_local(
                self.scheduled_departure,
                self.origin_timezone_name,
                self.origin_timezone_offset,
            ),
            "estimated_departure_local": format_local(
                self.estimated_departure,
                self.origin_timezone_name,
                self.origin_timezone_offset,
            ),
            "scheduled_arrival_local": format_local(
                self.scheduled_arrival,
                self.destination_timezone_name,
                self.destination_timezone_offset,
            ),
            "estimated_arrival_local": format_local(
                self.estimated_arrival,
                self.destination_timezone_name,
                self.destination_timezone_offset,
            ),
            "departure_tz_label": self.origin_timezone_name or "",
            "arrival_tz_label": self.destination_timezone_name or "",
        }

    @classmethod
    def from_sdk_flight(cls, sdk: "SdkFlight") -> Flight:
        num = getattr(sdk, "number", None)
        if num == "N/A":
            num = None
        reg = _norm_reg(getattr(sdk, "registration", None))
        ac = getattr(sdk, "aircraft_code", None)
        if ac == "N/A":
            ac = None
        op = getattr(sdk, "airline_icao", None)
        if op == "N/A":
            op = None
        orig = getattr(sdk, "origin_airport_iata", None)
        if orig == "N/A":
            orig = None
        dest = getattr(sdk, "destination_airport_iata", None)
        if dest == "N/A":
            dest = None
        lat = getattr(sdk, "latitude", None)
        lon = getattr(sdk, "longitude", None)
        if lat == "N/A" or lat is None:
            lat_f: float | None = None
        else:
            lat_f = float(lat)
        if lon == "N/A" or lon is None:
            lon_f = None
        else:
            lon_f = float(lon)
        alt = getattr(sdk, "altitude", None)
        if alt == "N/A" or alt is None:
            alt_f = None
        else:
            alt_f = float(alt)
        spd = getattr(sdk, "ground_speed", None)
        if spd == "N/A" or spd is None:
            spd_f = None
        else:
            spd_f = float(spd)
        og = getattr(sdk, "on_ground", None)
        on_g: bool | None
        if og == "N/A" or og is None:
            on_g = None
        else:
            on_g = bool(int(og)) if str(og).isdigit() else bool(og)
        cs = getattr(sdk, "callsign", None)
        if cs == "N/A":
            cs = None
        sched = getattr(sdk, "scheduled_arrival", None)
        est = getattr(sdk, "estimated_arrival", None)
        return cls(
            flight_number=num,
            registration=reg,
            aircraft_type=ac.upper() if isinstance(ac, str) else ac,
            operator=op,
            origin=orig,
            destination=dest,
            scheduled_arrival=sched if isinstance(sched, datetime) else None,
            estimated_arrival=est if isinstance(est, datetime) else None,
            latitude=lat_f,
            longitude=lon_f,
            altitude=alt_f,
            speed=spd_f,
            fr24_id=getattr(sdk, "id", None),
            callsign=cs,
            airline_icao=op,
            on_ground=on_g,
        )

    def apply_time_block(self, td: dict) -> None:
        if isinstance(td, dict):
            self._parse_fr24_time_block(td)

    def enrich_from_details(self, sdk: "SdkFlight") -> None:
        """After set_flight_details: times, airline name, timezones, flight number."""
        name = getattr(sdk, "airline_name", None)
        if name and name != "N/A":
            self.operator = str(name).strip()
        num = getattr(sdk, "number", None)
        if num and num != "N/A" and not self.flight_number:
            s = str(num).strip()
            if s and s != "ZZ0000":
                self.flight_number = s
        self._sync_timezones_from_sdk(sdk)
        td = getattr(sdk, "time_details", None)
        if isinstance(td, dict):
            self._parse_fr24_time_block(td)
            if "scheduled" not in td:
                self._ingest_time_tree(td)

    def _sync_timezones_from_sdk(self, sdk: "SdkFlight") -> None:
        pairs = [
            ("origin_timezone_name", "origin_airport_timezone_name"),
            ("destination_timezone_name", "destination_airport_timezone_name"),
            ("origin_timezone_offset", "origin_airport_timezone_offset"),
            ("destination_timezone_offset", "destination_airport_timezone_offset"),
        ]
        for dst, src in pairs:
            v = getattr(sdk, src, None)
            if v is None or v == "N/A":
                continue
            if dst.endswith("_offset"):
                try:
                    v = int(v)
                except (TypeError, ValueError):
                    continue
            setattr(self, dst, v)
        if self.source == "live" and self.monitored_airport:
            if self.movement == "arrival":
                self.monitored_timezone_name = self.destination_timezone_name
            elif self.movement == "departure":
                self.monitored_timezone_name = self.origin_timezone_name

    @staticmethod
    def _utc_from_unix(ts: Any) -> datetime | None:
        if not isinstance(ts, int) or ts < 1_000_000_000:
            return None
        if ts > 1_000_000_000_000:
            ts //= 1000
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except (ValueError, OSError):
            return None

    def _parse_fr24_time_block(self, td: dict) -> None:
        sch = td.get("scheduled") if isinstance(td.get("scheduled"), dict) else {}
        est = td.get("estimated") if isinstance(td.get("estimated"), dict) else {}
        real = td.get("real") if isinstance(td.get("real"), dict) else {}
        other = td.get("other") if isinstance(td.get("other"), dict) else {}

        self.scheduled_departure = self.scheduled_departure or self._utc_from_unix(
            sch.get("departure")
        )
        self.scheduled_arrival = self.scheduled_arrival or self._utc_from_unix(
            sch.get("arrival")
        )
        self.estimated_departure = self.estimated_departure or self._utc_from_unix(
            est.get("departure")
        ) or self._utc_from_unix(real.get("departure"))
        self.estimated_arrival = self.estimated_arrival or self._utc_from_unix(
            est.get("arrival")
        ) or self._utc_from_unix(real.get("arrival")) or self._utc_from_unix(
            other.get("eta")
        )

    def _ingest_time_tree(self, obj: Any, path: tuple[str, ...] = ()) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                self._ingest_time_tree(v, path + (str(k).lower(),))
            return
        if isinstance(obj, (int, float)):
            ts = int(obj)
            if ts > 1_000_000_000_000:
                ts //= 1000
            if ts < 1_000_000_000:
                return
            try:
                dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            except (ValueError, OSError):
                return
            self._assign_time_from_path(dt, path)
        elif isinstance(obj, str) and obj.isdigit() and len(obj) >= 10:
            self._ingest_time_tree(int(obj), path)

    def _assign_time_from_path(self, dt: datetime, path: tuple[str, ...]) -> None:
        joined = " ".join(path)
        is_est = any(
            x in joined
            for x in ("estimated", "eta", "predicted", "prognosed", "actual")
        )
        depish = any(
            x in joined
            for x in (
                "departure",
                "dep",
                "out",
                "takeoff",
                "off",
                "std",
                "etd",
            )
        )
        arrish = any(
            x in joined
            for x in (
                "arrival",
                "arr",
                "landing",
                "sta",
            )
        )
        if depish and not arrish:
            if is_est:
                self.estimated_departure = self.estimated_departure or dt
            else:
                self.scheduled_departure = self.scheduled_departure or dt
        elif arrish and not depish:
            if is_est:
                self.estimated_arrival = self.estimated_arrival or dt
            else:
                self.scheduled_arrival = self.scheduled_arrival or dt
        elif "departure" in joined or path[-1:] == ("departure",):
            if is_est:
                self.estimated_departure = self.estimated_departure or dt
            else:
                self.scheduled_departure = self.scheduled_departure or dt
        elif "arrival" in joined or path[-1:] == ("arrival",):
            if is_est:
                self.estimated_arrival = self.estimated_arrival or dt
            else:
                self.scheduled_arrival = self.scheduled_arrival or dt
