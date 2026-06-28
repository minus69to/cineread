<script>
  import { createEventDispatcher } from 'svelte';

  export let disabled = false;

  const dispatch = createEventDispatcher();
  let value = '';

  function submit() {
    const msg = value.trim();
    if (!msg || disabled) return;
    dispatch('send', msg);
    value = '';
  }

  function onKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }
</script>

<div class="flex items-end gap-3 p-4 border-t border-cine-border bg-cine-bg">
  <textarea
    bind:value
    on:keydown={onKeydown}
    {disabled}
    rows="1"
    placeholder="Ask anything — Dark দেখলাম, কী দেখব? / I loved Dune, what next?"
    class="flex-1 resize-none bg-cine-card border border-cine-border rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600
           focus:outline-none focus:border-cine-accent/60 transition-colors
           disabled:opacity-50 disabled:cursor-not-allowed
           min-h-[48px] max-h-36 overflow-y-auto leading-relaxed"
    style="field-sizing: content"
  ></textarea>

  <button
    on:click={submit}
    {disabled}
    class="flex-shrink-0 w-11 h-11 bg-cine-accent hover:bg-cine-accent-hover disabled:opacity-40 disabled:cursor-not-allowed
           rounded-xl flex items-center justify-center transition-colors duration-150"
    aria-label="Send"
  >
    <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-white rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M12 19V5m0 0l-7 7m7-7l7 7" />
    </svg>
  </button>
</div>
