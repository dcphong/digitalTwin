"use client";

import { motion } from "motion/react";
import {
  Accessibility,
  Camera,
  Cctv,
  DoorOpen,
  RadioTower,
  Zap,
} from "lucide-react";

import type { ParkingSlot } from "@/lib/parking-data";
import { cn } from "@/lib/utils";

type ParkingLotProps = {
  slots: ParkingSlot[];
  routeMode: "empty" | "mine" | null;
  target: string | null;
  showGraph: boolean;
};

const WIDTH = 1210;
const HEIGHT = 860;
const laneY = [115, 265, 415, 565, 715];
const slotX = Array.from({ length: 10 }, (_, index) => 205 + index * 91);

const statusClass = {
  free: "border-emerald-200/30 bg-emerald-400 text-emerald-950",
  occupied: "border-rose-200/30 bg-rose-500 text-white",
  reserved: "border-sky-200/30 bg-sky-500 text-white",
  mine: "border-amber-100 bg-amber-300 text-amber-950 shadow-[0_0_26px_#fbbf2475]",
};

const carRoutes = [
  { color: "#3a9aff", duration: 16, delay: 0, x: [22, 67, 67, 720, 720], y: [832, 832, 115, 115, 70] },
  { color: "#ff7658", duration: 19, delay: 3, x: [22, 67, 67, 994, 994], y: [832, 832, 265, 265, 220] },
  { color: "#a979ff", duration: 18, delay: 7, x: [1128, 1128, 810, 810, 1188], y: [415, 832, 832, 832, 832] },
  { color: "#2ac97e", duration: 21, delay: 2, x: [22, 67, 67, 538, 538], y: [832, 832, 565, 565, 610] },
  { color: "#ffc43d", duration: 20, delay: 10, x: [1128, 1128, 356, 356, 1188], y: [715, 832, 832, 832, 832] },
  { color: "#f25380", duration: 23, delay: 5, x: [22, 67, 67, 902, 902], y: [832, 832, 415, 415, 370] },
];

function slotPosition(index: number) {
  const lane = Math.floor(index / 20);
  const withinLane = index % 20;
  const column = withinLane % 10;
  const north = withinLane < 10;
  return {
    left: slotX[column],
    top: laneY[lane] + (north ? -49 : 49),
  };
}

function ParkingSpace({
  slot,
  index,
  target,
}: {
  slot: ParkingSlot;
  index: number;
  target: string | null;
}) {
  const position = slotPosition(index);
  const active = target === slot.id;
  return (
    <motion.div
      layout
      title={`${slot.id} • ${slot.status}`}
      className={cn(
        "absolute z-20 flex h-9 w-[72px] -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-md border text-[9px] font-extrabold shadow-[0_3px_0_#10171f] transition-colors",
        statusClass[slot.status],
        active && "ring-2 ring-white ring-offset-2 ring-offset-[#27313d]",
      )}
      style={{
        left: `${(position.left / WIDTH) * 100}%`,
        top: `${(position.top / HEIGHT) * 100}%`,
      }}
      animate={active ? { scale: [1, 1.1, 1] } : { scale: 1 }}
      transition={{ repeat: active ? Infinity : 0, duration: 1.1 }}
    >
      {slot.accessible && <Accessibility className="absolute left-1 top-1 size-2.5" />}
      {slot.electric && <Zap className="absolute right-1 top-1 size-2.5" />}
      {slot.id}
    </motion.div>
  );
}

function Barrier({
  side,
  open,
}: {
  side: "entry" | "exit";
  open: boolean;
}) {
  const left = side === "entry" ? 2.8 : 92.3;
  return (
    <div className="absolute z-30" style={{ left: `${left}%`, top: "92%" }}>
      <div className="relative">
        <div className="h-7 w-4 rounded bg-orange-400 shadow-lg" />
        <motion.div
          className="absolute left-2 top-1 h-1.5 w-12 origin-left rounded-full bg-white"
          animate={{ rotate: open ? -42 : 0 }}
        />
        <span className="absolute left-1/2 top-8 w-20 -translate-x-1/2 text-center text-[8px] font-bold text-slate-200">
          {side === "entry" ? "CỔNG VÀO" : "LỐI RA"}
        </span>
      </div>
    </div>
  );
}

export function ParkingLot({ slots, routeMode, target, showGraph }: ParkingLotProps) {
  const targetIndex = slots.findIndex((slot) => slot.id === target);
  const targetPosition = targetIndex >= 0 ? slotPosition(targetIndex) : { left: 356, top: 764 };
  const targetLane = targetIndex >= 0 ? laneY[Math.floor(targetIndex / 20)] : 715;
  const route =
    routeMode === "mine"
      ? `M 24 24 L 67 24 L 67 ${targetLane} L ${targetPosition.left} ${targetLane} L ${targetPosition.left} ${targetPosition.top}`
      : `M 22 832 L 67 832 L 67 ${targetLane} L ${targetPosition.left} ${targetLane} L ${targetPosition.left} ${targetPosition.top}`;

  return (
    <div className="overflow-hidden rounded-2xl border border-white/10 bg-[#27313d] shadow-2xl shadow-black/30">
      <div className="flex items-center justify-between border-b border-white/10 bg-[#121c2a] px-5 py-3">
        <div>
          <p className="text-[10px] font-extrabold tracking-[0.2em] text-cyan-400">
            SƠ ĐỒ VẬN HÀNH
          </p>
          <h2 className="mt-1 text-base font-bold text-white">100 vị trí đỗ xe • 5 khu A-E</h2>
        </div>
        <div className="flex items-center gap-2 text-[10px] text-slate-400">
          <span className="size-2 animate-pulse rounded-full bg-emerald-400" />
          CẬP NHẬT THỜI GIAN THỰC
        </div>
      </div>

      <div className="relative aspect-[1210/860] min-h-[620px] w-full overflow-hidden bg-[#303b47]">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(56,189,248,.07),transparent_35%)]" />

        {laneY.map((y, index) => (
          <div key={y}>
            <div
              className="absolute left-[5.5%] right-[6.7%] h-[46px] -translate-y-1/2 bg-[#3d4855]"
              style={{ top: `${(y / HEIGHT) * 100}%` }}
            >
              <div className="absolute inset-x-3 top-1/2 border-t-2 border-dashed border-slate-400/35" />
              <div className="absolute inset-0 flex items-center justify-around text-xs text-slate-400/45">
                {Array.from({ length: 8 }, (_, arrow) => <span key={arrow}>›</span>)}
              </div>
            </div>
            <div
              className="absolute left-[7.4%] z-10 -translate-y-1/2 rounded-md border border-white/10 bg-[#1b2633] px-2 py-1 text-[9px] font-black text-slate-400"
              style={{ top: `${(y / HEIGHT) * 100}%` }}
            >
              KHU {String.fromCharCode(65 + index)}
            </div>
          </div>
        ))}

        <div className="absolute bottom-[2.2%] left-0 right-0 h-12 bg-[#3d4855]">
          <div className="absolute inset-x-8 top-1/2 border-t-2 border-dashed border-slate-400/35" />
        </div>
        <div className="absolute bottom-[2.2%] left-[5.5%] top-0 w-[46px] bg-[#3d4855]">
          <div className="absolute bottom-8 left-1/2 top-8 border-l-2 border-dashed border-slate-400/35" />
        </div>
        <div className="absolute bottom-[2.2%] right-[4.9%] top-0 w-[46px] bg-[#3d4855]">
          <div className="absolute bottom-8 left-1/2 top-8 border-l-2 border-dashed border-slate-400/35" />
        </div>

        <div className="absolute left-[0.8%] top-[1.4%] z-30 flex h-14 w-16 flex-col items-center justify-center rounded-lg border border-white/10 bg-[#1c2a39] shadow-lg">
          <DoorOpen className="size-4 text-cyan-400" />
          <span className="mt-1 text-[8px] font-bold text-slate-300">SẢNH TTTM</span>
        </div>

        {[28, 58, 84].map((left) => (
          <div key={left} className="absolute top-[1.5%] z-30" style={{ left: `${left}%` }}>
            <div className="flex items-center gap-1 rounded-md border border-white/10 bg-[#162231] px-2 py-1 text-[8px] text-slate-300">
              <Camera className="size-3 text-cyan-400" /> AI
            </div>
          </div>
        ))}
        <div className="absolute right-[8%] top-[1.6%] z-30 flex items-center gap-1 text-[9px] text-cyan-300">
          <Zap className="size-3" /> 10 TRẠM SẠC EV
        </div>

        {slots.map((slot, index) => (
          <ParkingSpace key={slot.id} slot={slot} index={index} target={target} />
        ))}

        {showGraph && (
          <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="pointer-events-none absolute inset-0 z-20 size-full opacity-55">
            <g stroke="#22d3ee" strokeWidth="1.2">
              {laneY.map((y) => <line key={y} x1="67" y1={y} x2="1128" y2={y} />)}
              <line x1="67" y1="20" x2="67" y2="832" />
              <line x1="1128" y1="20" x2="1128" y2="832" />
              {slotX.map((x) => laneY.map((y) => (
                <circle key={`${x}-${y}`} cx={x} cy={y} r="3" fill="#22d3ee" />
              )))}
            </g>
          </svg>
        )}

        {routeMode && (
          <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="pointer-events-none absolute inset-0 z-40 size-full">
            <motion.path
              d={route}
              fill="none"
              stroke="#060a0f"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="12"
            />
            <motion.path
              d={route}
              fill="none"
              stroke={routeMode === "mine" ? "#fbbf24" : "#38bdf8"}
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="5"
              strokeDasharray="12 10"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1, strokeDashoffset: [0, -44] }}
              transition={{
                pathLength: { duration: 0.9 },
                strokeDashoffset: { repeat: Infinity, duration: 1.3, ease: "linear" },
              }}
            />
          </svg>
        )}

        <Barrier side="entry" open />
        <Barrier side="exit" open={false} />

        <div className="absolute bottom-[8.5%] left-[8%] z-30 flex items-center gap-1 rounded-md border border-white/10 bg-slate-950/80 px-2 py-1 text-[8px] text-slate-300">
          <RadioTower className="size-3 text-violet-400" /> ANPR 51H-482.26
        </div>
        <div className="absolute bottom-[8.5%] right-[8%] z-30 flex items-center gap-1 rounded-md border border-white/10 bg-slate-950/80 px-2 py-1 text-[8px] text-slate-300">
          CAMERA AI <Cctv className="size-3 text-cyan-400" />
        </div>

        <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="pointer-events-none absolute inset-0 z-50 size-full">
          {carRoutes.map((car, index) => (
            <motion.g
              key={index}
              animate={{ x: car.x, y: car.y }}
              transition={{
                repeat: Infinity,
                duration: car.duration,
                delay: car.delay,
                ease: "linear",
                times: [0, 0.08, 0.22, 0.88, 1],
              }}
            >
              <rect x="-18" y="-10" width="36" height="20" rx="6" fill="#07101c" opacity=".55" />
              <rect x="-17" y="-12" width="34" height="19" rx="6" fill={car.color} stroke="#ffffff" strokeOpacity=".45" />
              <rect x="-6" y="-9" width="14" height="13" rx="3" fill="#b8dfee" />
              <rect x="-12" y="-14" width="7" height="4" rx="2" fill="#07101c" />
              <rect x="7" y="-14" width="7" height="4" rx="2" fill="#07101c" />
              <rect x="-12" y="6" width="7" height="4" rx="2" fill="#07101c" />
              <rect x="7" y="6" width="7" height="4" rx="2" fill="#07101c" />
            </motion.g>
          ))}
        </svg>

        <div className="absolute bottom-[7.5%] left-1/2 z-30 flex -translate-x-1/2 items-center gap-2 rounded-lg border border-white/10 bg-[#0c151f]/90 px-4 py-2 text-[10px] text-slate-300 shadow-lg backdrop-blur">
          <span className="size-2 animate-pulse rounded-full bg-emerald-400" />
          Cảm biến xác nhận vị trí CN-04 đã có xe
        </div>
      </div>
    </div>
  );
}
