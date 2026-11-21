import { createApp } from "vue";
import App from "../../src/App.vue";
import { TownAudio, type Sound } from "../../src/game/audio";
import "../../src/style.css";

const calls: string[] = [];
const play = TownAudio.prototype.play;
TownAudio.prototype.play = function (sound: Sound) {
  calls.push(sound.kind);
  return play.call(this, sound);
};
const app = createApp(App);
app.mount("#app");
(window as any).audioHarness = { calls, dispose: () => app.unmount() };
