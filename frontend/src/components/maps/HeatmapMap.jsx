import L from 'leaflet';
import { useEffect, useRef } from 'react';

const DEFAULT_CENTER = [20.5937, 78.9629];

function intensityColor(value) {
  if (value >= 20) {
    return '#b91c1c';
  }
  if (value >= 10) {
    return '#b45309';
  }
  if (value >= 4) {
    return '#1f4e79';
  }
  return '#0f766e';
}

function popupContent(point) {
  return `
    <strong>${point.camera_name}</strong><br>
    ${point.location_name}<br>
    ${point.intensity} violations<br>
    Severity: ${point.severity_score || 0}<br>
    Safety Index: ${point.safety_index ?? 100}/100
  `;
}

export default function HeatmapMap({ points = [] }) {
  const mapRef = useRef(null);
  const elementRef = useRef(null);

  useEffect(() => {
    if (!elementRef.current || mapRef.current) {
      return;
    }

    mapRef.current = L.map(elementRef.current, {
      zoomControl: true,
      attributionControl: true,
    }).setView(DEFAULT_CENTER, 5);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(mapRef.current);
  }, []);

  useEffect(() => {
    if (!mapRef.current) {
      return undefined;
    }

    const layer = L.layerGroup().addTo(mapRef.current);
    const bounds = [];

    points.forEach((point) => {
      if (typeof point.latitude !== 'number' || typeof point.longitude !== 'number') {
        return;
      }

      const latLng = [point.latitude, point.longitude];
      bounds.push(latLng);
      L.circleMarker(latLng, {
        radius: Math.min(28, 8 + point.intensity * 1.4),
        color: intensityColor(point.intensity),
        fillColor: intensityColor(point.intensity),
        fillOpacity: 0.35,
        weight: 2,
      })
        .bindPopup(popupContent(point))
        .addTo(layer);
    });

    if (bounds.length > 0) {
      mapRef.current.fitBounds(bounds, { padding: [36, 36], maxZoom: 14 });
    }

    return () => {
      layer.remove();
    };
  }, [points]);

  return <div ref={elementRef} className="h-[420px] min-h-[360px] w-full" aria-label="Violation heatmap" />;
}

