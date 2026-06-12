"use client";

import { motion } from "motion/react";
import { Accessibility, Camera, CarFront, Cctv, Zap } from "lucide-react";

import type { ParkingSlot } from "@/lib/parking-data";
import { movingCars, zones } from "@/lib/parking-data";
import { cn } from "@/lib/utils";

type ParkingLotProps = {
  slots: ParkingSlot[];
  routeMode: "empty" | "mine" | null;
  target: string | null;
  showGraph: boolean;
};

const statusClass = {
  free: "border-emerald-300/30 bg-emerald-400 text-emerald-950",
  occupied: "border-rose-300/30 bg-rose-500 text-white",
  reserved: "border-sky-300/30 bg-sky-500 text-white",
  mine: "border-amber-200 bg-amber-300 text-amber-950 shadow-[0_0_22px_#fbbf2470]",
};

function Slot({ slot, target }: { slot: ParkingSlot; target: string | null }) {
  return (
    <motion.div
      layout
      title={`${slot.id} • ${slot.status}`}
      className={cn(
        "relative flex h-7 min-w-0 items-center justify-center rounded-[5px] border px-0.5 text-[7px] font-extrabold tracking-tight transition-all sm:h-8 sm:text-[8px]",
        statusClass[slot.status],
        target === slot.id && "ring-2 ring-white ring-offset-2 ring-offset-slate-900",
      )}
      animate={target === slot.id ? { scale: [1, 1.08, 1] } : { scale: 1 }}
      transition={{ repeat: target === slot.id ? Infinity : 0, duration: 1.2 }}
    >
      {slot.accessible && <Accessibility className="absolute left-0.5 top-0.5 size-2" />}
      {slot.electric && <Zap className="absolute right-0.5 top-0.5 size-2" />}
      {slot.id.replace("-", "")}
    </motion.div>
  );
}

function Lane({ zone, slots, target }: { zone: string; slots: ParkingSlot[]; target: string | null }) {
  const north = slots.slice(0, 10);
  const south = slots.slice(10);

  return (
    <div className="relative grid grid-cols-[38px_1fr] gap-2">
      <div className="flex items-center justify-center">
        <span className="rounded-lg border border-white/10 bg-white/5 px-2 py-3 text-xs font-black text-slate-400">
          {zone}
        </span>
      </div>
      <div className="space-y-1.5">
        <div className="grid grid-cols-10 gap-1">
          {north.map((slot) => <Slot key={slot.id} slot={slot} target={target} />)}
        </div>
        <div className="relative h-7 overflow-hidden rounded-md border border-white/5 bg-slate-700/70 sm:h-8">
          <div className="absolute inset-x-2 top-1/2 border-t border-dashed border-slate-400/40" />
          <div className="absolute inset-0 flex items-center justify-around text-[9px] text-slate-400/50">
            {Array.from({ length: 6 }, (_, index) => <span key={index}>›</span>)}
          </div>
        </div>
        <div className="grid grid-cols-10 gap-1">
          {south.map((slot) => <Slot key={slot.id} slot={slot} target={target} />)}
        </div>
      </div>
    </div>
  );
}

export function ParkingLot({ slots, routeMode, target, showGraph }: ParkingLotProps) {
  return (
    <div className="relative min-h-[650px] overflow-hidden rounded-2xl border border-white/10 bg-[#202b38] p-3 shadow-2xl shadow-black/30 sm:p-5">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(56,189,248,.08),transparent_35%)]" />

      <div className="relative z-10 mb-4 flex items-center justify-between">
        <div>
          <p className="text-[10px] font-bold tracking-[0.22em] text-cyan-400">LIVE FLOOR MAP</p>
          <h2 className="mt-1 text-base font-bold text-white sm:text-lg">Tầng B1 • 100 vị trí</h2>
        </div>
        <div className="flex items-center gap-2 text-[10px] text-slate-400">
          <span className="size-2 animate-pulse rounded-full bg-emerald-400" />
          Cập nhật trực tiếp
        </div>
      </div>

      <div className="relative z-10 space-y-3 rounded-xl border border-white/5 bg-black/10 p-2 sm:p-3">
        {zones.map((zone) => (
          <Lane
            key={zone}
            zone={zone}
            slots={slots.filter((slot) => slot.zone === zone)}
            target={target}
          />
        ))}

        {showGraph && (
          <svg className="pointer-events-none absolute inset-0 size-full opacity-50">
            <defs>
              <pattern id="graph" width="52" height="45" patternUnits="userSpaceOnUse">
                <path d="M 0 22.5 H 52 M 26 0 V 45" fill="none" stroke="#22d3ee" strokeWidth="0.7" />
                <circle cx="26" cy="22.5" r="2" fill="#22d3ee" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#graph)" />
          </svg>
        )}

        {routeMode && (
          <svg className="pointer-events-none absolute inset-0 size-full">
            <motion.path
              d={routeMode === "mine"
                ? "M 36 18 L 58 18 L 58 320 L 70 320 L 70 430"
                : "M 8 615 L 8 535 L 42 535 L 42 438 L 72 438"}
              fill="none"
              stroke={routeMode === "mine" ? "#fbbf24" : "#38bdf8"}
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="5"
              strokeDasharray="10 8"
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: 1, opacity: 1, strokeDashoffset: [0, -36] }}
              transition={{ pathLength: { duration: 0.9 }, strokeDashoffset: { repeat: Infinity, duration: 1.4, ease: "linear" } }}
              vectorEffect="non-scaling-stroke"
            />
          </svg>
        )}
      </div>

      <div className="absolute bottom-4 left-5 z-20 flex items-center gap-2 rounded-lg border border-white/10 bg-slate-950/80 px-3 py-2 text-[10px] text-slate-300 backdrop-blur">
        <Camera className="size-3.5 text-cyan-400" /> ANPR CỔNG VÀO
      </div>
      <div className="absolute bottom-4 right-5 z-20 flex items-center gap-2 rounded-lg border border-white/10 bg-slate-950/80 px-3 py-2 text-[10px] text-slate-300 backdrop-blur">
        LỐI RA <Cctv className="size-3.5 text-cyan-400" />
      </div>

      {movingCars.map((car) => (
        <motion.div
          key={car.id}
          className="pointer-events-none absolute z-30"
          style={{ top: `${23 + car.lane * 14.3}%` }}
          initial={{ left: "31%" }}
          animate={{ left: ["31%", "91%", "31%"] }}
          transition={{ repeat: Infinity, duration: car.duration, delay: car.delay, ease: "linear" }}
        >
          <div className="rounded-md border border-white/30 p-1 shadow-lg" style={{ background: car.color }}>
            <CarFront className="size-3.5 text-slate-950" />
          </div>
        </motion.div>
      ))}
    </div>
  );
}

