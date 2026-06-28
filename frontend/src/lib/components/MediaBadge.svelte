<script>
  export let type = '';

  const config = {
    movie:  { emoji: '🎬', label: 'Movie',  color: 'bg-violet-900/60 text-violet-300 border-violet-700/50' },
    series: { emoji: '📺', label: 'Series', color: 'bg-blue-900/60 text-blue-300 border-blue-700/50' },
    book:   { emoji: '📚', label: 'Book',   color: 'bg-emerald-900/60 text-emerald-300 border-emerald-700/50' },
  };

  $: cfg = config[type] ?? { emoji: '?', label: type, color: 'bg-gray-800 text-gray-400 border-gray-700' };
</script>

<span class="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full border {cfg.color}">
  {cfg.emoji} {cfg.label}
</span>
