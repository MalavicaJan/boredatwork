// Pure grid helpers. No solution knowledge lives on the client: these
// only ever look at what the player has typed.

export const SIZE = 9;
export const CELLS = SIZE * SIZE;
export const EMPTY = "0";

export function rowOf(index: number) {
  return Math.floor(index / SIZE);
}

export function columnOf(index: number) {
  return index % SIZE;
}

export function boxOf(index: number) {
  return Math.floor(rowOf(index) / 3) * 3 + Math.floor(columnOf(index) / 3);
}


export function replaceCell(grid: string, index: number, value: string) {
  return grid.slice(0, index) + value + grid.slice(index + 1);
}

export function remainingCells(grid: string) {
  return grid.split("").filter((cell) => cell === EMPTY).length;
}

export function formatTime(totalSeconds: number) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;

  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}
