"use client";

import Image from "next/image";
import { useCallback, useMemo, useState } from "react";
import { GoogleMap, Marker, InfoWindow, useJsApiLoader } from "@react-google-maps/api";

type Props = {
  lat: number;
  lng: number;
  zoom?: number;
  onPick?: (lat: number, lng: number, address?: string, error?: string) => void;
};

const containerStyle = {
  width: "100%",
  height: "100%",
};

const cleanMapStyle: google.maps.MapTypeStyle[] = [
  { featureType: "poi", stylers: [{ visibility: "off" }] },
  { featureType: "transit", stylers: [{ visibility: "off" }] },
];

const BOSTON_BBOX = {
  latMin: 42.2279,
  latMax: 42.3995,
  lngMin: -71.1912,
  lngMax: -70.986,
};

function inBostonBBox(lat: number, lng: number) {
  return (
    lat >= BOSTON_BBOX.latMin &&
    lat <= BOSTON_BBOX.latMax &&
    lng >= BOSTON_BBOX.lngMin &&
    lng <= BOSTON_BBOX.lngMax
  );
}

function streetViewStaticUrl(lat: number, lng: number) {
  const key = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
  const size = "640x360";
  const fov = 80;
  const pitch = 0;

  return (
    `https://maps.googleapis.com/maps/api/streetview` +
    `?size=${size}` +
    `&location=${lat},${lng}` +
    `&fov=${fov}` +
    `&pitch=${pitch}` +
    `&key=${encodeURIComponent(String(key || ""))}`
  );
}

export default function MapView({ lat, lng, zoom = 15, onPick }: Props) {
  const center = useMemo(() => ({ lat, lng }), [lat, lng]);

  const { isLoaded, loadError } = useJsApiLoader({
    id: "script-loader",
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY as string,
    libraries: ["places"],
    language: "en",
    region: "US",
  });

  const [infoOpen, setInfoOpen] = useState(false);
  const [infoPos, setInfoPos] = useState<{ lat: number; lng: number } | null>(null);
  const [svOk, setSvOk] = useState<boolean | null>(null);
  const [svUrl, setSvUrl] = useState<string>("");

  const checkStreetView = useCallback((lat: number, lng: number) => {
    if (!window.google?.maps) return;

    setSvOk(null);
    setSvUrl("");

    const sv = new google.maps.StreetViewService();
    sv.getPanorama({ location: { lat, lng }, radius: 60 }, (data, status) => {
      if (status === "OK" && data?.location?.latLng) {
        setSvOk(true);
        setSvUrl(streetViewStaticUrl(lat, lng));
      } else {
        setSvOk(false);
        setSvUrl("");
      }
    });
  }, []);

  const handleClick = useCallback(
    (e: google.maps.MapMouseEvent) => {
      if (!e.latLng) return;

      const newLat = e.latLng.lat();
      const newLng = e.latLng.lng();

      if (!inBostonBBox(newLat, newLng)) {
        onPick?.(newLat, newLng, undefined, "目前只支持Boston地区");
        return;
      }

      onPick?.(newLat, newLng);

      setInfoPos({ lat: newLat, lng: newLng });
      setInfoOpen(true);
      checkStreetView(newLat, newLng);
    },
    [onPick, checkStreetView],
  );

  if (loadError) return <div>Map failed to load</div>;
  if (!isLoaded) return <div />;

  return (
    <GoogleMap
      mapContainerStyle={containerStyle}
      center={center}
      zoom={zoom}
      onClick={handleClick}
      options={{
        clickableIcons: false,
        streetViewControl: false,
        mapTypeControl: false,
        fullscreenControl: false,
        styles: cleanMapStyle,
        restriction: {
          latLngBounds: {
            north: BOSTON_BBOX.latMax,
            south: BOSTON_BBOX.latMin,
            east: BOSTON_BBOX.lngMax,
            west: BOSTON_BBOX.lngMin,
          },
          strictBounds: true,
        },
      }}
    >
      <Marker position={center} />

      {infoOpen && infoPos && (
        <InfoWindow
          position={infoPos}
          onCloseClick={() => setInfoOpen(false)}
          options={{ pixelOffset: new google.maps.Size(0, -8) }}
        >
          <div style={{ width: 320 }}>
            <div style={{ fontWeight: 800, marginBottom: 6, color: "#111827" }}>
              Street View
            </div>

            {svOk === null && (
              <div style={{ fontSize: 13, color: "#6b7280" }}>Loading photo…</div>
            )}

            {svOk === false && (
              <div style={{ fontSize: 13, color: "#6b7280" }}>
                No Street View photo at this spot.
              </div>
            )}

            {svOk === true && svUrl && (
              <div
                style={{
                  borderRadius: 10,
                  border: "1px solid #e5e7eb",
                  overflow: "hidden",
                }}
              >
                <Image
                  src={svUrl}
                  alt="Street View"
                  width={640}
                  height={360}
                  style={{ width: "100%", height: "auto", display: "block" }}
                  unoptimized
                  priority={false}
                />
              </div>
            )}

            <div style={{ marginTop: 8, fontSize: 12, color: "#6b7280" }}>
              {infoPos.lat.toFixed(5)}, {infoPos.lng.toFixed(5)}
            </div>
          </div>
        </InfoWindow>
      )}
    </GoogleMap>
  );
}
