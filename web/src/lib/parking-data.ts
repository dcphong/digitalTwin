export type SlotStatus = "free" | "occupied" | "reserved" | "mine";

export type ParkingSlot = {
  id: string;
  zone: string;
  status: SlotStatus;
  electric: boolean;
  accessible: boolean;
};

export const zones = ["A", "B", "C", "D", "E"];

export function createParkingSlots(): ParkingSlot[] {
  return zones.flatMap((zone, zoneIndex) =>
    Array.from({ length: 20 }, (_, index) => {
      const side = index < 10 ? "N" : "S";
      const number = (index % 10) + 1;
      const seed = zoneIndex * 20 + index;
      return {
        id: `${zone}${side}-${String(number).padStart(2, "0")}`,
        zone,
        status:
          seed === 47
            ? "mine"
            : seed % 4 === 0 || seed % 7 === 0
              ? "occupied"
              : seed % 19 === 0
                ? "reserved"
                : "free",
        electric: zone === "A" && number > 5,
        accessible: zone === "A" && number < 3,
      };
    }),
  );
}

export const movingCars = [
  { id: 1, color: "#3a9aff", duration: 13, delay: 0, lane: 0 },
  { id: 2, color: "#ff7658", duration: 16, delay: 2, lane: 1 },
  { id: 3, color: "#a979ff", duration: 14, delay: 5, lane: 2 },
  { id: 4, color: "#2ac97e", duration: 18, delay: 1, lane: 3 },
  { id: 5, color: "#ffc43d", duration: 15, delay: 7, lane: 4 },
];

