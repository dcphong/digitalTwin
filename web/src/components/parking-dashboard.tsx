"use client";

import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { motion } from "motion/react";
import { QRCodeSVG } from "qrcode.react";
import {
  Activity, BadgeCheck, Cctv, ChevronRight, CircleParking,
  Cpu, Gauge, GitBranch, LocateFixed, Navigation, Radio, ScanLine,
  Search, ShieldCheck, Smartphone, Sparkles, Zap,
} from "lucide-react";

import { ParkingLot } from "@/components/parking-lot";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { createParkingSlots, type ParkingSlot } from "@/lib/parking-data";
import { cn } from "@/lib/utils";

type RouteMode = "empty" | "mine" | null;

const techItems = [
  { icon: ScanLine, label: "ANPR Camera", value: "51H-482.26", color: "text-violet-400" },
  { icon: Radio, label: "Cảm biến IoT", value: "99.98% online", color: "text-emerald-400" },
  { icon: Activity, label: "Độ trễ dữ liệu", value: "24 ms", color: "text-cyan-400" },
  { icon: Zap, label: "Trạm sạc EV", value: "10 vị trí", color: "text-sky-400" },
  { icon: ShieldCheck, label: "Thanh toán số", value: "Sẵn sàng", color: "text-amber-400" },
  { icon: Cctv, label: "Camera AI", value: "12 thiết bị", color: "text-orange-400" },
];

const subscribeToLocation = () => () => {};
const getLocationSnapshot = () => window.location.href;
const getLocationServerSnapshot = () => "http://localhost:3000";

export function ParkingDashboard() {
  const [slots, setSlots] = useState<ParkingSlot[]>(createParkingSlots);
  const [routeMode, setRouteMode] = useState<RouteMode>(null);
  const [target, setTarget] = useState<string | null>(null);
  const [showGraph, setShowGraph] = useState(false);
  const [events, setEvents] = useState(1284);
  const url = useSyncExternalStore(
    subscribeToLocation,
    getLocationSnapshot,
    getLocationServerSnapshot,
  );

  useEffect(() => {
    const timer = window.setInterval(() => {
      setSlots((current) => {
        const next = [...current];
        const candidates = next
          .map((slot, index) => ({ slot, index }))
          .filter(({ slot }) => slot.status !== "mine" && slot.id !== target);
        const selected = candidates[Math.floor(Math.random() * candidates.length)];
        if (!selected) return current;
        next[selected.index] = {
          ...selected.slot,
          status: selected.slot.status === "occupied" ? "free" : "occupied",
        };
        return next;
      });
      setEvents((value) => value + 1);
    }, 2400);
    return () => window.clearInterval(timer);
  }, [target]);

  const stats = useMemo(() => {
    const occupied = slots.filter((slot) => slot.status === "occupied" || slot.status === "mine").length;
    const reserved = slots.filter((slot) => slot.status === "reserved").length;
    return { occupied, reserved, free: slots.length - occupied - reserved };
  }, [slots]);

  function guideToEmpty() {
    const best = slots.find((slot) => slot.status === "free" && slot.zone === "E")
      ?? slots.find((slot) => slot.status === "free");
    setRouteMode("empty");
    setTarget(best?.id ?? null);
  }

  function guideToMine() {
    const mine = slots.find((slot) => slot.status === "mine");
    setRouteMode("mine");
    setTarget(mine?.id ?? null);
  }

  return (
    <main className="min-h-screen bg-[#07101c] text-slate-100">
      <div className="mx-auto flex min-h-screen max-w-[1920px] flex-col xl:flex-row">
        <aside className="border-b border-white/10 bg-[#0b1624]/95 p-4 backdrop-blur-xl xl:sticky xl:top-0 xl:h-screen xl:w-[390px] xl:shrink-0 xl:overflow-y-auto xl:border-b-0 xl:border-r">
          <div className="mb-5 flex items-start justify-between">
            <div>
              <p className="text-[10px] font-black tracking-[0.22em] text-cyan-400">MALL DIGITAL TWIN</p>
              <h1 className="mt-1 text-2xl font-black tracking-tight">Smart Parking B1</h1>
              <p className="mt-1 text-xs text-slate-400">Trung tâm điều hành thời gian thực</p>
            </div>
            <Badge className="border-emerald-400/20 bg-emerald-400/10 text-emerald-300">
              <span className="mr-1.5 size-1.5 animate-pulse rounded-full bg-emerald-400" /> LIVE
            </Badge>
          </div>

          <Card className="border-white/10 bg-white/[0.045] text-white">
            <CardContent className="flex gap-4 p-4">
              <div className="rounded-xl bg-white p-2">
                <QRCodeSVG value={url} size={104} bgColor="#ffffff" fgColor="#07101c" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 text-cyan-400">
                  <Smartphone className="size-4" />
                  <span className="text-[10px] font-bold tracking-wider">KHÁCH HÀNG</span>
                </div>
                <p className="mt-2 text-sm font-bold">Quét QR để tìm chỗ và tìm xe</p>
                <p className="mt-2 line-clamp-2 text-[11px] leading-relaxed text-slate-400">{url}</p>
              </div>
            </CardContent>
          </Card>

          <div className="my-4 grid grid-cols-3 gap-2">
            {[
              ["TRỐNG", stats.free, "text-emerald-400"],
              ["ĐÃ ĐỖ", stats.occupied, "text-rose-400"],
              ["ĐANG ĐI", 6, "text-sky-400"],
            ].map(([label, value, color]) => (
              <Card key={String(label)} className="border-white/10 bg-white/[0.045] text-center text-white">
                <CardContent className="p-3">
                  <p className={cn("text-2xl font-black", color)}>{value}</p>
                  <p className="mt-1 text-[9px] font-bold tracking-wider text-slate-500">{label}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="grid gap-2">
            <Button onClick={guideToEmpty} className="h-12 justify-between bg-sky-500 font-bold hover:bg-sky-400">
              <span className="flex items-center gap-2"><Search className="size-4" /> TÌM CHỖ ĐỖ TỐT NHẤT</span>
              <ChevronRight className="size-4" />
            </Button>
            <Button onClick={guideToMine} className="h-12 justify-between bg-amber-300 font-bold text-slate-950 hover:bg-amber-200">
              <span className="flex items-center gap-2"><LocateFixed className="size-4" /> DẪN ĐẾN XE CỦA TÔI</span>
              <ChevronRight className="size-4" />
            </Button>
          </div>

          <Card className="mt-4 border-white/10 bg-white/[0.045] text-white">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-xs tracking-wider text-cyan-400">
                <Navigation className="size-4" /> ĐIỀU HƯỚNG A*
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="min-h-10 text-sm leading-relaxed text-slate-300">
                {!routeMode && "Chọn chức năng để hệ thống bắt đầu dẫn đường."}
                {routeMode === "empty" && `A* đề xuất vị trí ${target}, cách cổng vào 58 m.`}
                {routeMode === "mine" && `Xe 51H-482.26 ở ${target}. Tuyến đi bộ dài 94 m.`}
              </p>
              <Separator className="my-3 bg-white/10" />
              <div className="grid grid-cols-3 gap-2">
                {[["ĐÍCH", target ?? "--"], ["QUÃNG ĐƯỜNG", routeMode ? (routeMode === "mine" ? "94 m" : "58 m") : "--"], ["NODE A*", routeMode ? "17" : "--"]].map(([label, value]) => (
                  <div key={label}>
                    <p className="text-sm font-bold">{value}</p>
                    <p className="mt-1 text-[9px] text-slate-500">{label}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="mt-4 border-white/10 bg-white/[0.045] text-white">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center justify-between text-sm">
                Công suất bãi xe <span className="text-amber-300">{stats.occupied}%</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Progress value={stats.occupied} className="h-2 bg-white/10 [&_[data-slot=progress-indicator]]:bg-amber-300" />
            </CardContent>
          </Card>

          <div className="mt-4 grid grid-cols-2 gap-2">
            {techItems.map(({ icon: Icon, label, value, color }) => (
              <div key={label} className="rounded-xl border border-white/10 bg-white/[0.035] p-3">
                <div className="flex items-center gap-2">
                  <Icon className={cn("size-4", color)} />
                  <span className="text-[10px] text-slate-500">{label}</span>
                </div>
                <p className="mt-1 text-xs font-bold">{value}</p>
              </div>
            ))}
          </div>
        </aside>

        <section className="min-w-0 flex-1 p-3 sm:p-5">
          <header className="mb-4 flex flex-col gap-3 rounded-2xl border border-white/10 bg-white/[0.035] p-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-[10px] font-bold tracking-[0.18em] text-cyan-400">DIGITAL TWIN CONTROL CENTER</p>
              <h2 className="mt-1 text-xl font-black sm:text-2xl">Bản đồ vận hành bãi xe</h2>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="border-white/10 text-slate-300"><Cpu className="mr-1 size-3" /> IoT 100/100</Badge>
              <Badge variant="outline" className="border-white/10 text-slate-300"><Gauge className="mr-1 size-3" /> 24 ms</Badge>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setShowGraph((value) => !value)}
                className={cn("border-white/10 bg-white/5", showGraph && "border-cyan-400/40 bg-cyan-400/10 text-cyan-300")}
              >
                <GitBranch className="mr-1 size-4" /> Graph A*
              </Button>
            </div>
          </header>

          <ParkingLot slots={slots} routeMode={routeMode} target={target} showGraph={showGraph} />

          <div className="mt-4 grid gap-3 md:grid-cols-3">
            {[
              { icon: Sparkles, title: "Sự kiện mới nhất", value: `#${events} • Cảm biến xác nhận vị trí CN-04`, color: "text-cyan-400" },
              { icon: CircleParking, title: "Lượt xe hoàn tất", value: "2.162 lượt trong phiên mô phỏng", color: "text-emerald-400" },
              { icon: BadgeCheck, title: "Tình trạng hệ thống", value: "Tất cả dịch vụ hoạt động bình thường", color: "text-violet-400" },
            ].map(({ icon: Icon, title, value, color }, index) => (
              <motion.div key={title} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.08 }}>
                <Card className="h-full border-white/10 bg-white/[0.035] text-white">
                  <CardContent className="flex items-start gap-3 p-4">
                    <div className="rounded-lg bg-white/5 p-2"><Icon className={cn("size-4", color)} /></div>
                    <div><p className="text-xs font-bold">{title}</p><p className="mt-1 text-[11px] text-slate-400">{value}</p></div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
