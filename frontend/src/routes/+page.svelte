<script>
  import { goto } from '$app/navigation';

  const examples = [
    'Dark series শেষ করলাম, এখন কী দেখব?',
    'I loved Dune — book or movie, what\'s next?',
    'Something like Gone Girl — doesn\'t matter the format',
    'কিছু একটা দাও, sad but hopeful'
  ];
</script>

<svelte:head>
  <title>CineRead — Find Your Next Movie, Series, or Book</title>
</svelte:head>

<main class="min-h-screen flex flex-col items-center justify-center px-4 py-16">
  <div class="w-full max-w-xl text-center">

    <div class="mb-8">
      <h1 class="text-5xl font-bold mb-3">
        <span class="text-cine-accent">CineRead</span>
      </h1>
      <p class="text-lg text-gray-400">
        Movies &bull; Series &bull; Books &mdash; one conversation.
      </p>
    </div>

    <div class="card p-6 mb-8 text-left">
      <p class="text-xs text-gray-500 uppercase tracking-widest font-medium mb-4">
        Try asking
      </p>
      <ul class="space-y-3">
        {#each examples as example}
          <li class="flex items-start gap-3">
            <span class="text-cine-accent mt-0.5">›</span>
            <span class="text-gray-300 text-sm leading-relaxed">"{example}"</span>
          </li>
        {/each}
      </ul>
    </div>

    <div class="flex gap-3 justify-center text-sm text-gray-500 mb-8">
      <span class="flex items-center gap-1.5">🎬 Movies</span>
      <span class="text-cine-border">|</span>
      <span class="flex items-center gap-1.5">📺 TV Series</span>
      <span class="text-cine-border">|</span>
      <span class="flex items-center gap-1.5">📚 Books</span>
    </div>

    <button class="btn-primary text-base px-10 py-3" on:click={() => goto('/chat')}>
      Start Chatting →
    </button>

  </div>
</main>
