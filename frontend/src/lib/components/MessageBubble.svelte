<script>
  import MediaCard from './MediaCard.svelte';
  import TypingIndicator from './TypingIndicator.svelte';

  export let message = {};

  $: isUser = message.role === 'user';
  $: filter = 'all';

  const filters = [
    { key: 'all', label: 'All' },
    { key: 'movie', label: '🎬 Movies' },
    { key: 'series', label: '📺 Series' },
    { key: 'book', label: '📚 Books' },
  ];

  $: visibleItems = filter === 'all'
    ? (message.items ?? [])
    : (message.items ?? []).filter(i => i.media_type === filter);

  $: hasMultipleTypes = new Set((message.items ?? []).map(i => i.media_type)).size > 1;
</script>

{#if isUser}
  <div class="flex justify-end mb-4">
    <div class="max-w-[75%] bg-cine-accent/20 border border-cine-accent/30 rounded-2xl rounded-tr-sm px-4 py-2.5">
      <p class="text-sm text-white leading-relaxed whitespace-pre-wrap">{message.text}</p>
    </div>
  </div>

{:else}
  <div class="flex flex-col gap-3 mb-6">
    <!-- Text or typing indicator -->
    <div class="flex items-start gap-3">
      <div class="w-7 h-7 rounded-full bg-cine-accent/30 flex items-center justify-center text-xs flex-shrink-0 mt-0.5">
        C
      </div>
      <div class="flex-1 min-w-0">
        {#if message.loading && !message.text}
          <TypingIndicator />
        {:else if message.text}
          <div class="card px-4 py-3">
            <p class="text-sm text-gray-200 leading-relaxed whitespace-pre-wrap">{message.text}</p>
          </div>
        {/if}
      </div>
    </div>

    <!-- Media cards -->
    {#if message.items && message.items.length > 0}
      <div class="ml-10">
        {#if hasMultipleTypes}
          <div class="flex gap-2 mb-3 flex-wrap">
            {#each filters as f}
              <button
                on:click={() => filter = f.key}
                class="text-xs px-3 py-1 rounded-full border transition-colors duration-150
                       {filter === f.key
                         ? 'bg-cine-accent border-cine-accent text-white'
                         : 'border-cine-border text-gray-400 hover:border-gray-500'}"
              >
                {f.label}
              </button>
            {/each}
          </div>
        {/if}

        <div class="space-y-3">
          {#each visibleItems as item (item.id)}
            <MediaCard {item} />
          {/each}
        </div>
      </div>
    {/if}
  </div>
{/if}
