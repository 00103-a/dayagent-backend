<script setup>
// Skeleton loading state for the home page
// Matches the new layout: hero → focus → timeline
</script>

<template>
  <div class="skel">
    <!-- Hero skeleton -->
    <div class="skel-hero">
      <div class="skeleton" style="width:72%;height:26px;margin-bottom:14px" />
      <div class="skeleton" style="width:40%;height:14px" />
    </div>

    <!-- Section label -->
    <div class="skeleton" style="width:56px;height:10px;margin-top:32px;margin-bottom:16px" />

    <!-- Focus items -->
    <div class="skel-focus">
      <div v-for="i in 3" :key="i" class="skel-focus-row">
        <div class="skeleton" style="width:14px;height:14px;flex-shrink:0" />
        <div class="skeleton" :style="{ width: (75 - i * 10) + '%', height: '15px' }" />
      </div>
    </div>

    <!-- Timeline skeleton -->
    <div class="skeleton" style="width:56px;height:10px;margin-top:32px;margin-bottom:16px" />
    <div class="skel-timeline">
      <div v-for="i in 3" :key="i" class="skel-timeline-row">
        <div class="skeleton" style="width:38px;height:14px;flex-shrink:0" />
        <div class="skel-timeline-card">
          <div class="skeleton" style="width:65%;height:15px;margin-bottom:6px" />
          <div class="skeleton" style="width:35%;height:12px" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.skel {
  display: flex;
  flex-direction: column;
}

.skel-hero {
  padding: 8px 0 40px;
}

.skel-focus {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.skel-focus-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 0;
  border-bottom: 1px solid var(--border-subtle);
}

.skel-timeline {
  display: flex;
  flex-direction: column;
}

.skel-timeline-row {
  display: flex;
  gap: 16px;
  min-height: 48px;
  padding-bottom: 20px;
}

.skel-timeline-card {
  flex: 1;
}
</style>
