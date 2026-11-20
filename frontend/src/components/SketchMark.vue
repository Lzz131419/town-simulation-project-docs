<script setup lang="ts">
withDefaults(defineProps<{ kind?: "spark" | "dots" | "arrow" }>(), {
  kind: "spark",
});
</script>
<template>
  <svg class="sketch-mark" viewBox="0 0 100 100" fill="none" aria-hidden="true">
    <g
      v-if="kind === 'spark'"
      stroke="currentColor"
      stroke-width="5"
      stroke-linecap="round"
    >
      <path
        d="M47 5 44 29M76 14 62 34M92 43 70 47M85 75 65 62M50 92 49 69M17 80 32 63M6 44 29 48M17 16 33 34"
      />
    </g>
    <g v-else-if="kind === 'dots'" fill="currentColor">
      <path
        d="m9 14 5-3 4 4-1 6-7 1Zm25-9 5 1 2 6-6 3-4-4Zm32 9 6-3 3 6-3 4-5-1ZM87 5l6 3-2 7-6-2ZM19 39l7-2 2 6-6 3-4-3Zm27-9 5 3-1 6-6 1-2-6Zm27 9 5-2 4 6-5 4-5-3Zm19-11 5 3-3 6-5-2ZM5 64l7-1 2 6-7 4-3-5Zm30-9 6 1-1 7-7 1-2-4Zm23 12 6-3 3 7-5 3-5-3Zm29-13 6 2-2 7-6-1ZM18 85l6-3 4 6-6 5-5-4Zm25-6 6 2-1 7-7-1Zm31 10 5-4 4 5-2 6-6-1Z"
      />
    </g>
    <g
      v-else
      stroke="currentColor"
      stroke-width="3.5"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <path
        d="M8 14c57-17 77 25 49 40-24 13-41-16-17-22 32-9 52 22 42 54M65 73l17 16 13-18"
      />
    </g>
  </svg>
</template>
