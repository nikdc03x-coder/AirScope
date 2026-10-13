
/**
 * AirScope | nik
 * Data freshness indicator for Berlin and London.
 *
 * Reads timestamps from the existing historical APIs.
 * Shows the age of the latest stored observation.
 * Never describes archived observations as live.
 */

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import {
  Alert,
  Box,
  Card,
  CardContent,
  CircularProgress,
  Stack,
  Typography,
} from "@mui/material";

type City = "berlin" | "london";

type Props = {
  city: City;
  stationId: string;
};

type HistoryResponse = {
  city: string;
  station_id: string;
  station_name: string;
  source: string;
  window_end_utc: string;
  available_measurements: number;
  is_live: boolean;
  observations: {
    timestamp_utc: string;
    pm25_ugm3: number | null;
  }[];
};

const API_BASE = "http://127.0.0.1:8000/api/v1";

function formatTimestamp(
  value: string,
  german: boolean
) {
  return (
    new Intl.DateTimeFormat(
      german ? "de-DE" : "en-GB",
      {
        dateStyle: "medium",
        timeStyle: "short",
        timeZone: "UTC",
      }
    ).format(new Date(value)) + " UTC"
  );
}

function formatAge(
  timestamp: string,
  german: boolean
) {
  const elapsedMs = Date.now() - new Date(timestamp).getTime();

  if (!Number.isFinite(elapsedMs)) {
    return "—";
  }

  if (elapsedMs < 0) {
    return german
      ? "Zeitstempel liegt in der Zukunft"
      : "Timestamp is in the future";
  }

  const hours = Math.floor(elapsedMs / 3_600_000);
  const days = Math.floor(hours / 24);

  if (hours < 1) {
    return german
      ? "Weniger als eine Stunde"
      : "Less than one hour";
  }

  if (hours < 24) {
    return german
      ? `${hours} Stunden`
      : `${hours} hours`;
  }

  if (days < 30) {
    return german
      ? `${days} Tage`
      : `${days} days`;
  }

  return german
    ? `${Math.floor(days / 30)} Monate (ungefähr)`
    : `${Math.floor(days / 30)} months (approx.)`;
}

export default function DataFreshnessPanel({
  city,
  stationId,
}: Props) {
  const { i18n } = useTranslation();
  const german = i18n.language.startsWith("de");

  const [history, setHistory] =
    useState<HistoryResponse | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const labels = german
    ? {
        title: "Aktualität der Messdaten",
        station: "Messstation",
        latest: "Letzter verfügbarer Messwert",
        age: "Alter des Messwerts",
        source: "Quelle",
        loading: "Zeitstempel wird geladen...",
        error: "Zeitstempel konnte nicht geladen werden.",
        notice:
          "Dies ist ein gespeicherter Messwert und keine aktuelle Live-Messung.",
        noReading: "Kein gültiger Messwert verfügbar",
        historical: "Historische Daten · Nicht live",
      }
    : {
        title: "Data Freshness",
        station: "Monitoring station",
        latest: "Latest available observation",
        age: "Age of observation",
        source: "Source",
        loading: "Loading observation timestamp...",
        error: "Unable to load observation timestamp.",
        notice:
          "This is a stored observation, not a current live measurement.",
        noReading: "No valid measurement available",
        historical: "Historical data · Not live",
      };

  // Fetch the latest available stored hourly observations.
  useEffect(() => {
    const controller = new AbortController();

    async function loadHistory() {
      setLoading(true);
      setHistory(null);
      setError("");

      try {
        const endpoint =
          `${API_BASE}/observations/${city}/` +
          `${encodeURIComponent(stationId)}?days=7`;

        const response = await fetch(endpoint, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data: HistoryResponse =
          await response.json();

        if (
          data.station_id !== stationId ||
          !Array.isArray(data.observations) ||
          data.is_live !== false
        ) {
          throw new Error("Invalid observation response");
        }

        setHistory(data);
      } catch (err) {
        if (controller.signal.aborted) return;

        setError(
          err instanceof Error ? err.message : "Unknown error"
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void loadHistory();

    return () => controller.abort();
  }, [city, stationId]);

  // Use the last genuine non-null observation.
  // The latest stored hourly slot may have no measurement.
  const latestReading = history?.observations
    .filter(
      (item) =>
        item.pm25_ugm3 !== null &&
        Number.isFinite(item.pm25_ugm3)
    )
    .at(-1);

  return (
    <Card variant="outlined">
      <CardContent>
        <Stack spacing={2}>
          <Typography
            variant="h6"
            sx={{ fontWeight: 700 }}
          >
            {labels.title}
          </Typography>

          {loading && (
            <Stack
              direction="row"
              spacing={2}
              sx={{ alignItems: "center" }}
            >
              <CircularProgress size={22} />

              <Typography>
                {labels.loading}
              </Typography>
            </Stack>
          )}

          {error && (
            <Alert severity="error">
              {labels.error} ({error})
            </Alert>
          )}

          {history && (
            <>
              <Typography
                variant="body2"
                color="text.secondary"
              >
                {labels.historical}
              </Typography>

              <Box
                sx={{
                  display: "grid",
                  gridTemplateColumns: {
                    xs: "1fr",
                    sm: "repeat(2, minmax(0, 1fr))",
                  },
                  gap: 2,
                }}
              >
                <Box>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                  >
                    {labels.station}
                  </Typography>

                  <Typography sx={{ fontWeight: 600 }}>
                    {history.station_name}
                  </Typography>
                </Box>

                <Box>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                  >
                    {labels.source}
                  </Typography>

                  <Typography sx={{ fontWeight: 600 }}>
                    {history.source}
                  </Typography>
                </Box>

                <Box>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                  >
                    {labels.latest}
                  </Typography>

                  <Typography sx={{ fontWeight: 600 }}>
                    {latestReading
                      ? formatTimestamp(
                          latestReading.timestamp_utc,
                          german
                        )
                      : labels.noReading}
                  </Typography>
                </Box>

                <Box>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                  >
                    {labels.age}
                  </Typography>

                  <Typography sx={{ fontWeight: 600 }}>
                    {latestReading
                      ? formatAge(
                          latestReading.timestamp_utc,
                          german
                        )
                      : "—"}
                  </Typography>
                </Box>
              </Box>

              <Alert severity="info">
                {labels.notice}
              </Alert>
            </>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}
