"use client";
import dynamic from 'next/dynamic';

const Map = dynamic (() => import("../components/Map/Map"), {
  ssr: false,
  loading: () => (
    <div style={{
      height: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "#111318",
      color: "#64748b",
    }}>
      Loading map...
    </div>
  ),
});



export default function Home() {
  return <Map/>;
}
