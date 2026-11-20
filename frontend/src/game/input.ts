import type Phaser from "phaser";

// Phaser also receives window mouse-up events from controls above the canvas.
// A scene selection must both start and end on the actual game surface.
export function canvasClick(
  pointer: Phaser.Input.Pointer,
  canvas: HTMLCanvasElement,
) {
  return pointer.downElement === canvas && pointer.upElement === canvas;
}
