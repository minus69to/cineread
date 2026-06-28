<script>
  import { onMount, tick } from 'svelte';
  import { streamChat } from '$lib/api.js';
  import MessageBubble from '$lib/components/MessageBubble.svelte';
  import ChatInput from '$lib/components/ChatInput.svelte';

  let messages = [];
  let loading = false;
  let scrollEl;
  let sessionId = crypto.randomUUID();

  async function scrollToBottom() {
    await tick();
    if (scrollEl) scrollEl.scrollTop = scrollEl.scrollHeight;
  }

  async function send(e) {
    const text = e.detail;
    if (!text || loading) return;

    messages = [...messages, { role: 'user', text }];
    await scrollToBottom();

    const assistantMsg = { role: 'assistant', text: '', items: [], loading: true };
    messages = [...messages, assistantMsg];
    const idx = messages.length - 1;
    loading = true;

    try {
      for await (const chunk of streamChat(text, sessionId)) {
        if (chunk.type === 'media') {
          messages[idx].items = chunk.items;
          messages = [...messages];
          await scrollToBottom();
        } else if (chunk.type === 'text') {
          messages[idx].text = chunk.content;
          messages = [...messages];
          await scrollToBottom();
        } else if (chunk.type === 'error') {
          messages[idx].text = 'Something went wrong. Please try again.';
          messages = [...messages];
        }
      }
    } catch (err) {
      messages[idx].text = 'Connection error. Is the backend running?';
      messages = [...messages];
    } finally {
      messages[idx].loading = false;
      messages = [...messages];
      loading = false;
      await scrollToBottom();
    }
  }

  const examples = [
    'Dark series শেষ করলাম, কী দেখব?',
    'I loved Inception — what next?',
    'Something sad but hopeful, any format',
  ];
</script>

<svelte:head>
  <title>CineRead — Chat</title>
</svelte:head>

<div class="flex flex-col h-screen bg-cine-bg">
  <!-- Header -->
  <header class="flex items-center justify-between px-5 py-3 border-b border-cine-border bg-cine-bg/95 backdrop-blur-sm sticky top-0 z-10">
    <a href="/" class="text-lg font-bold text-cine-accent hover:opacity-80 transition-opacity">
      CineRead
    </a>
    <div class="flex items-center gap-3 text-xs text-gray-500">
      <span>🎬 Movies</span>
      <span class="text-cine-border">|</span>
      <span>📺 Series</span>
      <span class="text-cine-border">|</span>
      <span>📚 Books</span>
    </div>
  </header>

  <!-- Messages -->
  <div
    bind:this={scrollEl}
    class="flex-1 overflow-y-auto px-4 py-6 max-w-3xl w-full mx-auto"
  >
    {#if messages.length === 0}
      <!-- Empty state -->
      <div class="flex flex-col items-center justify-center h-full gap-6 text-center">
        <div>
          <p class="text-gray-500 text-sm mb-4">Ask anything across movies, series, and books</p>
          <div class="space-y-2">
            {#each examples as ex}
              <button
                on:click={() => send({ detail: ex })}
                class="block w-full text-left text-sm text-gray-400 hover:text-white bg-cine-card hover:bg-cine-border border border-cine-border hover:border-cine-accent/40 rounded-xl px-4 py-3 transition-all duration-150"
              >
                <span class="text-cine-accent mr-2">›</span>{ex}
              </button>
            {/each}
          </div>
        </div>
      </div>
    {:else}
      {#each messages as message (message)}
        <MessageBubble {message} />
      {/each}
    {/if}
  </div>

  <!-- Input -->
  <div class="max-w-3xl w-full mx-auto">
    <ChatInput {loading} disabled={loading} on:send={send} />
  </div>
</div>
