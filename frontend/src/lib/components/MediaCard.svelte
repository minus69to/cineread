<script>
  import MediaBadge from './MediaBadge.svelte';

  export let item = {};

  $: cover = item.cover_url ?? null;
  $: rating = item.rating ? Number(item.rating).toFixed(1) : null;
  $: year = item.year ?? null;
  $: creator = item.creator || '';
  $: overview = item.overview ? item.overview.slice(0, 200) + (item.overview.length > 200 ? '…' : '') : '';
  $: reasoning = item.reasoning ?? '';
  $: meta = [
    item.seasons ? `${item.seasons} season${item.seasons > 1 ? 's' : ''}` : null,
    item.status ?? null,
    item.pages ? `${item.pages} pages` : null,
  ].filter(Boolean);
</script>

<div class="card flex gap-4 p-4 hover:border-cine-accent/50 transition-colors duration-200 group">
  <!-- Cover -->
  <div class="flex-shrink-0 w-20 h-28 rounded-lg overflow-hidden bg-cine-border">
    {#if cover}
      <img src={cover} alt={item.title} class="w-full h-full object-cover" loading="lazy" />
    {:else}
      <div class="w-full h-full flex items-center justify-center text-2xl text-gray-600">
        {item.media_type === 'movie' ? '🎬' : item.media_type === 'series' ? '📺' : '📚'}
      </div>
    {/if}
  </div>

  <!-- Info -->
  <div class="flex-1 min-w-0">
    <div class="flex items-start justify-between gap-2 mb-1.5">
      <div class="min-w-0">
        <h3 class="font-semibold text-white text-sm leading-snug truncate group-hover:text-cine-accent transition-colors">
          {item.title}
        </h3>
        <div class="flex items-center gap-2 mt-0.5 text-xs text-gray-500 flex-wrap">
          {#if year}<span>{year}</span>{/if}
          {#if creator}<span>· {creator}</span>{/if}
          {#each meta as m}<span>· {m}</span>{/each}
        </div>
      </div>
      <div class="flex flex-col items-end gap-1 flex-shrink-0">
        <MediaBadge type={item.media_type} />
        {#if rating}
          <span class="text-xs font-bold text-yellow-400">⭐ {rating}</span>
        {/if}
      </div>
    </div>

    {#if overview}
      <p class="text-xs text-gray-400 leading-relaxed mb-2 line-clamp-2">{overview}</p>
    {/if}

    {#if reasoning}
      <p class="text-xs text-cine-accent/80 italic leading-relaxed border-l-2 border-cine-accent/30 pl-2">
        {reasoning}
      </p>
    {/if}
  </div>
</div>
