<script lang="ts">
	import { useSidebar } from './ui/sidebar';
	import SidebarToggle from './sidebar-toggle.svelte';
	import { innerWidth } from 'svelte/reactivity/window';
	import { Tooltip, TooltipContent, TooltipTrigger } from './ui/tooltip';
	import { Button } from './ui/button';
	import PlusIcon from './icons/plus.svelte';
	import { goto } from '$app/navigation';
	import type { Chat, User } from '$lib/server/db/schema';
	import VisibilitySelector from './visibility-selector.svelte';

	let {
		user,
		chat,
		readonly
	}: {
		user: User | undefined;
		chat: Chat | undefined;
		readonly: boolean;
	} = $props();

	const sidebar = useSidebar();

	async function handleMoodleSync() {
		await fetch('/api/sync-moodle', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ userId: user?.id })
		});
	}
</script>

<header class="bg-background sticky top-0 flex items-center gap-2 p-2">
	<SidebarToggle />

	{#if !sidebar.open || (innerWidth.current ?? 768) < 768}
		<Tooltip>
			<TooltipTrigger>
				{#snippet child({ props })}
					<Button
						{...props}
						variant="outline"
						class="order-2 ml-auto px-2 md:order-1 md:ml-0 md:h-fit md:px-2"
						onclick={() => {
							goto('/', {
								invalidateAll: true
							});
						}}
					>
						<PlusIcon />
						<span class="md:sr-only">New Chat</span>
					</Button>
				{/snippet}
			</TooltipTrigger>
			<TooltipContent>New Chat</TooltipContent>
		</Tooltip>
	{/if}

	{#if !readonly && chat}
		<VisibilitySelector {chat} class="order-1 md:order-3" />
	{/if}

	{#if !user?.ucl_api_token}
		<Button href="/signin" class="order-5 px-2 py-1.5 md:h-[34px]">Connect UCL</Button>
	{/if}

	{#if !user?.last_moodle_sync}
		<Button
			class="order-4 hidden h-fit bg-zinc-900 px-2 py-1.5 text-zinc-50 hover:bg-zinc-800 md:ml-auto md:flex md:h-[34px] dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
			onclick={handleMoodleSync}
		>
			Connect Moodle
		</Button>
	{/if}
</header>
